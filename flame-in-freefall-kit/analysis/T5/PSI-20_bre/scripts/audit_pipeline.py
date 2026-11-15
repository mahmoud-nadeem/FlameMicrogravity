#!/usr/bin/env python3
"""Lossless-source, reproducible PSI-20 CSV audit. Requires pandas, numpy, matplotlib."""
import argparse,csv,hashlib,json,re,collections
from pathlib import Path
from datetime import datetime,timedelta
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def digest(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def load(p):
 raw=Path(p).read_bytes(); enc='utf-8-sig'
 try: s=raw.decode(enc)
 except UnicodeDecodeError: enc='latin-1';s=raw.decode(enc)
 import io
 rows=list(csv.reader(io.StringIO(s,newline=''),delimiter=','))
 if len(rows)<2:raise ValueError('Missing metadata/header')
 meta,headers=rows[:2]; records=rows[2:]
 if len(set(headers))!=len(headers):raise ValueError('Duplicate header names')
 bad=[i+3 for i,r in enumerate(records) if len(r)!=len(headers)]
 if bad:raise ValueError(f'Width mismatch at physical lines {bad[:20]} (total {len(bad)})')
 frame=pd.DataFrame(records,columns=headers,dtype=str)
 return {'metadata_raw_fields':meta,'metadata_key_values':{a.strip():b.strip() for x in meta[1:] if ':' in x for a,b in [x.split(':',1)]},'metadata_first_field':meta[0],'headers':headers,'frame':frame,'encoding':enc,'delimiter':',','bytes':len(raw),'sha256':digest(p),'records':len(records),'bad_width_lines':bad}
def experiment_date(first):
 match=re.match(r'\s*(\d{4}-\d{2}-\d{2})(?=\s|$)',first)
 if not match: raise ValueError(f'Missing ISO experiment date in metadata: {first!r}')
 try: return datetime.strptime(match.group(1),'%Y-%m-%d').date().isoformat()
 except ValueError as exc: raise ValueError(f'Invalid experiment date in metadata: {first!r}') from exc

def timestamps(times,first):
 match=re.match(r'\s*(\d{4}-\d{2}-\d{2})\s+',first)
 if not match: return pd.Series(pd.NaT,index=times.index), 'No ISO date in metadata first field'
 base=datetime.strptime(match.group(1),'%Y-%m-%d')
 parsed=[];prev=None;day=0
 for value in times:
  m=re.fullmatch(r'\s*(\d{2}):(\d{2}):(\d{2}):(\d{1,6})\s*',str(value))
  if not m:parsed.append(pd.NaT);continue
  hh,mm,ss,frac=map(int,m.groups()); digits=len(m.group(4))
  if hh>23 or mm>59 or ss>59:parsed.append(pd.NaT);continue
  tod=timedelta(hours=hh,minutes=mm,seconds=ss,microseconds=frac*10**(6-digits))
  # Do NOT assume midnight rollover: a negative jump remains visible.
  t=base+tod;parsed.append(t)
 return pd.Series(pd.to_datetime(parsed),index=times.index),None
def audit_one(obj,kind,out,run, gap_threshold_s=1.0):
 df=obj['frame'];ts,error=timestamps(df['Time'],obj['metadata_first_field']); obj['timestamps']=ts
 q=[];numeric={}; n=len(df)
 for col in df.columns:
  raw=df[col].astype(str).str.strip(); missing=raw.eq('') | raw.str.lower().isin(['null','none','na','n/a'])
  if col=='Time':
   q.append(dict(source=kind,column=col,records=n,missing=int(missing.sum()),nonnumeric='',nan_tokens='',positive_infinity='',negative_infinity='',min='',max='',median='',unique_raw=int(raw.nunique(dropna=False)),constant_candidate=bool(raw.nunique()==1),saturation_candidate=False,channel_role='timestamp'));continue
  vals=pd.to_numeric(raw.mask(missing),errors='coerce');nan_tokens=raw.str.lower().isin(['nan','+nan','-nan']); pos=np.isposinf(vals);neg=np.isneginf(vals)
  nonnumeric=(vals.isna() & ~missing & ~nan_tokens); finite=vals[np.isfinite(vals)];numeric[col]=vals
  counts=finite.value_counts(); max_repeat=int(counts.iloc[0]) if len(counts) else 0
  # Heuristic only, not evidence of physical saturation.
  sat=bool(kind=='data' and len(finite)>=20 and finite.nunique()>1 and (int((finite==finite.min()).sum())>=max(20,len(finite)*.05) or int((finite==finite.max()).sum())>=max(20,len(finite)*.05)))
  q.append(dict(source=kind,column=col,records=n,missing=int(missing.sum()),nonnumeric=int(nonnumeric.sum()),nan_tokens=int(nan_tokens.sum()),positive_infinity=int(pos.sum()),negative_infinity=int(neg.sum()),min=float(finite.min()) if len(finite) else '',max=float(finite.max()) if len(finite) else '',median=float(finite.median()) if len(finite) else '',unique_raw=int(raw.nunique(dropna=False)),constant_candidate=bool(len(finite)>0 and finite.nunique()==1),saturation_candidate=sat,channel_role='control_setpoint' if kind=='mfc' else 'raw_measured_channel'))
 delta=ts.diff().dt.total_seconds(); positive=delta[delta>0];valid=delta.dropna()
 modal=float(positive.round(6).mode().iloc[0]) if len(positive) else None
 # Report all non-modal positive intervals, not just extreme gaps; no fixed sampling assumption.
 events=[]
 for i,d in delta.items():
  if pd.isna(d):continue
  if d<=0 or (modal is not None and abs(d-modal)>1e-9):
   events.append({'source':kind,'row_index_1based':int(i+1),'source_csv_record':int(i+3),'previous_time':str(ts.iloc[i-1]),'current_time':str(ts.iloc[i]),'delta_seconds':float(d),'type':'duplicate_timestamp' if d==0 else 'backward_jump' if d<0 else 'major_gap' if d>=gap_threshold_s else 'normal_positive_variation'})
 timing={'source':kind,'records':n,'valid_timestamps':int(ts.notna().sum()),'invalid_timestamps':int(ts.isna().sum()),'timestamp_parse_issue':error,'monotonic_nondecreasing':bool(ts.dropna().is_monotonic_increasing),'duplicate_timestamps':int(ts.duplicated(keep='first').sum()-max(0,int(ts.isna().sum())-1)),'negative_intervals':int((delta<0).sum()),'zero_intervals':int((delta==0).sum()),'gap_threshold_seconds':gap_threshold_s,'major_gap_count':int((delta>=gap_threshold_s).sum()),'positive_interval_p01_s':float(positive.quantile(.01)) if len(positive) else None,'positive_interval_p95_s':float(positive.quantile(.95)) if len(positive) else None,'positive_interval_p99_s':float(positive.quantile(.99)) if len(positive) else None,'positive_interval_count':len(positive),'positive_interval_min_s':float(positive.min()) if len(positive) else None,'positive_interval_median_s':float(positive.median()) if len(positive) else None,'positive_interval_max_s':float(positive.max()) if len(positive) else None,'modal_positive_interval_s':modal,'interval_frequency_seconds':{str(k):int(v) for k,v in valid.round(6).value_counts().sort_index().items()},'discontinuities':events,'first_timestamp':str(ts.iloc[0]) if n else None,'last_timestamp':str(ts.iloc[-1]) if n else None}
 duplicates=int(df.duplicated(keep=False).sum());timing['rows_participating_in_exact_duplicates']=duplicates;timing['exact_duplicate_rows_beyond_first']=int(df.duplicated().sum())
 return q,timing,numeric

def run_pipeline(data,mfc,out,preview=False,run_id=None,gap_threshold_s=1.0):
 out=Path(out);(out/'audit').mkdir(parents=True,exist_ok=True);(out/'charts').mkdir(exist_ok=True)
 sources={'data':load(data),'mfc':load(mfc)}
 ids=[v['metadata_key_values'].get('Test Point','').strip() for v in sources.values()]
 if not all(ids) or len(set(ids))!=1:raise ValueError(f'Metadata Test Point mismatch or missing: {ids}')
 dates={k:experiment_date(v['metadata_first_field']) for k,v in sources.items()}
 if len(set(dates.values()))!=1:raise ValueError(f'Experiment date mismatch between data and MFC metadata: {dates}')
 run=run_id or ids[0]
 if not re.fullmatch(r'[A-Za-z0-9_-]+',run):raise ValueError('Unsafe run ID')
 if run!=ids[0]:raise ValueError(f'--run-id {run} does not match source metadata {ids[0]}')
 if gap_threshold_s<=0 or not np.isfinite(gap_threshold_s):raise ValueError('Gap threshold must be positive and finite')
 for kind,obj in sources.items():
  if 'Time' not in obj['headers']:raise ValueError(f'{kind}: missing Time')
  obj['quality'],obj['timing'],obj['numeric']=audit_one(obj,kind,out,run,gap_threshold_s)
 def dump(name,x): (out/'audit'/name).write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
 dump(f'{run}_metadata.json',{k:{'source_file':str(Path(data if k=='data' else mfc).name),'first_record_raw_fields':v['metadata_raw_fields'],'first_record_first_field':v['metadata_first_field'],'parsed_key_values':v['metadata_key_values']} for k,v in sources.items()})
 dump(f'{run}_schema.json',{k:{'columns':v['headers'],'column_count':len(v['headers']),'measurement_records':v['records'],'encoding':v['encoding'],'delimiter':v['delimiter'],'metadata_records':1,'header_records':1,'invalid_width_records':len(v['bad_width_lines']),'source_bytes':v['bytes'],'sha256':v['sha256']} for k,v in sources.items()})
 pd.DataFrame([r for v in sources.values() for r in v['quality']]).to_csv(out/'audit'/f'{run}_quality_report.csv',index=False)
 dump(f'{run}_timing_report.json',{'timestamp_assumptions':['ISO calendar date extracted from first metadata field','Time is HH:MM:SS:fraction; fraction interpreted as decimal fraction of a second','No timezone assumed; timestamps are naive local clock labels','No automatic midnight rollover, interpolation, deduplication or reordering',f'Operational major-gap threshold >= {gap_threshold_s} seconds (user-configurable, not a NASA acquisition specification); shorter positive deviations are normal interval variation'],**{k:v['timing'] for k,v in sources.items()}})
 mf=sources['mfc'];df=mf['frame'];cols=df.columns[1:]; changed=df[list(cols)].ne(df[list(cols)].shift()).any(axis=1)
 ev=df.loc[changed].copy();ev.insert(0,'mfc_change_event_id',[f'{run}_E{i:04d}' for i in range(1,len(ev)+1)]);ev.insert(1,'event_kind',['initial_state' if i==0 else 'setpoint_change' for i in ev.index]);ev.insert(2,'source_csv_record',ev.index+3);ev.insert(1,'original_row_1based',ev.index+1);ev.insert(2,'parsed_timestamp',mf['timestamps'].loc[changed].astype(str).values)
 ev['changed_channels']= [','.join([c for c in cols if i==0 or df.loc[i,c]!=df.loc[i-1,c]]) for i in ev.index]
 gap_intervals=[e for e in sources['data']['timing']['discontinuities'] if e['type']=='major_gap']
 ev['inside_major_data_gap']=[any(pd.Timestamp(g['previous_time'])<t<pd.Timestamp(g['current_time']) for g in gap_intervals) if pd.notna(t) else False for t in mf['timestamps'].loc[changed]]
 ev['clock_sync_verified']=False
 ev.to_csv(out/'audit'/f'{run}_mfc_events.csv',index=False)
 d=sources['data']; plot_cols=[c for c in ['IonCurrent','PMT1','BRECenter','TCBurner','MFCA3FuelFlow'] if c in d['numeric']]
 for c in plot_cols:
  fig,ax=plt.subplots(figsize=(11,3.6));ax.plot(d['timestamps'],d['numeric'][c],linewidth=.5);ax.set(title=f'RAW SENSOR SIGNALS — {c} (uncalibrated)',xlabel='Timestamp (metadata date + Time; timezone unspecified)',ylabel=f'{c} (raw recorded values)');ax.grid(alpha=.25);fig.autofmt_xdate();fig.tight_layout();fig.savefig(out/'charts'/f'{run}_raw_{c}.png',dpi=130);plt.close(fig)
 if preview:
  # A record lookup is NOT an event lookup or a measured response.
  left=pd.DataFrame({'data_original_row_1based':np.arange(1,len(d['frame'])+1),'data_source_csv_record':np.arange(3,len(d['frame'])+3),'data_timestamp':d['timestamps']})
  right=pd.DataFrame({'mfc_original_row_1based':np.arange(1,len(df)+1),'mfc_source_csv_record':np.arange(3,len(df)+3),'mfc_timestamp':mf['timestamps']})
  event_by_row=dict(zip(ev['original_row_1based'].astype(int),ev['mfc_change_event_id']))
  right['matched_record_change_event_id']=right['mfc_original_row_1based'].map(event_by_row)
  valid_left=left.dropna(subset=['data_timestamp']).sort_values('data_timestamp',kind='stable')
  valid_right=right.dropna(subset=['mfc_timestamp']).sort_values(['mfc_timestamp','mfc_original_row_1based'],kind='stable')
  aligned=pd.merge_asof(valid_left,valid_right,left_on='data_timestamp',right_on='mfc_timestamp',direction='backward',allow_exact_matches=True)
  aligned=pd.concat([aligned,left[left['data_timestamp'].isna()]],ignore_index=True).sort_values('data_original_row_1based',kind='stable')
  aligned['matched_mfc_record_is_change_event']=aligned['matched_record_change_event_id'].notna()
  aligned['matched_mfc_age_seconds']=(aligned['data_timestamp']-aligned['mfc_timestamp']).dt.total_seconds()
  # Operational freshness screen, not an instrument specification.
  aligned['stale_lookup_age_exceeds_threshold']=aligned['matched_mfc_age_seconds']>gap_threshold_s
  aligned['matched_mfc_timestamp_within_major_data_gap']=[any(pd.Timestamp(g['previous_time'])<t<pd.Timestamp(g['current_time']) for g in gap_intervals) if pd.notna(t) else False for t in aligned['mfc_timestamp']]
  aligned['lookup_crosses_major_data_gap']=[any(pd.notna(m) and pd.notna(t) and m<=pd.Timestamp(g['previous_time']) and t>=pd.Timestamp(g['current_time']) for g in gap_intervals) for m,t in zip(aligned['mfc_timestamp'],aligned['data_timestamp'])]
  aligned['stale_timestamp_lookup']=aligned['stale_lookup_age_exceeds_threshold']|aligned['lookup_crosses_major_data_gap']
  aligned['clock_synchronization']='UNVERIFIED'
  aligned['interpretation']='MFC RECORD TIMESTAMP LOOKUP ONLY - NOT A MEASURED RESPONSE OR VERIFIED SYNCHRONIZED STATE'
  aligned.to_csv(out/'audit'/f'{run}_alignment_preview.csv',index=False)
 summary=[f'# Run {run} — raw audit summary','','All statements below: **OBSERVED IN DATA** unless labeled as assumptions.','','| Source | Records | Exact duplicates beyond first | Duplicate timestamps | Negative intervals | Non-modal/zero intervals |','|---|---:|---:|---:|---:|---:|']
 for k,v in sources.items():
  t=v['timing'];summary.append(f"| {k} | {v['records']:,} | {t['exact_duplicate_rows_beyond_first']:,} | {t['duplicate_timestamps']:,} | {t['negative_intervals']:,} | {len(t['discontinuities']):,} |")
 summary+=['','No raw measurement records were dropped. All numerical channel summaries are uncalibrated.','Potential saturation screening applies only to measured data channels, never MFC control setpoints; no physical saturation is confirmed.',f'Major data gaps (threshold >= {gap_threshold_s} s): {sources["data"]["timing"]["major_gap_count"]}. Full interval statistics and source positions in timing_report.json.','No flame-extinction classification, causal inference, physical calibration, or modeling was performed.']
 summary += ['','## Alignment safety (ASSUMPTIONS / OPERATIONAL SCREENING)','MFC record timestamp lookup is not a change-event measurement or response. Repeated records have no independent change-event ID. Staleness uses the operational gap threshold and gap crossing; clocks remain unverified.','','## MFC events within major data gaps (OBSERVED TIMESTAMP LABELS; clock synchronization UNVERIFIED)']
 for _,r in ev[ev['inside_major_data_gap']].iterrows():summary.append(f"- MFC source row {r['original_row_1based']} at {r['parsed_timestamp']} lies within a data timestamp gap; this is NOT measured response.")
 (out/'audit'/f'{run}_audit_summary.md').write_text('\n'.join(summary)+'\n')
 log=[f'# Data log — PSI-20 / {run}','','## Inputs (OBSERVED IN DATA)']
 for k,v in sources.items():log.append(f"- {k}: `{Path(data if k=='data' else mfc).name}`; {v['bytes']} bytes; SHA-256 `{v['sha256']}`; {v['records']} measurement records; {len(v['headers'])} columns")
 log+=['','## Transformations','- Read raw bytes; decode UTF-8-SIG, fall back to Latin-1 only on decoding failure.','- CSV record 1 preserved as ordered metadata fields; record 2 used as headers.','- Original row order and repeated timestamps retained; conversion errors counted, not dropped.','- Parse date from metadata first field and time-of-day from Time, without timezone or midnight rollover.','- MFC change-event IDs assigned only to setpoint changes; first row is initial state, repeated rows are not independent events.','- Charts use selected raw numeric channel values, no calibration.']
 if preview:log+=['- Optional backward as-of timestamp preview: last MFC row at or before each data timestamp, no tolerance, stable sort, equal timestamps resolve to last source-order MFC row. This is a visualization aid, NOT a measured synchronized state; rows with invalid timestamps excluded from preview only.']
 log+=['','## Uncertainties / limitations','- MFC clock synchronization with sensor clock is UNVERIFIED. Events inside data gaps are timestamp-label observations only.','- Alignment preview retains source row IDs and all data rows, including invalid timestamps, and is NOT a measured MFC response.','- Metadata field labels are preserved, but sensor calibration and physical meanings have not been independently verified against NASA documentation.','- Experiment calendar dates must agree across source metadata; timezone, clock synchronization, possible rollover, and actual acquisition sampling behavior are undocumented.','- Non-modal positive intervals are reported without asserting expected sample rate.','- No extinction outcome or scientific causality can be established from this audit.']
 (out/'data_log.md').write_text('\n'.join(log)+'\n')
 write_inventory(out)
 return sources

def write_inventory(out):
 """Stable relative-path SHA-256 inventory; never hash the inventory itself."""
 out=Path(out)
 target=out/'audit'/'file_inventory_sha256.txt'
 entries=[]
 for p in sorted(out.rglob('*')):
  if p.is_file() and p!=target and '__pycache__' not in p.parts:
   entries.append(f'{digest(p)}  {p.relative_to(out).as_posix()}')
 target.write_text('\n'.join(entries)+'\n',encoding='utf-8')

def main():
 p=argparse.ArgumentParser();p.add_argument('--data',required=True);p.add_argument('--mfc',required=True);p.add_argument('--out',required=True);p.add_argument('--alignment-preview',action='store_true');p.add_argument('--run-id');p.add_argument('--major-gap-seconds',type=float,default=1.0);a=p.parse_args();run_pipeline(a.data,a.mfc,a.out,a.alignment_preview,a.run_id,a.major_gap_seconds)
if __name__=='__main__':main()
