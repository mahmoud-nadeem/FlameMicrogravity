#!/usr/bin/env python3
"""Task 04C: non-destructive, page-cited comparison of PSI-20 BRE day-level records."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
from datetime import date
from collections import Counter

REPORT = 'ACME/BRE Final Report (2022)'
REPORT_DATE = '2022-02-01'
REFERENCE = [
    ('19066', '2019-03-07', '34%', '6', '24;112'),
    ('19091', '2019-04-01', '21%', '0', '24;112'),
    ('20261', '2020-09-17', '26.5%; 34%', '13', '24;112'),
    ('20279', '2020-10-05', '25%; 34%; 40%', '21', '24;112'),
    ('19094', '2019-04-04', '21%; 26.5%; 34%', '9', '23;24'),
    ('19094', '2019-04-05', '21%; 26.5%; 34%', '9', '112'),
]
# Page 23 explicitly identifies April 4 as the corrected operational test-day date.
# Page 112 preserves the superseded April 5 listing as historical provenance.
REF_FIELDS = ['report_title','report_date','pdf_pages','test_day','reference_calendar_date','reference_oxygen_concentration_text','reference_flames_ignited_count','provenance','verification_status','date_status','interpretation_note']
DIFF_FIELDS = ['discrepancy_id','discrepancy_type','csv_source_row','csv_calendar_date','csv_column','csv_raw_value','report_test_day','report_calendar_date','report_raw_value','report_pdf_pages','verification_status','interpretation_limit','resolution_status','authoritative_explanation_pdf_page']

def sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1048576),b''): h.update(b)
    return h.hexdigest()

def write_csv(path, fields, rows):
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(rows)

def csv_date(row):
    from importlib.util import spec_from_file_location,module_from_spec
    # Independent parser to avoid altering the approved Task 04 module.
    months={'feb':2,'march':3,'april':4,'sept':9,'oct':10,'dec':12,'jan':1}
    return date(int(row['Year']),months[row['Month'].strip().lower()],int(row['Date'])).isoformat()

def reconcile(table, out):
    table=Path(table).resolve();out=Path(out).resolve()
    if not table.is_file(): raise FileNotFoundError(table)
    if out==table.parent: raise ValueError('Output must not be source directory')
    before=sha256(table)
    with table.open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f);rows=[(i,r,csv_date(r)) for i,r in enumerate(reader,2)]
    out.mkdir(parents=True,exist_ok=True)
    references=[]
    for day,d,oxygen,flames,pages in REFERENCE:
        is_corrected=day=='19094' and d=='2019-04-04'
        is_historical=day=='19094' and d=='2019-04-05'
        references.append(dict(zip(REF_FIELDS,[REPORT,REPORT_DATE,pages,day,d,oxygen,flames,
            'NASA ACME/BRE Final Report, PDF page(s) '+pages,'independently_checked_pdf_text',
            'corrected_operational_date' if is_corrected else 'historical_superseded_date' if is_historical else 'as_reported',
            'PDF page 23 explicitly corrects 19094 to April 4; April 5 is historical (page 112)' if (is_corrected or is_historical) else ''])))
    write_csv(out/'report_reference_manifest.csv',REF_FIELDS,references)
    differences=[]
    def add(kind,row,col,raw,ref,reported,limit,resolution='unresolved',explanation_page=''):
        differences.append(dict(discrepancy_id=f'D{len(differences)+1:03d}',discrepancy_type=kind,csv_source_row=row[0] if row else '',csv_calendar_date=row[2] if row else '',csv_column=col,csv_raw_value=raw,report_test_day=ref['test_day'],report_calendar_date=ref['reference_calendar_date'],report_raw_value=reported,report_pdf_pages=ref['pdf_pages'],verification_status='source_difference_verified',interpretation_limit=limit,resolution_status=resolution,authoritative_explanation_pdf_page=explanation_page))
    for ref in references[:4]:
        # Use documented date OR documented count + known date difference to identify rows; never infer a run ID.
        if ref['test_day'] in ('19066','19091'):
            matches=[r for r in rows if r[2]==ref['reference_calendar_date']]
        else:
            target={'20261':'2020-10-17','20279':'2020-12-05'}[ref['test_day']]
            matches=[r for r in rows if r[2]==target and r[1]['Flames Ignited']==ref['reference_flames_ignited_count']]
        if len(matches)!=1: raise ValueError(f'Expected unique CSV day-level record for {ref["test_day"]}, got {len(matches)}')
        row=matches[0]
        if row[1]['Flames Ignited']!=ref['reference_flames_ignited_count']:
            add('flame_count_difference',row,'Flames Ignited',row[1]['Flames Ignited'],ref,ref['reference_flames_ignited_count'],'Day-level count comparison; definitions may differ')
        if row[2]!=ref['reference_calendar_date']:
            add('calendar_date_difference',row,'Year/Month/Date',row[2],ref,ref['reference_calendar_date'],'Calendar date discrepancy only; not a raw-run date correction')
        if ref['test_day'] in ('19066','19091') and row[1]['Oxygen Conc (percent)']!=ref['reference_oxygen_concentration_text']:
            add('oxygen_text_difference',row,'Oxygen Conc (percent)',row[1]['Oxygen Conc (percent)'],ref,ref['reference_oxygen_concentration_text'],'Different source strings; no inferred correction or calibration')
    # Additional internal report discrepancy: same Test Day, two Table 1 versions.
    a,b=references[4:6]
    if a['reference_calendar_date']!=b['reference_calendar_date']:
        add('explained_historical_source_difference',None,'NASA Table 1','',b,b['reference_calendar_date'],'PDF page 23 explicitly corrects Test Day 19094 to April 4; page 112 retains the historical April 5 entry. The operational test-day date is when testing began, even if later tests crossed midnight.','explained_by_report','23')
    write_csv(out/'cross_source_discrepancies.csv',DIFF_FIELDS,differences)
    count_sum=sum(int(r[1]['Flames Ignited']) for r in rows)
    # Page 127 wording is specifically "Round 2 tests were finished with 196 successful ignitions".
    notes=f'''# Task 04C — NASA report reconciliation (non-destructive)

## OBSERVED IN LOCAL FILES
- Source CSV SHA-256: `{before}`; {len(rows)} day-level records; sum of `Flames Ignited` = **{count_sum}**.
- Four CSV-versus-report differences are preserved individually in `cross_source_discrepancies.csv`.
- One additional **explained historical source difference** is retained as a provenance record, not an unresolved date discrepancy.
- Original CSV raw values and row order, plus all Task 04 legacy outputs, remain unchanged.

## REPORTED BY NASA — independently inspected PDF pages
- **{REPORT}**, dated **1 February 2022**, Table 1 on PDF **pages 24 and 112**: Test Day 19066 (7 March 2019, 34%, 6 flames); 19091 (1 April 2019, 21%, 0 flames); 20261 (17 September 2020, 26.5% and 34%, 13 flames); 20279 (5 October 2020, 25%, 34%, 40%, 21 flames).
- **PDF page 23 (explicit correction):** Test Day **19094** is corrected to **4 April 2019**. Older 30-day reports had listed April 5. Some testing continued past midnight in Cleveland, but NASA identifies a Test Day by **the calendar date the test day began**. Table 1 **page 24** uses April 4, while its historical Appendix reproduction on **page 112** retains April 5. The original experimental CSV lists April 4. The page-112 date remains documented as historical provenance, not an unresolved conflict.
- **PDF page 29:** **“BRE tests in orbit were finished with 196 successful ignitions.”** This is an overall orbital-test statement, in the flammability-map discussion; it does not explicitly restrict the 196 count to Round 2.
- **PDF page 110:** **62** flames in Round 1, **132** in Round 2, **194 total flames ignited**.
- **PDF page 116:** **194 flames ignited**, in the completeness/quality-of-data section.
- **PDF page 127:** **“Round 2 tests were finished with 196 successful ignitions.”** This wording explicitly invokes Round 2, whereas page 110 reports 132 Round 2 flames. **Apparent scope inconsistency unresolved.**

## OUR INFERENCE / UNRESOLVED
- The CSV sum **194** agrees numerically with the NASA total on pages 110 and 116; this does not prove equivalence of counting definitions with **196 successful ignitions** on pages 29 and 127.
- The **194 versus 196** discrepancy is **unresolved**; do not invent an explanation. The **page-127 Round 2 scope versus page-110 Round 2 count of 132** is an additional apparent scope inconsistency, not resolved by page 29.
- `3400%` versus `34%` and `2100%` versus `21%` are source-string differences, not demonstrated measurement errors or authorized corrections.
- CSV dates 2020-10-17 and 2020-12-05 differ from NASA Table 1 dates 2020-09-17 and 2020-10-05 for candidate day-level correspondences (13 and 21 flames). No raw-run identities are inferred.
- Day-level `Flames Ignited` counts do not equal raw CSV run counts. No calibration, classification, modeling, or causal inference.

## Reproduction
```bash
python scripts/reconcile_nasa_report.py --table "/mnt/data/PSI-20_Experimental table_ACME BRE.csv" --out table_audit
```
'''
    (out/'report_reconciliation.md').write_text(notes,encoding='utf-8')
    output_names=['report_reference_manifest.csv','cross_source_discrepancies.csv','report_reconciliation.md']
    (out/'report_reconciliation_sha256.txt').write_text(''.join(f'{sha256(out/n)}  {n}\n' for n in output_names),encoding='utf-8')
    if sha256(table)!=before: raise RuntimeError('Input source hash changed')
    return {'source_sha256':before,'rows':len(rows),'flames_ignited_sum':count_sum,'cross_source_differences':sum(d['discrepancy_type']!='explained_historical_source_difference' for d in differences),'report_internal_differences':sum(d['discrepancy_type']=='explained_historical_source_difference' for d in differences),'output_sha256':{n:sha256(out/n) for n in output_names}}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--table',required=True);p.add_argument('--out',required=True)
    a=p.parse_args();print(json.dumps(reconcile(a.table,a.out),sort_keys=True,indent=2))
if __name__=='__main__':main()
