#!/usr/bin/env python3
"""Descriptive, non-calibrated PSI-20 BRE EDA. Python 3.10+, pandas, matplotlib, numpy."""
import csv
import hashlib
from pathlib import Path
import argparse
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TABLE = Path('/mnt/data/PSI-20_Experimental table_ACME BRE.csv')
DEFAULT_RAW = Path('/mnt/data/19056A2_data.csv')
EXPECTED = {'table':'4aa5d3f98708ceacced5c620d46858b9965f8d4d941b203229f46467d53e5ab7','raw':'9b90a1c2b0c227823df193ba0a070d07bb30e42077fb0534ca38bc47687dad49'}

def sha256(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def save(fig,path):
    fig.savefig(path,dpi=170,bbox_inches='tight',facecolor='white')
    plt.close(fig)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--table',type=Path,default=DEFAULT_TABLE)
    ap.add_argument('--raw',type=Path,default=DEFAULT_RAW)
    ap.add_argument('--out',type=Path,default=ROOT/'eda')
    args=ap.parse_args(); out=args.out;out.mkdir(parents=True,exist_ok=True)
    hashes={'table':sha256(args.table),'raw':sha256(args.raw)}
    for k,v in EXPECTED.items():
        if hashes[k]!=v: raise ValueError(f'{k} source hash differs from approved baseline: {hashes[k]}')
    table=pd.read_csv(args.table,dtype=str,keep_default_na=False)
    if len(table)!=18:raise ValueError('Unexpected summary row count')
    counts=pd.to_numeric(table['Flames Ignited'],errors='raise').astype(int)
    if counts.sum()!=194:raise ValueError('Unexpected Flames Ignited total')
    month={'Feb':2,'March':3,'April':4,'Sept':9,'Oct':10,'Dec':12,'Jan':1}
    dates=[pd.Timestamp(int(r['Year']),month[r['Month']],int(r['Date'])) for _,r in table.iterrows()]
    labels=[d.strftime('%Y-%m-%d') for d in dates]
    order=sorted(range(len(table)),key=lambda i:(dates[i],i))  # Preserve CSV dates/counts; sort display only.
    sorted_counts=[int(counts.iloc[i]) for i in order]
    sorted_labels=[labels[i] for i in order]
    fig,ax=plt.subplots(figsize=(12,5));bars=ax.bar(range(len(table)),sorted_counts,color='#336c94')
    ax.set_xticks(range(len(table)),sorted_labels,rotation=65,ha='right',fontsize=8);ax.set_ylabel('Flames ignited (day-level count)');ax.set_xlabel('Date as recorded in experimental CSV');ax.set_title('BRE experimental summary: flames ignited by recorded day');ax.grid(axis='y',alpha=.2)
    for b,n in zip(bars,sorted_counts):ax.text(b.get_x()+b.get_width()/2,b.get_height()+.25,str(n),ha='center',fontsize=8)
    ax.text(0,-.36,'Dates are as recorded in the CSV; known NASA source-date discrepancies are retained.',transform=ax.transAxes,fontsize=8,color='#555555')
    fig.tight_layout();save(fig,out/'01_flames_by_day.png')
    fig,ax=plt.subplots(figsize=(8,4.7));bins=np.arange(-.5,25.6,3);ax.hist(counts,bins=bins,color='#336c94',edgecolor='white');ax.set_xlabel('Flames ignited per summary day');ax.set_ylabel('Number of summary days');ax.set_title('Distribution of day-level ignition counts (n=18)');ax.grid(axis='y',alpha=.2);fig.tight_layout();save(fig,out/'02_day_count_distribution.png')
    # Source values preserved; fuel whitespace normalized ONLY for descriptive grouping in plot.
    fuel=table['Fuel Bottle'].str.replace(' ','',regex=False)
    groups=table.assign(fuel_group=fuel,flames=counts).groupby('fuel_group',sort=True).agg(days=('flames','size'),flames=('flames','sum'))
    fig,ax=plt.subplots(figsize=(8.5,4.8));bars=ax.bar(groups.index,groups.days,color='#52816d');ax.set_title('Recorded fuel-bottle categories across summary days');ax.set_ylabel('Summary days (not raw runs)');ax.set_xlabel('Fuel bottle text, whitespace harmonized for display');ax.grid(axis='y',alpha=.2)
    for b,n in zip(bars,groups.days):ax.text(b.get_x()+b.get_width()/2,b.get_height()+.1,str(n),ha='center')
    fig.tight_layout();save(fig,out/'03_fuel_categories.png')
    with args.raw.open(newline='',encoding='utf-8-sig') as f:
        reader=csv.reader(f);metadata=next(reader);header=next(reader)
        data=pd.DataFrame(reader,columns=header)
    assert 'Test Point: 19056A2' in metadata
    def seconds(s):
        hh,mm,ss,frac=s.split(':');return int(hh)*3600+int(mm)*60+int(ss)+int(frac)/(10**len(frac))
    t=np.array([seconds(s) for s in data['Time']]);elapsed=t-t[0];dt=np.diff(t)
    gaps=np.flatnonzero(dt>=1);backwards=np.flatnonzero(dt<0)
    selected=['IonCurrent','PMT1','MFCA3FuelFlow']
    fig,axes=plt.subplots(3,1,figsize=(11.5,7.5),sharex=True)
    for ax,col in zip(axes,selected):
        y=pd.to_numeric(data[col],errors='coerce')
        # Break at each major timestamp gap: no line or interpolation across missing time.
        starts=np.r_[0,gaps+1];ends=np.r_[gaps+1,len(elapsed)]
        for start,end in zip(starts,ends):
            ax.plot(elapsed[start:end],y.iloc[start:end],lw=.65,color='#336c94')
        ax.set_ylabel(col+'\n(raw units unspecified)',fontsize=9);ax.grid(alpha=.2)
        for i in gaps:ax.axvspan(elapsed[i],elapsed[i+1],color='#e4ad48',alpha=.25)
    axes[0].set_title('19056A2: selected raw channels (no calibration or physical interpretation)')
    axes[-1].set_xlabel('Elapsed seconds from first recorded timestamp (clock labels)')
    fig.tight_layout();save(fig,out/'04_run_raw_signals.png')
    stats=[]
    for col in selected:
        s=pd.to_numeric(data[col],errors='coerce')
        stats.append((col,int(s.count()),int(s.isna().sum()),float(s.min()),float(s.median()),float(s.max())))
    def rowlist():return '\n'.join(f'| {name} | {n:,} | {missing} | {mn:.6g} | {med:.6g} | {mx:.6g} |' for name,n,missing,mn,med,mx in stats)
    top=sorted(enumerate(counts),key=lambda v:-v[1])[:3]
    summary=f'''# PSI-20 BRE — General descriptive EDA\n\n## OBSERVED IN LOCAL FILES\n- Experimental summary: **{len(table)} day-level rows**, **{counts.sum()} flames ignited** in total, range **{counts.min()}–{counts.max()}** per day, median **{counts.median():g}** and mean **{counts.mean():.2f}**. Source: `{args.table.name}`, data rows 2–19 (CSV header is row 1).\n- Largest day-level counts: {', '.join(f'{labels[i]} ({int(n)}) [CSV row {i+2}]' for i,n in top)}. These are CSV dates, not independently corrected NASA operational dates.\n- Fuel labels (display-only whitespace grouping): {', '.join(f'{k}: {int(r.days)} days' for k,r in groups.iterrows())}. Source: CSV rows 2–19. This is descriptive grouping, not condition attribution to individual flames.\n- Oxygen concentration entries are lists of approximate conditions on each day, not per-flame settings. CSV row 6 contains `3400%`; row 9 contains `2100%`. Both are retained, excluded from any numeric oxygen analysis. Source: `{args.table.name}` rows 6 and 9; see Task 04C reconciliation.\n- Run `19056A2`: **{len(data):,} measurement rows**, {len(header)} channels including `Time`. Source: `{args.raw.name}`, CSV metadata row 1, header row 2, data rows 3–{len(data)+2}.\n- Raw time labels: **{len(gaps)} gaps >=1 s**, largest **{max(dt[gaps]) if len(gaps) else 0:.3f} s**; **{len(backwards)} negative time steps**. Source: raw `Time` column; gap interval from data rows {gaps[0]+3} to {gaps[0]+4} if present. Clock synchronization and timezone unverified.\n\n## Selected raw-channel statistics\n\n| Channel | Numeric samples | Missing/non-numeric | Min | Median | Max |\n|---|---:|---:|---:|---:|---:|\n{rowlist()}\n\nSource: `{args.raw.name}`, named columns, measurement data rows 3–{len(data)+2}. Values are raw channel values; physical units and calibration not established.\n\n## REPORTED BY NASA\nNASA ACME/BRE Final Report (2022) PDF pages **110 and 116** report **194 flames ignited**; pages **29 and 127** state **196 successful ignitions** (page 127 invokes Round 2). The apparent difference in definitions/scope remains unresolved. NASA report page **23** corrects Test Day 19094 to 4 April 2019.\n\n## OUR INFERENCE / limitations\nA day-level total of 194 is numerically consistent with the NASA 194 statements, but not proof of identical definitions. The one available raw-run pair does **not** establish NASA-wide run coverage. A raw signal trace shows variation and a recording gap, not flame stability, extinction, or causal relationships.\n\n## Source integrity\n- Experimental CSV SHA-256: `{hashes['table']}`\n- Raw CSV SHA-256: `{hashes['raw']}`\n- Original source files were read only; no values modified.\n'''
    (out/'eda_summary.md').write_text(summary,encoding='utf-8')
    (out/'findings.md').write_text('''# Presentation findings\n\n1. **OBSERVED IN LOCAL FILES:** 18 summary days contain 194 recorded flames ignited; day-level counts range from 0 to 21. Source: `PSI-20_Experimental table_ACME BRE.csv`, rows 2–19. See Charts 1–2.\n2. **OBSERVED IN LOCAL FILES:** The largest recorded day is CSV 2020-12-05 with 21 ignitions (CSV row 13); NASA Table 1 lists Test Day 20279 as 2020-10-05, also 21. This is a source-date discrepancy, not an authorized correction. Source: experimental CSV row 13; NASA Final Report PDF page 24; Task 04C cross-source report.\n3. **OBSERVED IN LOCAL FILES:** Fuel-bottle categories vary across summary days, but the summary table does not link individual flames to unique oxygen settings. Source: experimental CSV rows 2–19, `Fuel Bottle` and `Oxygen Conc (percent)` columns. See Chart 3.\n4. **OBSERVED IN LOCAL FILES:** Run `19056A2` has 31,316 raw samples and a 123.034-second timestamp gap. The plotted channels vary over time; raw units are unspecified. Source: `19056A2_data.csv`, metadata/header rows 1–2, `Time`, `IonCurrent`, `PMT1`, `MFCA3FuelFlow` columns. See Chart 4.\n5. **REPORTED BY NASA:** Final Report PDF pages 110 and 116 say 194 flames ignited, whereas pages 29 and 127 mention 196 successful ignitions. **OUR INFERENCE:** the discrepancy remains unresolved; the figures must not be treated as equivalent counts.\n''',encoding='utf-8')
    (out/'README.md').write_text('''# Reproduce PSI-20 BRE EDA\n\nPython 3.10+ with `numpy`, `pandas`, `matplotlib`. Run from the existing approved project root with the original source CSVs at their approved paths:\n\n```bash\npython eda/run_eda.py\n```\n\nOutputs: four PNG charts, `eda_summary.md`, `findings.md`. Input hashes are checked before analysis; original CSVs are never written. All dates on charts are original CSV dates, including known cross-source differences. No calibration, extinction classification, or inference of NASA-wide coverage.\n''',encoding='utf-8')
    print(f'PASS: {len(table)} summary days; {counts.sum()} flames; {len(data)} raw rows; {len(gaps)} gaps; {len(backwards)} negative intervals; {len(list(out.glob("*.png")))} charts')
if __name__=='__main__':main()
