import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_pipeline import load,timestamps,run_pipeline
class TestAudit(unittest.TestCase):
 def test_metadata_and_duplicates(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'a.csv';p.write_text('2019-02-25 056 15:00:00:000,Test Point: 19056A2\nTime,X\n15:00:00:000,1\n15:00:00:000,1\n')
   a=load(p);self.assertEqual(a['records'],2);self.assertEqual(a['metadata_key_values']['Test Point'],'19056A2');self.assertEqual(a['frame'].duplicated().sum(),1)
 def test_timestamps_backward_and_duplicate(self):
  import pandas as pd
  ts,_=timestamps(pd.Series(['23:59:59:900','23:59:59:900','00:00:00:100']),'2019-02-25 056 15:00:00:000')
  self.assertEqual(ts.diff().dt.total_seconds().iloc[1],0);self.assertLess(ts.diff().dt.total_seconds().iloc[2],0)
 def test_bad_width(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'a.csv';p.write_text('meta\nTime,X\n12:00:00:000\n')
   with self.assertRaises(ValueError):load(p)
 def test_end_to_end(self):
  with tempfile.TemporaryDirectory() as t:
   t=Path(t);head='2019-02-25 056 15:00:00:000,Test Point: 19056A2\n'
   d=t/'d.csv';m=t/'m.csv';d.write_text(head+'Time,IonCurrent\n15:00:00:000,1\n15:00:00:010,nan\n15:00:00:010,bad\n');m.write_text(head+'Time,MFCA1Setpoint(V)\n15:00:00:000,0\n15:00:00:000,0\n15:00:00:020,1\n')
   before=(d.read_bytes(),m.read_bytes());run_pipeline(d,m,t/'out',True)
   self.assertEqual(before,(d.read_bytes(),m.read_bytes()))
   self.assertTrue((t/'out/audit/19056A2_timing_report.json').exists())
   self.assertEqual(len((t/'out/audit/19056A2_mfc_events.csv').read_text().splitlines()),3)
if __name__=='__main__':unittest.main()

class TestHardening(unittest.TestCase):
 def fixture(self,root,run='88888B1',mfc_run=None):
  head=lambda r:f'2019-02-25 056 15:00:00:000,Test Point: {r}\n'
  d=root/'data.csv';m=root/'mfc.csv'
  d.write_text(head(run)+'Time,Sensor\n15:00:00:000,1\n15:00:00:010,bad\n15:00:02:010,NaN\n15:00:02:007,3\n')
  m.write_text(head(mfc_run or run)+'Time,Control\n15:00:00:000,0\n15:00:01:000,1\n15:00:01:000,1\n15:00:01:000,2\n')
  return d,m
 def test_other_run_and_quality_and_gap(self):
  import json,pandas as pd
  from audit_pipeline import digest
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);d,m=self.fixture(root);before=(digest(d),digest(m));out=root/'out'
   run_pipeline(d,m,out,True)
   self.assertTrue((out/'audit/88888B1_metadata.json').exists())
   timing=json.loads((out/'audit/88888B1_timing_report.json').read_text())
   self.assertEqual(timing['data']['major_gap_count'],1)
   self.assertEqual(timing['data']['negative_intervals'],1)
   self.assertEqual(timing['mfc']['zero_intervals'],2)
   q=pd.read_csv(out/'audit/88888B1_quality_report.csv');r=q[(q.source=='data')&(q.column=='Sensor')].iloc[0]
   self.assertEqual(r.nonnumeric,1);self.assertEqual(r.nan_tokens,1)
   self.assertFalse(q[q.source=='mfc'].saturation_candidate.any())
   self.assertEqual(len(pd.read_csv(out/'audit/88888B1_alignment_preview.csv')),4)
   self.assertEqual(before,(digest(d),digest(m)))
   inv=(out/'audit/file_inventory_sha256.txt').read_text();self.assertNotIn('file_inventory_sha256.txt',inv)
 def test_metadata_mismatch_and_explicit_run_mismatch(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);d,m=self.fixture(root,mfc_run='99999C2')
   with self.assertRaisesRegex(ValueError,'mismatch'):run_pipeline(d,m,root/'out')
   d,m=self.fixture(root)
   with self.assertRaisesRegex(ValueError,'does not match'):run_pipeline(d,m,root/'out',run_id='19056A2')
 def test_deterministic_regeneration(self):
  from audit_pipeline import digest
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);d,m=self.fixture(root)
   run_pipeline(d,m,root/'out1',True)
   run_pipeline(d,m,root/'out2',True)
   a={p.relative_to(root/'out1').as_posix():digest(p) for p in (root/'out1').rglob('*') if p.is_file()}
   b={p.relative_to(root/'out2').as_posix():digest(p) for p in (root/'out2').rglob('*') if p.is_file()}
   self.assertEqual(a,b)

class TestTask02B(unittest.TestCase):
 def make_inputs(self,root,date_data='2019-02-25',date_mfc='2019-02-25'):
  head=lambda date:f'{date} 056 15:00:00:000,Test Point: SYNTHB2,Experiment: 4\n'
  d=root/'data.csv';m=root/'mfc.csv'
  d.write_text(head(date_data)+'Time,Sensor\n15:00:00:000,1\n15:00:00:010,2\n15:00:03:010,3\n15:00:03:007,4\n')
  m.write_text(head(date_mfc)+'Time,Control\n15:00:00:000,0\n15:00:00:000,0\n15:00:00:020,1\n15:00:00:020,1\n')
  return d,m
 def test_cross_date_rejected_and_sources_unchanged(self):
  from audit_pipeline import digest
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);d,m=self.make_inputs(root,date_mfc='2019-02-26');before=(digest(d),digest(m))
   with self.assertRaisesRegex(ValueError,'Experiment date mismatch'):run_pipeline(d,m,root/'out',True)
   self.assertEqual(before,(digest(d),digest(m)))
 def test_event_identity_repeated_rows_and_stale_gap(self):
  import pandas as pd
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);d,m=self.make_inputs(root);run_pipeline(d,m,root/'out',True)
   audit=root/'out'/'audit';ev=pd.read_csv(audit/'SYNTHB2_mfc_events.csv');a=pd.read_csv(audit/'SYNTHB2_alignment_preview.csv')
   self.assertEqual(ev['original_row_1based'].tolist(),[1,3])
   self.assertEqual(ev['event_kind'].tolist(),['initial_state','setpoint_change'])
   self.assertEqual(a['mfc_original_row_1based'].tolist(),[2,2,4,4])
   self.assertFalse(a['matched_mfc_record_is_change_event'].any())
   self.assertTrue(a.loc[2,'stale_timestamp_lookup'])
   self.assertTrue(a.loc[2,'matched_mfc_timestamp_within_major_data_gap'])
   self.assertGreater(a.loc[2,'matched_mfc_age_seconds'],1)
   self.assertFalse(a.loc[0,'stale_timestamp_lookup'])
   self.assertNotIn('data_inside_major_gap',a.columns)
 def test_actual_change_event_id_only_on_change_record(self):
  import pandas as pd
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);d,m=self.make_inputs(root)
   # Replace last repeated row with a later change record.
   s=m.read_text().replace('15:00:00:020,1\n15:00:00:020,1\n','15:00:00:020,1\n15:00:00:030,2\n');m.write_text(s)
   run_pipeline(d,m,root/'out',True)
   a=pd.read_csv(root/'out/audit/SYNTHB2_alignment_preview.csv')
   self.assertTrue(a.loc[2,'matched_mfc_record_is_change_event'])
   self.assertEqual(a.loc[2,'matched_record_change_event_id'],'SYNTHB2_E0003')
