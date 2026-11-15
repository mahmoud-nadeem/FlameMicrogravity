#!/usr/bin/env python3
"""PSI-20 local CSV inventory. Reads only first two CSV records; streams SHA-256."""
import argparse
import csv
import hashlib
import json
import re
from collections import defaultdict, Counter
from datetime import date
from pathlib import Path

RUN_ID_RE = re.compile(r'[A-Za-z0-9]+(?:_[A-Za-z0-9]+)*', re.ASCII)
PATTERN = re.compile(r'^(?:PSI-20_Raw Data_)?(?P<run>[A-Za-z0-9]+(?:_[A-Za-z0-9]+)*)_(?P<kind>data|mfcSetpoints)\.csv$', re.I)
# Files with recognized run-data suffixes but malformed IDs must be reported, not silently ignored.
RUN_LIKE = re.compile(r'^(?:PSI-20_Raw Data_)?(?P<run>.*?)_(?P<kind>data|mfcSetpoints)\.csv$', re.I)
FILE_COLUMNS = ['path','filename','candidate_run_id','kind','size_bytes','sha256','encoding','metadata_test_point','experiment_date','metadata_raw_fields_json','header_fields_json','status','error']
RUN_COLUMNS = ['run_id','status','data_candidates','mfc_candidates','data_paths','mfc_paths','experiment_date','issues']
ISSUE_COLUMNS = ['run_id','code','path','detail']

def sha256(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def header_info(path):
    # A strict UTF-8 decode is intentional: never silently reinterpret malformed bytes.
    with path.open('r',encoding='utf-8-sig',newline='') as f:
        reader=csv.reader(f)
        metadata=next(reader,None)
        header=next(reader,None)
    if not metadata or not header:raise ValueError('Missing metadata or column-header CSV record')
    if len(set(header))!=len(header) or any(not x.strip() for x in header):raise ValueError('Empty or duplicate column header')
    if 'Time' not in header:raise ValueError('Missing Time column')
    fields={k.strip():v.strip() for field in metadata[1:] if ':' in field for k,v in [field.split(':',1)]}
    test_point=fields.get('Test Point','')
    if not test_point:raise ValueError('Missing Test Point metadata')
    m=re.match(r'^\s*(\d{4}-\d{2}-\d{2})(?=\s|$)',metadata[0])
    if not m:raise ValueError('Missing ISO experiment calendar date in first metadata field')
    try: date.fromisoformat(m.group(1))
    except ValueError as e:raise ValueError('Invalid experiment calendar date') from e
    return metadata,header,test_point,m.group(1)

def write_csv(path,columns,records):
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=columns,lineterminator='\n');w.writeheader();w.writerows(records)

def expected_runs(path):
    if path is None:return None,None
    p=Path(path)
    raw=p.read_bytes(); digest=hashlib.sha256(raw).hexdigest()
    if p.suffix.lower()=='.json':
        obj=json.loads(raw.decode('utf-8-sig'))
        ids=obj['expected_runs'] if isinstance(obj,dict) else obj
    else:
        ids=[line.strip() for line in raw.decode('utf-8-sig').splitlines() if line.strip() and not line.lstrip().startswith('#')]
    if not isinstance(ids,list) or not all(isinstance(x,str) and RUN_ID_RE.fullmatch(x) for x in ids):raise ValueError('Expected-run manifest must contain run IDs (JSON array / expected_runs array / plain text lines)')
    if len(set(ids))!=len(ids):raise ValueError('Duplicate expected-run manifest IDs')
    return sorted(ids),{'path':str(p.resolve()),'sha256':digest,'format':p.suffix.lower() or 'text','provenance':'USER-SUPPLIED LOCAL MANIFEST; NOT VERIFIED AS NASA-AUTHORITATIVE'}

def build(input_dir,out,expected=None,strict=False):
    root=Path(input_dir).resolve(); dest=Path(out).resolve()
    if not root.is_dir():raise ValueError(f'Input directory does not exist: {root}')
    if dest==root or root in dest.parents:raise ValueError('Output directory must be outside input tree to prevent self-discovery')
    dest.mkdir(parents=True,exist_ok=True)
    expected_ids,provenance=expected_runs(expected)
    files=[];issues=[];groups=defaultdict(lambda:defaultdict(list)); unrelated=[]
    def issue(run,code,path,detail):issues.append(dict(run_id=run,code=code,path=path,detail=detail))
    for p in sorted(root.rglob('*'),key=lambda x:x.relative_to(root).as_posix()):
        if not p.is_file():continue
        rel=p.relative_to(root).as_posix();m=PATTERN.fullmatch(p.name)
        if not m:
            suspicious=RUN_LIKE.fullmatch(p.name)
            if suspicious:
                rec=dict.fromkeys(FILE_COLUMNS,'')
                rec.update(path=rel,filename=p.name,candidate_run_id=suspicious['run'],kind='data' if suspicious['kind'].lower()=='data' else 'mfc',status='invalid_filename_run_id',error='Malformed or unsafe run identifier in run-like CSV filename')
                try:
                    rec['size_bytes']=p.stat().st_size
                    rec['sha256']=sha256(p)
                except OSError as exc:
                    rec['error']+=f'; {type(exc).__name__}: {exc}'
                files.append(rec)
                issue(suspicious['run'],'invalid_filename_run_id',rel,rec['error'])
            else:
                unrelated.append(rel)
            continue
        run=m['run'];kind='data' if m['kind'].lower()=='data' else 'mfc'
        rec=dict.fromkeys(FILE_COLUMNS,'');rec.update(path=rel,filename=p.name,candidate_run_id=run,kind=kind,status='ok')
        try:
            rec['size_bytes']=p.stat().st_size
            rec['sha256']=sha256(p)
            metadata,headers,test,date_value=header_info(p)
            rec.update(encoding='utf-8-sig',metadata_test_point=test,experiment_date=date_value,metadata_raw_fields_json=json.dumps(metadata,ensure_ascii=False),header_fields_json=json.dumps(headers,ensure_ascii=False))
            if test!=run:
                rec['status']='filename_metadata_conflict';issue(run,'filename_metadata_conflict',rel,f'Filename run {run} != metadata Test Point {test}')
        except (OSError,UnicodeError,csv.Error,ValueError,StopIteration) as exc:
            rec['status']='unreadable_or_invalid';rec['error']=f'{type(exc).__name__}: {exc}'
            issue(run,'unreadable_or_invalid',rel,rec['error'])
        files.append(rec);groups[run][kind].append(rec)
    runs=[]
    for run in sorted(set(groups)|set(expected_ids or [])):
        kinds=groups.get(run,{})
        a=kinds.get('data',[]);b=kinds.get('mfc',[])
        local_codes=[x['code'] for x in issues if x['run_id']==run]
        if len(a)>1:issue(run,'duplicate_data_candidates','; '.join(x['path'] for x in a),f'{len(a)} data candidates; no automatic selection')
        if len(b)>1:issue(run,'duplicate_mfc_candidates','; '.join(x['path'] for x in b),f'{len(b)} MFC candidates; no automatic selection')
        if not a:issue(run,'missing_data_partner','', 'No local data candidate' if b else 'Expected run not observed locally')
        if not b:issue(run,'missing_mfc_partner','', 'No local MFC candidate' if a else 'Expected run not observed locally')
        if len(a)==len(b)==1 and a[0]['status']=='ok' and b[0]['status']=='ok' and a[0]['experiment_date']!=b[0]['experiment_date']:
            issue(run,'cross_date_mismatch',a[0]['path']+'; '+b[0]['path'],f"{a[0]['experiment_date']} != {b[0]['experiment_date']}")
        codes=sorted(set(x['code'] for x in issues if x['run_id']==run))
        status='complete_validated_pair' if len(a)==len(b)==1 and not codes else 'incomplete_or_conflicting'
        runs.append(dict(run_id=run,status=status,data_candidates=len(a),mfc_candidates=len(b),data_paths='; '.join(x['path'] for x in a),mfc_paths='; '.join(x['path'] for x in b),experiment_date=a[0]['experiment_date'] if status=='complete_validated_pair' else '',issues='; '.join(codes)))
    write_csv(dest/'file_inventory.csv',FILE_COLUMNS,files)
    write_csv(dest/'run_inventory.csv',RUN_COLUMNS,runs)
    write_csv(dest/'pairing_issues.csv',ISSUE_COLUMNS,sorted(issues,key=lambda x:(x['run_id'],x['code'],x['path'])))
    summary={'recognized_files':len(files),'unrelated_files':len(unrelated),'unique_candidate_runs':len(groups),'complete_validated_pairs':sum(x['status']=='complete_validated_pair' for x in runs),'incomplete_or_conflicting_pairs':sum(x['status']!='complete_validated_pair' for x in runs),'issues':len(issues)}
    invalid_run_like_count=sum(x['status']=='invalid_filename_run_id' for x in files)
    if invalid_run_like_count:summary['invalid_run_like_files']=invalid_run_like_count
    manifest={'schema_version':'1.0','scope':'LOCAL FILE INVENTORY ONLY','input_dir':str(root),'output_dir':str(dest),'summary':summary,'expected_runs_manifest':provenance,'expected_run_ids':expected_ids,'unrelated_files':unrelated,'limitations':['Only first two CSV records parsed; full data integrity is not verified','SHA-256 streamed across entire recognized files','No timezone or clock synchronization assumptions','Filename/metadata pairing is local evidence, not NASA completeness certification','Unrelated files listed but not hashed','Strict mode exits nonzero for pairing issues or invalid recognized files']}
    (dest/'inventory_manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    report=['# PSI-20 BRE — local run inventory','','## OBSERVED IN LOCAL FILES',f"- Recognized CSV files: {summary['recognized_files']}",f"- Unrelated files (not inspected): {summary['unrelated_files']}",f"- Unique filename-derived candidate runs: {summary['unique_candidate_runs']}",f"- Complete validated local pairs: {summary['complete_validated_pairs']}",f"- Incomplete/conflicting run entries: {summary['incomplete_or_conflicting_pairs']}",f"- Pairing issues: {summary['issues']}",'','## OUR INFERENCE','- A validated pair means filename Test Point and experiment calendar date agree, not that full measurements are valid.','- No unobserved runs are considered missing without an explicitly supplied expected-run manifest.','- Duplicates are unresolved, even when their content hashes match.','','## REPORTED BY NASA','- None. No external NASA documentation was consulted or used to infer a complete run list.','','## Unrelated files (relative paths)']
    if invalid_run_like_count:report.insert(10,f'- Malformed run-like filenames: {invalid_run_like_count} (see pairing_issues.csv)')
    report += [f'- `{p}`' for p in unrelated] or ['- None']
    report += ['','## Unresolved questions','- Is there an authoritative complete expected-run list and provenance?','- Are experiment date and Test Point sufficient to uniquely identify source exports?','- Are source CSVs complete beyond their metadata and header records?','- Clock synchronization, timezones, calibration and scientific outcomes are not assessed.','','## Input manifest provenance',json.dumps(provenance,ensure_ascii=False) if provenance else 'No expected-run manifest supplied.']
    (dest/'inventory_report.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
    # Deterministic inventory over inventory outputs, excluding itself.
    lines=[f'{sha256(dest/name)}  {name}' for name in ['file_inventory.csv','run_inventory.csv','pairing_issues.csv','inventory_manifest.json','inventory_report.md']]
    (dest/'inventory_sha256.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    if strict and issues:raise ValueError(f'Strict inventory validation failed: {len(issues)} pairing issues (reports written to {dest})')
    return summary

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--input-dir',required=True);ap.add_argument('--out',required=True);ap.add_argument('--expected-runs');ap.add_argument('--strict',action='store_true')
    a=ap.parse_args();print(json.dumps(build(a.input_dir,a.out,a.expected_runs,a.strict),sort_keys=True))
if __name__=='__main__':main()
