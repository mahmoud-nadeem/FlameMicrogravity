import csv,importlib.util,tempfile,unittest
from pathlib import Path
S=Path(__file__).resolve().parents[1]/'scripts'/'reconcile_nasa_report.py'
spec=importlib.util.spec_from_file_location('reconcile_report',S);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class ReportReconciliationTests(unittest.TestCase):
 def setUp(self):
  t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);self.root=Path(t.name);self.table=self.root/'source.csv';self.out=self.root/'out'
  with self.table.open('w',newline='') as f:
   w=csv.writer(f);w.writerow(['Year','Month','Date','Burner Size (mm)','Fuel Bottle','Oxygen Conc (percent)','Flames Ignited','Notes']);w.writerows([
    ['2019','March','7','25','x','3400%','6',''],['2019','April','1','25','x','2100%','0',''],
    ['2020','Oct','17','25','x','26.5; 34','13',''],['2020','Dec','5','25','x','25; 34; 40','21','']])
 def test_oxygen_3400(self):
  m.reconcile(self.table,self.out);self.assertIn('3400%',(self.out/'cross_source_discrepancies.csv').read_text())
 def test_oxygen_2100(self):
  m.reconcile(self.table,self.out);self.assertIn('2100%',(self.out/'cross_source_discrepancies.csv').read_text())
 def test_date_20261(self):
  m.reconcile(self.table,self.out);self.assertIn('2020-09-17',(self.out/'cross_source_discrepancies.csv').read_text())
 def test_date_20279(self):
  m.reconcile(self.table,self.out);self.assertIn('2020-10-05',(self.out/'cross_source_discrepancies.csv').read_text())
 def test_counts_and_scope(self):
  x=m.reconcile(self.table,self.out);self.assertEqual(x['flames_ignited_sum'],40);self.assertEqual(x['cross_source_differences'],4);self.assertEqual(x['report_internal_differences'],1)
  s=(self.out/'report_reconciliation.md').read_text();self.assertIn('196 successful ignitions',s);self.assertIn('page 127',s)
 def test_manifest_provenance(self):
  m.reconcile(self.table,self.out)
  with (self.out/'report_reference_manifest.csv').open() as f:rows=list(csv.DictReader(f))
  self.assertEqual(rows[0]['test_day'],'19066');self.assertEqual(rows[0]['pdf_pages'],'24;112')
 def test_immutability(self):
  before=m.sha256(self.table);m.reconcile(self.table,self.out);self.assertEqual(before,m.sha256(self.table))
 def test_deterministic(self):
  m.reconcile(self.table,self.out);first={p.name:p.read_bytes() for p in self.out.iterdir()};m.reconcile(self.table,self.out);self.assertEqual(first,{p.name:p.read_bytes() for p in self.out.iterdir()})
 def test_reject_missing_comparison_row(self):
  self.table.write_text('Year,Month,Date,Burner Size (mm),Fuel Bottle,Oxygen Conc (percent),Flames Ignited,Notes\n2019,March,7,25,x,3400%,6,\n')
  with self.assertRaisesRegex(ValueError,'Expected unique CSV day-level record'):m.reconcile(self.table,self.out)
 def test_page23_explicit_correction_and_historical_date(self):
  m.reconcile(self.table,self.out)
  with (self.out/'report_reference_manifest.csv').open() as f:refs=list(csv.DictReader(f))
  corrected=[r for r in refs if r['test_day']=='19094' and r['date_status']=='corrected_operational_date']
  historical=[r for r in refs if r['test_day']=='19094' and r['date_status']=='historical_superseded_date']
  self.assertEqual(len(corrected),1);self.assertEqual(corrected[0]['reference_calendar_date'],'2019-04-04');self.assertIn('23',corrected[0]['pdf_pages'].split(';'))
  self.assertEqual(len(historical),1);self.assertEqual(historical[0]['reference_calendar_date'],'2019-04-05')
  with (self.out/'cross_source_discrepancies.csv').open() as f:diff=list(csv.DictReader(f))
  d=[r for r in diff if r['discrepancy_type']=='explained_historical_source_difference']
  self.assertEqual(len(d),1);self.assertEqual(d[0]['resolution_status'],'explained_by_report');self.assertEqual(d[0]['authoritative_explanation_pdf_page'],'23')
 def test_page29_196_and_scope(self):
  m.reconcile(self.table,self.out);report=(self.out/'report_reconciliation.md').read_text()
  for page in ('page 29','page 110','page 116','page 127'):self.assertIn(page,report)
  self.assertIn('196 successful ignitions',report);self.assertIn('132',report)
  self.assertIn('Apparent scope inconsistency unresolved',report)
 def test_four_cross_source_differences_preserved(self):
  m.reconcile(self.table,self.out)
  with (self.out/'cross_source_discrepancies.csv').open() as f:diff=list(csv.DictReader(f))
  self.assertEqual(len([d for d in diff if d['discrepancy_type']!='explained_historical_source_difference']),4)
  self.assertEqual(len(diff),5)
if __name__=='__main__':unittest.main()
