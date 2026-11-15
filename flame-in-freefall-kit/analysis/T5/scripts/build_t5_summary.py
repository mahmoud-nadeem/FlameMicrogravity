#!/usr/bin/env python3
"""Rebuild three descriptive charts from the NASA PSI source CSVs in the team kit.
PSI-20 EDA remains in its separately approved `scripts/run_eda.py`.
"""
from pathlib import Path
import csv, collections
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[3]
T5=ROOT/'analysis/T5'


def read(psi):
    paths=list((ROOT/'data/experimental_tables'/psi).rglob('*.csv'))
    assert len(paths)==1, (psi, paths)
    with paths[0].open(encoding='utf-8-sig',newline='') as f:
        return list(csv.DictReader(f))

def save(fig, name):
    fig.tight_layout()
    fig.savefig(name,dpi=170,bbox_inches='tight')
    plt.close(fig)

def main():
    p10=T5/'PSI-10_flame-design/charts/01_flame_design_entries.png'
    sources=list((ROOT/'data/experimental_tables/PSI-10').rglob('*.csv'))
    assert len(sources)==2
    counts=collections.Counter()
    for p in sources:
        with p.open(newline='',encoding='utf-8-sig') as f:
            counts.update(r['Flame Type'] for r in csv.DictReader(f))
    assert counts=={'Normal':207,'Inverse':120}
    fig,ax=plt.subplots(figsize=(7,4)); bars=ax.bar(['Normal','Inverse'],[207,120]); ax.bar_label(bars)
    ax.set_ylabel('Test-table entries (not ignition outcomes)');ax.set_title('PSI-10: documented experimental table entries')
    save(fig,p10)

    psi22=read('PSI-22')
    rows=[r for r in psi22 if r['Flames Ignited'].strip()]
    assert len(psi22)==32 and len(rows)==21
    vals=[int(r['Flames Ignited']) for r in rows]
    labels=[r['Test Day'] for r in rows]
    assert sum(vals)==230 and labels.count('18319')==2
    fig,ax=plt.subplots(figsize=(11,4.5));ax.bar(range(len(vals)),vals)
    ax.set_xticks(range(len(vals)),labels,rotation=75,fontsize=8)
    ax.set_ylabel('Flames ignited per CSV count-bearing row')
    ax.set_xlabel('Test Day (18319 appears twice in original source)')
    ax.set_title('PSI-22: recorded ignition counts — repeated day not deduplicated')
    ax.grid(axis='y',alpha=.2)
    save(fig,T5/'PSI-22_e-field/charts/01_e_field_source_rows.png')

    psi23=read('PSI-23')
    vals=[int(r['Flames Ignited*']) for r in psi23]
    labels=[r['Test Day*'] for r in psi23]
    assert len(vals)==18 and sum(vals)==276
    fig,ax=plt.subplots(figsize=(10,4.5));ax.bar(range(len(vals)),vals)
    ax.set_xticks(range(len(vals)),labels,rotation=75,fontsize=8)
    ax.set_ylabel('Flames ignited per summary day');ax.set_xlabel('Test Day (as recorded)')
    ax.set_title('PSI-23: recorded s-Flame day-level ignition counts')
    ax.grid(axis='y',alpha=.2)
    save(fig,T5/'PSI-23_s-flame/charts/01_s_flame_ignitions_by_day.png')
    print('PASS PSI-10 207+120=327; PSI-22 21 count-bearing rows, 20 unique days and source sum 230; PSI-23 18 rows sum 276. Three charts regenerated.')

if __name__=='__main__':main()
