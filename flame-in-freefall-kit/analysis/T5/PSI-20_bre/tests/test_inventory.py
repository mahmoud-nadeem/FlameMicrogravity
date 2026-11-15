import csv
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT=Path(__file__).resolve().parents[1]/'scripts'/'build_run_inventory.py'
spec=importlib.util.spec_from_file_location('inventory',SCRIPT)
inv=importlib.util.module_from_spec(spec);spec.loader.exec_module(inv)

class InventoryTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.root=Path(self.tmp.name)/'input with spaces';self.root.mkdir()
  self.out=Path(self.tmp.name)/'output'
 def make(self,run='ABC123',kind='data',date='2019-02-25',name=None,sub=''):
  p=self.root/sub/(name or f'{run}_{kind}.csv');p.parent.mkdir(parents=True,exist_ok=True)
  p.write_text(f'{date} 056 15:58:10:974 ,Experiment: 4,Test Point: {run}\nTime,Value\n15:58:51:737,1\n',encoding='utf-8');return p
 def codes(self):
  with (self.out/'pairing_issues.csv').open() as f:return [x['code'] for x in csv.DictReader(f)]
 def test_complete_pair(self):
  self.make();self.make(kind='mfcSetpoints');self.assertEqual(inv.build(self.root,self.out)['complete_validated_pairs'],1)
 def test_missing_partner(self):
  self.make();inv.build(self.root,self.out);self.assertIn('missing_mfc_partner',self.codes())
 def test_duplicate_candidates(self):
  self.make();self.make(sub='nested');self.make(kind='mfcSetpoints');inv.build(self.root,self.out);self.assertIn('duplicate_data_candidates',self.codes())
 def test_filename_metadata_conflict(self):
  self.make(name='WRONG_data.csv');self.make(kind='mfcSetpoints');inv.build(self.root,self.out);self.assertIn('filename_metadata_conflict',self.codes())
 def test_cross_date(self):
  self.make();self.make(kind='mfcSetpoints',date='2019-02-26');inv.build(self.root,self.out);self.assertIn('cross_date_mismatch',self.codes())
 def test_nested_prefixed_and_spaces(self):
  self.make(name='PSI-20_Raw Data_ABC123_data.csv',sub='nested folder');self.make(kind='mfcSetpoints',sub='other folder');self.assertEqual(inv.build(self.root,self.out)['complete_validated_pairs'],1)
 def test_unrelated(self):
  self.make();self.make(kind='mfcSetpoints');(self.root/'notes.txt').write_text('note');s=inv.build(self.root,self.out);self.assertEqual(s['unrelated_files'],1)
 def test_corrupt_csv(self):
  p=self.make();p.write_bytes(b'\xff\xfe\x00');self.make(kind='mfcSetpoints');inv.build(self.root,self.out);self.assertIn('unreadable_or_invalid',self.codes())
 def test_reproducible(self):
  self.make();self.make(kind='mfcSetpoints');inv.build(self.root,self.out)
  first={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in self.out.iterdir()}
  inv.build(self.root,self.out)
  self.assertEqual(first,{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in self.out.iterdir()})
 def test_expected_manifest_and_strict(self):
  self.make();self.make(kind='mfcSetpoints');manifest=Path(self.tmp.name)/'expected.json';manifest.write_text(json.dumps(['ABC123','XYZ999']))
  inv.build(self.root,self.out,manifest)
  self.assertIn('missing_data_partner',self.codes())
  with self.assertRaises(ValueError):inv.build(self.root,self.out,manifest,strict=True)
 def test_underscore_suffixed_pair(self):
  self.make(run='19051K1_1');self.make(run='19051K1_1',kind='mfcSetpoints')
  result=inv.build(self.root,self.out)
  self.assertEqual(result['complete_validated_pairs'],1)
  with (self.out/'run_inventory.csv').open() as f:self.assertEqual(next(csv.DictReader(f))['run_id'],'19051K1_1')
 def test_underscore_prefixed_and_nested(self):
  self.make(run='19051K1_1',name='PSI-20_Raw Data_19051K1_1_data.csv',sub='folder with spaces')
  self.make(run='19051K1_1',kind='mfcSetpoints',sub='other')
  self.assertEqual(inv.build(self.root,self.out)['complete_validated_pairs'],1)
 def test_underscore_missing_partner(self):
  self.make(run='19051K1_1');inv.build(self.root,self.out)
  self.assertIn('missing_mfc_partner',self.codes())
 def test_underscore_manifest(self):
  self.make(run='19051K1_1');self.make(run='19051K1_1',kind='mfcSetpoints')
  manifest=Path(self.tmp.name)/'expected.json';manifest.write_text(json.dumps({'expected_runs':['19051K1_1']}))
  self.assertEqual(inv.build(self.root,self.out,manifest)['complete_validated_pairs'],1)
  self.assertEqual(inv.expected_runs(manifest)[0],['19051K1_1'])
 def test_underscore_metadata_mismatch(self):
  self.make(run='19051K1_1',name='19051K1_2_data.csv')
  self.make(run='19051K1_2',kind='mfcSetpoints')
  inv.build(self.root,self.out)
  self.assertIn('filename_metadata_conflict',self.codes())
 def test_unsafe_manifest_ids_rejected(self):
  for bad in ['19051K1__1','_19051K1','19051K1_','../19051K1','19051K1-1','19051K1/1','19051K1 1']:
   manifest=Path(self.tmp.name)/'expected.json';manifest.write_text(json.dumps([bad]))
   with self.subTest(bad=bad),self.assertRaises(ValueError):inv.expected_runs(manifest)
 def test_malformed_run_like_is_not_unrelated(self):
  self.make(run='19051K1__1')
  result=inv.build(self.root,self.out)
  self.assertEqual(result['unrelated_files'],0)
  self.assertEqual(result['invalid_run_like_files'],1)
  self.assertIn('invalid_filename_run_id',self.codes())
  with self.assertRaises(ValueError):inv.build(self.root,self.out,strict=True)
 def test_existing_19056A2_regression(self):
  self.make(run='19056A2');self.make(run='19056A2',kind='mfcSetpoints')
  self.assertEqual(inv.build(self.root,self.out)['complete_validated_pairs'],1)
 def test_underscore_determinism(self):
  self.make(run='19051K1_1');self.make(run='19051K1_1',kind='mfcSetpoints')
  inv.build(self.root,self.out)
  first={p.name:inv.sha256(p) for p in self.out.iterdir()}
  inv.build(self.root,self.out)
  self.assertEqual(first,{p.name:inv.sha256(p) for p in self.out.iterdir()})
 def test_source_unchanged(self):
  a=self.make();b=self.make(kind='mfcSetpoints');before=[inv.sha256(p) for p in [a,b]]
  inv.build(self.root,self.out);self.assertEqual(before,[inv.sha256(p) for p in [a,b]])

if __name__=='__main__':unittest.main()
