import csv,importlib.util,json,tempfile,unittest
from pathlib import Path
SCRIPT=Path(__file__).resolve().parents[1]/'scripts'/'audit_experimental_table.py'
spec=importlib.util.spec_from_file_location('table_audit',SCRIPT);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class TableAuditTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.p=Path(self.temp.name)
  self.table=self.p/'table.csv';self.inv=self.p/'runs.csv';self.out=self.p/'output'
  with self.table.open('w',newline='') as f:
   w=csv.writer(f);w.writerow(m.EXPECTED);w.writerow(['2019','Feb','25','25','50% C2H4','3400%','8','']);w.writerow(['2019','March','7','25','100%C2H4','2100%','6',''])
  with self.inv.open('w',newline='') as f:
   w=csv.writer(f);w.writerow(['run_id','status','experiment_date']);w.writerow(['19056A2','complete_validated_pair','2019-02-25'])
 def run_audit(self):return m.audit(self.table,self.inv,self.out)
 def test_count_sum_and_raw_values(self):
  x=self.run_audit();self.assertEqual(x['table']['row_count'],2);self.assertEqual(x['table']['flames_ignited_sum_of_valid_integer_cells'],14);self.assertIn('3400%',(self.out/'table_quality_issues.csv').read_text());self.assertIn('2100%',(self.out/'table_quality_issues.csv').read_text())
 def test_day_match_and_unmatched(self):
  self.run_audit();s=(self.out/'day_run_crosswalk.csv').read_text();self.assertIn('19056A2',s);self.assertIn('unmatched_summary_day',s)
 def test_unmatched_run(self):
  self.inv.write_text('run_id,status,experiment_date\nA1,complete_validated_pair,2020-01-01\n');self.run_audit();self.assertIn('unmatched_local_run',(self.out/'day_run_crosswalk.csv').read_text())
 def test_unverified_run_excluded(self):
  self.inv.write_text('run_id,status,experiment_date\nA1,incomplete_or_conflicting,2019-02-25\n');self.run_audit();self.assertIn('unverified_run_excluded',(self.out/'day_run_crosswalk.csv').read_text())
 def test_invalid_count(self):
  self.table.write_text(','.join(m.EXPECTED)+'\n2019,Feb,25,25,fuel,21,NaN,\n');x=self.run_audit();self.assertEqual(x['table']['valid_flames_ignited_count_rows'],0);self.assertIn('invalid_count',(self.out/'table_quality_issues.csv').read_text())
 def test_bad_calendar_date(self):
  self.table.write_text(','.join(m.EXPECTED)+'\n2019,Feb,30,25,fuel,21,1,\n');self.run_audit();self.assertIn('invalid_calendar_date',(self.out/'table_quality_issues.csv').read_text())
 def test_reproducibility_and_source_immutability(self):
  a=m.digest(self.table);b=m.digest(self.inv);self.run_audit();first={p.name:p.read_bytes() for p in self.out.iterdir()};self.run_audit();self.assertEqual(first,{p.name:p.read_bytes() for p in self.out.iterdir()});self.assertEqual(a,m.digest(self.table));self.assertEqual(b,m.digest(self.inv))
 def test_multiple_runs_same_day(self):
  with self.inv.open('a') as f:f.write('19056A3,complete_validated_pair,2019-02-25\n')
  x=self.run_audit();self.assertEqual(x['crosswalk']['candidate_link_count'],2);self.assertIn('multiple local runs same day',(self.out/'day_run_crosswalk.csv').read_text())
 def test_table_schema_mismatch_reported(self):
  self.table.write_text('Year,Month,Date\n2019,Feb,25\n');self.run_audit();self.assertIn('unexpected_schema',(self.out/'table_quality_issues.csv').read_text())
if __name__=='__main__':unittest.main()
