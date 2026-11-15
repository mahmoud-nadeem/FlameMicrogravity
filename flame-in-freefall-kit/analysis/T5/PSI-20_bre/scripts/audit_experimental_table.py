#!/usr/bin/env python3
"""Non-destructive PSI-20 day-level experimental table quality and run-date crosswalk."""
import argparse,csv,hashlib,json,re
from collections import Counter,defaultdict
from datetime import date
from pathlib import Path

MONTHS={'jan':1,'january':1,'feb':2,'february':2,'mar':3,'march':3,'apr':4,'april':4,'may':5,'jun':6,'june':6,'jul':7,'july':7,'aug':8,'august':8,'sep':9,'sept':9,'september':9,'oct':10,'october':10,'nov':11,'november':11,'dec':12,'december':12}
EXPECTED=['Year','Month','Date','Burner Size (mm)','Fuel Bottle','Oxygen Conc (percent)','Flames Ignited','Notes']
ISSUE_COLS=['source_row','column','code','raw_value','detail','severity']
CROSS_COLS=['summary_source_row','summary_date','flames_ignited_raw','summary_fuel_bottle_raw','summary_oxygen_conc_raw','run_id','run_date','run_inventory_status','link_status','link_basis','ambiguity_note']

def digest(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest()

def read_csv(path):
 with open(path,encoding='utf-8-sig',newline='') as f:
  return list(csv.reader(f,strict=True))

def parse_day(row):
 try:
  month=MONTHS[row['Month'].strip().lower()]
  return date(int(row['Year'].strip()),month,int(row['Date'].strip())).isoformat()
 except (KeyError,ValueError,TypeError):return None

def audit(table_path,run_inventory_path,out):
 table_path=Path(table_path).resolve();run_inventory_path=Path(run_inventory_path).resolve();out=Path(out).resolve()
 if not table_path.is_file() or not run_inventory_path.is_file():raise FileNotFoundError('Table and run inventory must both exist')
 if out==table_path.parent or out==run_inventory_path.parent:raise ValueError('Output must not overwrite input directories')
 out.mkdir(parents=True,exist_ok=True)
 raw=read_csv(table_path)
 if not raw:raise ValueError('Empty experimental table')
 header=raw[0]; issues=[]
 def flag(row,col,code,val,detail,severity='review'):
  issues.append(dict(source_row=row,column=col,code=code,raw_value=val,detail=detail,severity=severity))
 if header!=EXPECTED:flag(1,'HEADER','unexpected_schema',json.dumps(header),f'Expected columns: {EXPECTED}','error')
 if len(header)!=len(set(header)):flag(1,'HEADER','duplicate_columns',json.dumps(header),'Duplicate column labels','error')
 rows=[]; days=defaultdict(list); total=0; numeric_count=0; missing=Counter();values=defaultdict(Counter);bad_width=0
 for line,fields in enumerate(raw[1:],2):
  if len(fields)!=len(header):
   bad_width+=1;flag(line,'ROW','field_count_mismatch',json.dumps(fields,ensure_ascii=False),f'Expected {len(header)} fields; found {len(fields)}','error')
  record={name:(fields[i] if i<len(fields) else '') for i,name in enumerate(header)}
  for name,val in record.items():
   values[name][val]+=1
   if not val.strip():
    missing[name]+=1
    if name!='Notes':flag(line,name,'missing_value',val,'Missing non-Notes field')
   elif val!=val.strip():flag(line,name,'surrounding_whitespace',val,'Noncanonical surrounding whitespace')
  day=parse_day(record) if all(k in record for k in ('Year','Month','Date')) else None
  if day:days[day].append(line)
  else:flag(line,'Year/Month/Date','invalid_calendar_date',str((record.get('Year'),record.get('Month'),record.get('Date'))),'Cannot parse calendar date','error')
  ignited=record.get('Flames Ignited','')
  if re.fullmatch(r'\d+',ignited.strip()):total+=int(ignited);numeric_count+=1
  else:flag(line,'Flames Ignited','invalid_count',ignited,'Not a nonnegative integer','error')
  size=record.get('Burner Size (mm)','')
  try:
   if float(size)<=0:flag(line,'Burner Size (mm)','nonpositive_size',size,'Nonpositive size')
  except ValueError:flag(line,'Burner Size (mm)','invalid_numeric',size,'Not numeric')
  oxy=record.get('Oxygen Conc (percent)','')
  if oxy:
   if '%' in oxy:
    flag(line,'Oxygen Conc (percent)','percent_symbol_in_value',oxy,'Percent symbol in field already labeled percent; preserve raw text')
   tokens=[t.strip() for t in oxy.split(';')]
   for token in tokens:
    match=re.fullmatch(r'(\d+(?:\.\d+)?)\s*(%)?',token)
    if not match:flag(line,'Oxygen Conc (percent)','unparsed_oxygen_token',token,'Token does not match simple numeric/percent syntax');continue
    if float(match[1])>100:flag(line,'Oxygen Conc (percent)','oxygen_value_over_100',oxy,'Token exceeds 100 on percent-labeled field; no correction inferred')
  rows.append((line,record,day))
 for name in ('Month','Fuel Bottle','Oxygen Conc (percent)'):
  if name in values:
   for val,count in sorted(values[name].items()):
    if name=='Fuel Bottle' and val and re.search(r'\d%\S',val):flag('ALL',name,'inconsistent_spacing',val,f'{count} row(s) have compact percent/fuel notation')
 for d,lines in days.items():
  if len(lines)>1:flag(';'.join(map(str,lines)),'Year/Month/Date','duplicate_summary_day',d,'Multiple day-level records; do not collapse')
 with run_inventory_path.open(encoding='utf-8-sig',newline='') as f:
  run_rows=list(csv.DictReader(f))
 verified=defaultdict(list);unverified=[]
 for run in run_rows:
  if run.get('status')=='complete_validated_pair' and re.fullmatch(r'\d{4}-\d{2}-\d{2}',run.get('experiment_date','')):
   try:date.fromisoformat(run['experiment_date']);verified[run['experiment_date']].append(run)
   except ValueError:unverified.append(run)
  else:unverified.append(run)
 cross=[]; matched_ids=set()
 for line,rec,d in rows:
  matches=verified.get(d,[]) if d else []
  if matches:
   for run in matches:
    matched_ids.add(run['run_id']);cross.append(dict(summary_source_row=line,summary_date=d or '',flames_ignited_raw=rec.get('Flames Ignited',''),summary_fuel_bottle_raw=rec.get('Fuel Bottle',''),summary_oxygen_conc_raw=rec.get('Oxygen Conc (percent)',''),run_id=run['run_id'],run_date=run['experiment_date'],run_inventory_status=run['status'],link_status='candidate_date_match',link_basis='verified_run_metadata_calendar_date_equals_summary_calendar_date',ambiguity_note='DAY-LEVEL match only; does not establish run-to-flame correspondence'+ ('; multiple local runs same day' if len(matches)>1 else '')))
  else:
   cross.append(dict(summary_source_row=line,summary_date=d or '',flames_ignited_raw=rec.get('Flames Ignited',''),summary_fuel_bottle_raw=rec.get('Fuel Bottle',''),summary_oxygen_conc_raw=rec.get('Oxygen Conc (percent)',''),run_id='',run_date='',run_inventory_status='',link_status='unmatched_summary_day' if d else 'invalid_summary_date',link_basis='no_verified_local_run_on_summary_day',ambiguity_note='No local verified pair on this date; not evidence NASA run absent'))
 for d,runs in sorted(verified.items()):
  for run in runs:
   if run['run_id'] not in matched_ids:cross.append(dict(summary_source_row='',summary_date='',flames_ignited_raw='',summary_fuel_bottle_raw='',summary_oxygen_conc_raw='',run_id=run['run_id'],run_date=d,run_inventory_status=run['status'],link_status='unmatched_local_run',link_basis='verified_run_date_not_in_summary_table',ambiguity_note='No summary day; not evidence of missing experimental record'))
 for run in unverified:
  cross.append(dict(summary_source_row='',summary_date='',flames_ignited_raw='',summary_fuel_bottle_raw='',summary_oxygen_conc_raw='',run_id=run.get('run_id',''),run_date=run.get('experiment_date',''),run_inventory_status=run.get('status',''),link_status='unverified_run_excluded',link_basis='run_inventory_not_complete_validated_pair',ambiguity_note='Cannot safely date-link'))
 def csv_write(name,cols,records):
  with (out/name).open('w',encoding='utf-8',newline='') as f:
   w=csv.DictWriter(f,fieldnames=cols,lineterminator='\n');w.writeheader();w.writerows(records)
 csv_write('table_quality_issues.csv',ISSUE_COLS,issues)
 csv_write('day_run_crosswalk.csv',CROSS_COLS,cross)
 counts=Counter(x['link_status'] for x in cross)
 summary={'schema_version':'1.0','scope':'DAY-LEVEL TABLE QUALITY AND LOCAL RUN DATE COVERAGE ONLY','table':{'path':str(table_path),'sha256':digest(table_path),'size_bytes':table_path.stat().st_size,'columns_original':header,'row_count':len(raw)-1,'well_formed_rows':len(raw)-1-bad_width,'valid_flames_ignited_count_rows':numeric_count,'flames_ignited_sum_of_valid_integer_cells':total,'unique_parsed_days':len(days),'missing_cells_by_column':dict(missing),'distinct_raw_values_by_column':{k:len(v) for k,v in values.items()}},'run_inventory':{'path':str(run_inventory_path),'sha256':digest(run_inventory_path),'row_count':len(run_rows),'validated_pairs_with_dates':sum(map(len,verified.values())),'unverified_run_rows':len(unverified)},'crosswalk':{'status_counts':dict(sorted(counts.items())),'matched_unique_local_run_ids':len(matched_ids),'candidate_link_count':counts['candidate_date_match'],'unmatched_summary_day_records':counts['unmatched_summary_day'],'unmatched_local_run_rows':counts['unmatched_local_run']},'quality_issue_count':len(issues),'provenance':{'table':'USER-SUPPLIED NASA PSI-20 STARTER-KIT CSV; NASA authorship not independently authenticated','run_dates':'LOCAL RUN INVENTORY: paired source Test Point and experiment calendar date metadata','nasa_report_comparison':'NOT PERFORMED: no exact source and page selected for comparable totals'},'limitations':['Summary days and raw runs have different granularities','Flames Ignited is not a raw run count','Matching dates imply candidate links only, not unique experimental attribution','No timezone assumptions; source notes say day change on ISS neglected','No normalization of suspicious oxygen percentages','No inferred NASA total run coverage']}
 (out/'coverage_summary.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False,sort_keys=True)+'\n',encoding='utf-8')
 profile=['# PSI-20 BRE experimental table — source-preserving profile','','## OBSERVED IN LOCAL FILES',f'- Source: `{table_path.name}`; SHA-256 `{summary["table"]["sha256"]}`',f'- Table records: **{len(raw)-1}**; columns: **{len(header)}**; distinct parsed calendar days: **{len(days)}**',f'- Sum of valid integer `Flames Ignited` cells: **{total}** ({numeric_count} cells). This is not a raw run count.',f'- Source header: `{json.dumps(header,ensure_ascii=False)}`','- Units are only those literally in column labels: `Burner Size (mm)` and `Oxygen Conc (percent)`; no physical conversion performed.','- Source notes describe oxygen concentrations as approximate and chamber pressure variations as omitted.','- Source notes state the day counts neglect the day change on ISS.','', '## Missing values (including optional Notes)']
 profile += [f'- `{h}`: {missing[h]}' for h in header]
 profile += ['','## Raw-value distributions (no normalization)']
 for h in header:
  profile.append(f'### {h}')
  profile.extend(f'- `{json.dumps(v,ensure_ascii=False)}`: {n}' for v,n in sorted(values[h].items()))
 profile += ['','## Suspicious raw values','- `3400%` and `2100%` occur in `Oxygen Conc (percent)` and exceed 100 when read literally. These are preserved unchanged; intended meaning unknown.','- `100%C2H4` and `100% C2H4` differ in spacing; no canonicalization.','- Month abbreviations and full month names coexist.','- Summary rows are not strictly chronological (2020 Dec 5 precedes Dec 4).','', '## OUR INFERENCE','- The percent strings warrant documentation review; do not assume decimal or formatting correction.','- Date-only matching cannot identify which flame ignition corresponds to which raw run.','','## REPORTED BY NASA','- No independent report-page comparison was performed. The uploaded table is attributed to the NASA starter kit by the user; this provenance has not been independently authenticated.']
 (out/'experimental_table_profile.md').write_text('\n'.join(profile)+'\n',encoding='utf-8')
 questions=['# Reconciliation questions — Task 04','','1. What are the intended values and original formatting for `3400%` (2019-03-07) and `2100%` (2019-04-01)? No correction applied.','2. What constitutes one `Flames Ignited` count versus a run/test point in PSI-20?','3. Does the day assignment in the table use an operations day that explicitly neglects ISS calendar rollover? How does this relate to CSV metadata calendar dates?','4. Can NASA provide a documented run-to-day/test-point mapping?','5. Can the complete expected-run manifest be supplied with authoritative provenance?','6. Which NASA report, exact page and table defines a comparable `Flames Ignited` total, if any? No forced reconciliation.','7. What do the percent-labeled oxygen tokens and bottle notation mean when formatting is inconsistent?','8. What chamber pressures and operational settings are absent from the day-level table?','', '## OBSERVED IN LOCAL FILES',f'- {len(raw)-1} day-level rows; valid Flames Ignited sum {total}.',f'- {counts["candidate_date_match"]} candidate date links, {counts["unmatched_summary_day"]} unmatched summary rows.','', '## OUR INFERENCE','- Date equality alone does not establish event correspondence or local run completeness.','','## REPORTED BY NASA','- No independently page-verified numerical reconciliation claim is made.']
 (out/'reconciliation_questions.md').write_text('\n'.join(questions)+'\n',encoding='utf-8')
 files=['experimental_table_profile.md','table_quality_issues.csv','day_run_crosswalk.csv','coverage_summary.json','reconciliation_questions.md']
 (out/'table_audit_sha256.txt').write_text(''.join(f'{digest(out/name)}  {name}\n' for name in files),encoding='utf-8')
 return summary

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--table',required=True);p.add_argument('--run-inventory',required=True);p.add_argument('--out',required=True)
 a=p.parse_args();result=audit(a.table,a.run_inventory,a.out);print(json.dumps({'rows':result['table']['row_count'],'flames_ignited_sum':result['table']['flames_ignited_sum_of_valid_integer_cells'],'crosswalk':result['crosswalk'],'issues':result['quality_issue_count']},sort_keys=True))
if __name__=='__main__':main()
