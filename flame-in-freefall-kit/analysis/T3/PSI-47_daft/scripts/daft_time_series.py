#!/usr/bin/env python3
"""DAFT (PSI-47) 1 s logs: P-Trak particle count vs DustTrak mass, per test.

Run from the kit root:  python analysis/T3/PSI-47_daft/scripts/daft_time_series.py

Reads only data/raw/PSI-47/Analyzed Data/PSI-47_Analyzed Data_DAFT Retrieved Data Summary.xls
(sheets 'Raw PTrak Data', 'Raw DustTrak Data', 'Headers', 'P-Trak vs. DustTrak Data') and
'PSI-47_Analyzed Data_flight data 063_TIMING.xls' (sheet 'TIMING'). Nothing is changed.
Raw sheets: 7 tests side by side as Date/Time/Data triplets (columns 3k..3k+2), 1 s logging,
Excel row 1 = header, so reading number k (1 = first second of the log) sits on Excel row k + 1.
Writes:
  tables/derived_daft_aligned.csv    one row per reading: source_file, sheet, source_row, test,
                                     instrument, seconds_after_own_log, seconds_on_ptrak_clock (test 2 only), value, unit
  tables/derived_daft_numbers.json   every number quoted in findings F-T3-20..22
  charts/daft_test02_velcro.png      (CAPTIONS.md)
Alignment of test 2: the TIMING sheet gives the video second at which each log was switched on
(row 7: P-Trak 1223 s, DustTrak 1176 s), so DustTrak reading k + 47 is matched with P-Trak reading k
(the 8 velcro events, rows 11-18, carry the same 47 s). Other events (HEPA, hose, log off) imply
53-72 s, so the result is also computed for every offset from 30 to 80 s. The instruments' own
clock times are not used for alignment (they disagree by about 51 minutes, see F-T3-20).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import xlrd
from scipy import stats

KIT = Path(__file__).resolve().parents[4]
REC = Path(__file__).resolve().parents[1]
AD = "PSI-47/Analyzed Data/"
SUMMARY = AD + "PSI-47_Analyzed Data_DAFT Retrieved Data Summary.xls"
TIMING = AD + "PSI-47_Analyzed Data_flight data 063_TIMING.xls"
BLUE, ORANGE, INK, MUTED, SURF = "#2a78d6", "#eb6834", "#1f1f1e", "#6b6a64", "#fcfcfb"


def book(rel):
    return xlrd.open_workbook(str(KIT / "data" / "raw" / rel))


def series(sheet, test):
    """Readings of one test: list of (excel_row, k, value). Empty cells end the series."""
    col = sheet.col_values(3 * (test - 1) + 2)
    out = []
    for r in range(1, sheet.nrows):
        v = col[r]
        if v == "" or v is None:
            break
        out.append((r + 1, r, float(v)))
    return out


def hms(dayfrac):
    s = round(float(dayfrac) * 86400)
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}", s


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    b = book(SUMMARY)
    P, D, H = b.sheet_by_name("Raw PTrak Data"), b.sheet_by_name("Raw DustTrak Data"), b.sheet_by_name("Headers")
    N = {"source_file": SUMMARY, "timing_file": TIMING, "tests": {}}
    rows = []
    for t in range(1, 8):
        p, d = series(P, t), series(D, t)
        # Headers: DustTrak start time row 5, P-Trak start time row 16 (column B = test 1 ... H = test 7, F blank)
        col = t if t <= 4 else t + 1
        d_start, d_s = hms(H.cell_value(4, col))
        p_start, p_s = hms(H.cell_value(15, col))
        pv, dv = np.array([x[2] for x in p]), np.array([x[2] for x in d])
        N["tests"][t] = {
            "series": "DAFT-1,2 (2005)" if t <= 4 else "DAFT-3 (2006)",
            "ptrak_readings": len(p), "ptrak_zero_share": round(float((pv == 0).mean()), 3), "ptrak_max_pt_cc": float(pv.max()),
            "ptrak_max_excel_row": int(p[int(pv.argmax())][0]),
            "dusttrak_readings": len(d), "dusttrak_zero_share": round(float((dv == 0).mean()), 3), "dusttrak_max_mg_m3": float(dv.max()),
            "headers_ptrak_start": p_start, "headers_dusttrak_start": d_start, "dusttrak_minus_ptrak_clock_s": d_s - p_s,
        }
        for inst, ser, sheet, unit in (("P-Trak", p, "Raw PTrak Data", "pt/cc"), ("DustTrak", d, "Raw DustTrak Data", "mg/m3")):
            for excel_row, k, v in ser:
                rows.append({"source_file": SUMMARY, "sheet": sheet, "source_row": excel_row, "test": t, "instrument": inst,
                             "seconds_after_own_log": k, "seconds_on_ptrak_clock": (k if inst == "P-Trak" else k - 47) if t == 2 else None,
                             "value": v, "unit": unit})
        N["tests"][t]["ptrak_second_highest_pt_cc"] = float(np.sort(pv)[-2])

    # video-based offset of test 2 from the TIMING sheet
    tm = book(TIMING).sheet_by_name("TIMING")
    ev = []
    for r in range(6, 22):
        name = str(tm.cell_value(r, 0)).strip()
        if name and tm.cell_value(r, 2) != "" and tm.cell_value(r, 4) != "":
            ev.append({"excel_row": r + 1, "event": name, "ptrak_s": float(tm.cell_value(r, 2)), "dusttrak_s": float(tm.cell_value(r, 4)),
                       "ptrak_video_s": float(tm.cell_value(r, 1)), "dusttrak_video_s": float(tm.cell_value(r, 3))})
    velcro = [e for e in ev if e["event"].startswith("velcro")]
    N["test2_timing"] = {"log_on_video_s": {"ptrak": ev[0]["ptrak_video_s"], "dusttrak": ev[0]["dusttrak_video_s"]},
                         "velcro_offsets_s": sorted({e["dusttrak_s"] - e["ptrak_s"] for e in velcro}),
                         "velcro_rows": [e["excel_row"] for e in velcro],
                         "velcro_windows_ptrak_s": [[velcro[i]["ptrak_s"], velcro[i + 1]["ptrak_s"]] for i in range(0, len(velcro), 2)]}

    df = pd.DataFrame(rows)
    (REC / "tables").mkdir(exist_ok=True)
    df.to_csv(REC / "tables" / "derived_daft_aligned.csv", index=False, encoding="utf-8-sig")

    # test 2 aligned comparison
    p2 = df[(df.test == 2) & (df.instrument == "P-Trak")].set_index("seconds_on_ptrak_clock").value
    d2 = df[(df.test == 2) & (df.instrument == "DustTrak")].set_index("seconds_on_ptrak_clock").value
    both = pd.concat([p2.rename("p"), d2.rename("d")], axis=1, join="inner")
    pos = both[(both.p > 0) & (both.d > 0)]
    r = stats.spearmanr(pos.p, pos.d)
    N["test2_aligned"] = {"overlap_s": int(len(both)), "both_positive": int(len(pos)), "spearman_rho": round(float(r.statistic), 3),
                          "p_value": round(float(r.pvalue), 3)}
    # sensitivity: the TIMING sheet's other events (HEPA, hose, log off) imply 50-72 s, so try every offset 30-80 s
    pk = df[(df.test == 2) & (df.instrument == "P-Trak")].set_index("seconds_after_own_log").value
    dk = df[(df.test == 2) & (df.instrument == "DustTrak")].set_index("seconds_after_own_log").value
    sens = {}
    for off in range(30, 81):
        j = pd.concat([pk.rename("p"), dk.rename("d").set_axis(dk.index - off)], axis=1, join="inner")
        j = j[(j.p > 0) & (j.d > 0)]
        sens[off] = round(float(stats.spearmanr(j.p, j.d).statistic), 3)
    N["test2_offset_sensitivity_30_80s"] = {"max_abs_rho": max(abs(v) for v in sens.values()), "rho_by_offset": sens}
    N["test2_other_event_offsets_s"] = sorted({e["dusttrak_s"] - e["ptrak_s"] for e in ev if not e["event"].startswith("velcro") and e["event"] != "Log on"})

    # NASA's own paired sheet for the 2006 bags (supplementary; alignment method not stated in the sheet)
    S = b.sheet_by_name("P-Trak vs. DustTrak Data")
    bags = {}
    for k in range(3):
        pp = np.array([x for x in S.col_values(2 * k)[2:] if x != ""], float)
        dd = np.array([x for x in S.col_values(2 * k + 1)[2:] if x != ""], float)
        m = (pp > 0) & (dd > 0)
        rr = stats.spearmanr(pp[m], dd[m])
        bags[f"bag{k + 1}"] = {"rows": int(len(pp)), "both_positive": int(m.sum()), "spearman_rho": round(float(rr.statistic), 3)}
    N["nasa_paired_bags_2006"] = bags
    N["nasa_paired_note_row3"] = str(S.cell_value(2, 7))
    (REC / "tables" / "derived_daft_numbers.json").write_text(json.dumps(N, indent=2) + "\n", encoding="utf-8")

    # chart: test 2, two panels on the P-Trak clock (no second y-axis)
    plt.rcParams.update({"font.family": "DejaVu Sans", "figure.facecolor": SURF})
    fig, axes = plt.subplots(2, 1, figsize=(7.4, 4.6), dpi=150, sharex=True)
    for ax, s, color, lab in ((axes[0], p2, BLUE, "P-Trak particle count (pt/cc)"), (axes[1], d2, ORANGE, "DustTrak mass (mg/m3)")):
        for a0, a1 in N["test2_timing"]["velcro_windows_ptrak_s"]:
            ax.axvspan(a0, a1, color="#ecebe6", zorder=0)
        ax.plot(s.index, s.values, color=color, linewidth=1.2, zorder=2)
        ax.set_ylabel(lab, color=MUTED, fontsize=8)
        ax.tick_params(colors=MUTED, labelsize=8, length=0)
        for sp in ("top", "right", "left"):
            ax.spines[sp].set_visible(False)
        ax.spines["bottom"].set_color("#d9d8d2")
        ax.grid(axis="y", color="#ecebe6", linewidth=0.8)
        ax.set_facecolor(SURF)
    axes[1].set_ylim(0, 1.0)
    axes[0].text(N["test2_timing"]["velcro_windows_ptrak_s"][0][0] + 3, p2.max() * 0.92, "shaded: velcro pulled apart", fontsize=7.5, color=MUTED)
    axes[1].set_xlabel("seconds after P-Trak log start (DustTrak shifted 47 s using the video timing)", color=MUTED, fontsize=8)
    axes[0].set_title("Velcro dust on the ISS: the particle counter jumped, the mass monitor stayed near zero",
                      loc="left", fontsize=10, color=INK, pad=8)
    fig.text(0.01, 0.01, "DAFT test 2, 4 Mar 2005. Source: PSI-47 DAFT Retrieved Data Summary.xls and flight data 063_TIMING.xls.",
             fontsize=7, color=MUTED)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    (REC / "charts").mkdir(exist_ok=True)
    fig.savefig(REC / "charts" / "daft_test02_velcro.png")
    plt.close(fig)
    print(json.dumps({"test2_aligned": N["test2_aligned"], "test2_timing": N["test2_timing"],
                      "bags": bags, "tests": {t: {k: v for k, v in x.items() if k in ("ptrak_zero_share", "ptrak_max_pt_cc", "ptrak_max_excel_row", "ptrak_second_highest_pt_cc", "dusttrak_zero_share", "dusttrak_max_mg_m3", "dusttrak_minus_ptrak_clock_s", "headers_ptrak_start", "headers_dusttrak_start")} for t, x in N["tests"].items()}}, indent=0))


if __name__ == "__main__":
    main()
