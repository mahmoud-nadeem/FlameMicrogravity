#!/usr/bin/env python3
"""T3 v2: SAME-R housekeeping (HKP) time series, 1 sample per second (PSI-101 Raw Data).

Run from the kit root:  python analysis/T3/PSI-101_same-r/scripts/hkp_time_series.py

Reads data/raw/PSI-101/Raw Data/*HKPData*.csv only (never changes them). For every test number
(= 'SAME #' of the results workbook) it finds the heater start (first row with HeatingInProgress = 1)
and measures, per channel, when the signal leaves its pre-heating baseline and when it peaks.

Response definition (stated in findings):
  baseline   = median of the channel from 60 s to 5 s before heater start
  noise      = 1.4826 x median absolute deviation over the same window
  threshold  = max(5 x noise, floor); floors: ISS scatter 0.02 V, ISS obscuration 0.01 V,
               ion A 0.02 V, ion B 0.05 V, DustTrak B 0.05 mg/m3, gas plume temperature 5 C
  response   = first time in [0, 900] s after heater start where |signal - baseline| > threshold
               for at least 5 consecutive samples
  peak       = time of the largest |signal - baseline| in [0, 900] s
Repeated header lines inside a file are skipped and rows with a repeated timestamp keep the first
occurrence; both are written to data_log.md between the hkp_time_series markers.
Outputs: tables/derived_hkp_test_events.csv, tables/derived_hkp_numbers.json,
         charts/iss_scatter_floor.png, charts/smoke_arrival_times.png
source_row = line number in the CSV file, header = line 1.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

KIT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(KIT))
from tools import kitlib as K  # noqa: E402

REC = Path(__file__).resolve().parents[1]
RAW = KIT / "data" / "raw" / "PSI-101" / "Raw Data"
WB_TABLE = REC / "tables" / "derived_same_results_flight_tests.csv"
CH = {
    "plume_temp_c": ("GasPlumeTemperature(DegC)", 5.0),
    "iss_obscuration_v": ("ISSDetectorObscurationMeasurement(Volts)", 0.01),
    "iss_scatter_v": ("ISSDetectorScatterMeasurement(Volts)", 0.02),
    "ion_a_v": ("IonDetectorAMeasurement(Volts)", 0.02),
    "ion_b_v": ("IonDetectorBMeasurement(Volts)", 0.05),
    "dustrak_b_mg_m3": ("DustTrakBMeasurement(MgPerM3)", 0.05),
}
SMOKE = ["iss_scatter_v", "ion_b_v", "dustrak_b_mg_m3"]
LABEL = {"iss_scatter_v": "ISS detector, scatter", "ion_b_v": "Ion detector B", "dustrak_b_mg_m3": "DustTrak B"}
DTA = "DustTrakAMeasurement(MgPerM3)"
K_SD, RUN, PRE, POST = 5.0, 5, (-60, -5), (0, 900)
BLUE, ORANGE = "#2a78d6", "#eb6834"
INK, MUTED, SURF = "#1f1f1e", "#6b6a64", "#fcfcfb"
LOG_START = "<!-- hkp_time_series: start (generated, do not edit between these markers) -->"
LOG_END = "<!-- hkp_time_series: end -->"
SCRIPT = "analysis/T3/PSI-101_same-r/scripts/hkp_time_series.py"


def rel(p: Path) -> str:
    return p.relative_to(KIT / "data" / "raw").as_posix()


def load_tests():
    """Yield (file, test number, frame sorted by time with t = seconds from heater start, log lines)."""
    for p in sorted(RAW.glob("*HKPData*.csv")):
        df, rows = K.read_source(p)
        df.insert(0, "source_row", rows)
        log = []
        inner = df[df.TimeString == "TimeString"]
        if len(inner):
            log.append(f"{rel(p)} | {K.compact_ranges(inner.source_row.tolist())} | all | repeated header line | "
                       f"(skipped) | second header inside the file | {SCRIPT} (load)")
        df = df[(df.TimeString != "TimeString") & (df.TimeString.str.strip() != "")].copy()
        num = ["Time", "TestNumber", "HeatingInProgress", DTA] + [c for c, _ in CH.values()]
        for c in num:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        for tn, g in df[df.TestNumber > 0].groupby("TestNumber"):
            g = g.sort_values(["Time", "source_row"])
            dup = g[g.Time.duplicated()]
            if len(dup):
                log.append(f"{rel(p)} | {K.compact_ranges(dup.source_row.tolist())} | Time | repeated timestamp "
                           f"(test {int(tn)}) | (row skipped, first kept) | one sample per second | {SCRIPT} (load)")
            g = g.drop_duplicates("Time")
            yield p, int(tn), g, log
            log = []


def events(g: pd.DataFrame) -> dict:
    h = g[g.HeatingInProgress == 1]
    if h.empty:
        return {"heating_found": False}
    t0 = h.Time.iloc[0]
    g = g.assign(t=g.Time - t0)
    rec = {"heating_found": True, "source_row": int(h.source_row.iloc[0]),
           "heating_s": float(h.Time.iloc[-1] - t0), "pre_samples": int(((g.t >= PRE[0]) & (g.t <= PRE[1])).sum())}
    pre = g[(g.t >= PRE[0]) & (g.t <= PRE[1])]
    post = g[(g.t >= POST[0]) & (g.t <= POST[1])]
    for k, (col, floor) in CH.items():
        base = float(pre[col].median())
        noise = float(1.4826 * np.median(np.abs(pre[col] - base)))
        thr = max(K_SD * noise, floor)
        dev = post[col] - base
        exc = (dev.abs() > thr).astype(int)
        run = exc.groupby((exc != exc.shift()).cumsum()).transform("sum") * exc
        hit = post[run >= RUN]
        i = dev.abs().idxmax()
        rec.update({f"{k}_baseline": round(base, 4), f"{k}_threshold": round(thr, 4),
                    f"{k}_response_s": float(hit.t.iloc[0]) if len(hit) else None,
                    f"{k}_response_row": int(hit.source_row.iloc[0]) if len(hit) else None,
                    f"{k}_peak_s": float(post.loc[i, "t"]), f"{k}_peak_row": int(post.loc[i, "source_row"]),
                    f"{k}_peak_dev": round(float(dev.loc[i]), 4)})
    s = g["ISSDetectorScatterMeasurement(Volts)"]
    rec["iss_scatter_min_v"] = round(float(s.min()), 4)
    rec["iss_scatter_min_row"] = int(g.loc[s.idxmin(), "source_row"])
    rec["iss_scatter_s_within_0_01v_of_min"] = int((s <= s.min() + 0.01).sum())
    rec["dustrak_a_values"] = " ".join(str(int(v)) for v in sorted(g[DTA].dropna().unique())[:6])
    return rec


def style(ax, title, xlabel):
    ax.set_title(title, loc="left", fontsize=11, color=INK, pad=10)
    ax.set_xlabel(xlabel, color=MUTED, fontsize=9)
    ax.tick_params(colors=MUTED, labelsize=9, length=0)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.spines["bottom"].set_color("#d9d8d2")
    ax.grid(axis="x", color="#ecebe6", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.set_facecolor(SURF)


def main() -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rows, logs, traces = [], [], {}
    dta_all = []
    for p, tn, g, log in load_tests():
        logs += log
        rec = {"source_file": rel(p), "test_number": tn, **events(g)}
        rec.setdefault("source_row", int(g.source_row.iloc[0]))
        rows.append(rec)
        dta_all.append(g[DTA].dropna())
        if rec.get("heating_found"):
            h = g[g.HeatingInProgress == 1]
            traces[tn] = (g.Time - h.Time.iloc[0], g["ISSDetectorScatterMeasurement(Volts)"])
    ev = pd.DataFrame(rows)
    first = ["source_file", "source_row", "test_number"]
    ev = ev[first + [c for c in ev.columns if c not in first]]
    (REC / "tables").mkdir(exist_ok=True)
    ev.to_csv(REC / "tables" / "derived_hkp_test_events.csv", index=False, encoding="utf-8-sig")
    h = ev[ev.heating_found == True].copy()  # noqa: E712

    N = {"files": int(ev.source_file.nunique()), "tests": int(len(ev)), "tests_with_heating": int(len(h)),
         "tests_without_heating": ev.loc[ev.heating_found != True, ["source_file", "test_number"]].values.tolist(),  # noqa: E712
         "heating_s_range": [float(h.heating_s.min()), float(h.heating_s.max())],
         "plume_temp_response_s_range": [float(h.plume_temp_c_response_s.min()), float(h.plume_temp_c_response_s.max())],
         "definition": {"baseline_window_s": PRE, "k_sd": K_SD, "run_samples": RUN, "post_window_s": POST,
                        "floors": {k: f for k, (_, f) in CH.items()}}}

    # A. ISS scatter: raw channel goes negative with smoke; minima bunch at about -6.25 to -6.28 V
    pinned = h[h.iss_scatter_min_v <= -6.2]
    N["iss_scatter"] = {
        "baseline_median_v": round(float(h.iss_scatter_v_baseline.median()), 3),
        "tests_min_at_or_below_minus_6_2_v": int(len(pinned)), "of_tests": int(len(h)),
        "pinned_min_range_v": [round(float(pinned.iss_scatter_min_v.min()), 3), round(float(pinned.iss_scatter_min_v.max()), 3)],
        "pinned_seconds_within_0_01v_median": float(pinned.iss_scatter_s_within_0_01v_of_min.median()),
        "pinned_seconds_within_0_01v_range": [int(pinned.iss_scatter_s_within_0_01v_of_min.min()),
                                              int(pinned.iss_scatter_s_within_0_01v_of_min.max())],
        "pinned_tests": pinned.test_number.tolist()}
    wb = pd.read_csv(WB_TABLE, encoding="utf-8-sig", dtype={"same_no": str}) if WB_TABLE.exists() else None
    if wb is not None:
        w = wb[(wb.mission == "SAME-R") & (~wb.same_no.str.endswith("a"))].copy()
        w["test_number"] = pd.to_numeric(w.same_no, errors="coerce")
        j = h.merge(w[["test_number", "iss_scatter_v", "source_row"]].rename(columns={"source_row": "workbook_row"}),
                    on="test_number", how="inner")
        j["sum"] = j.iss_scatter_v + j.iss_scatter_min_v
        N["iss_scatter"]["workbook_match"] = {
            "tests_matched": int(len(j)), "max_abs_workbook_plus_hkp_min_v": round(float(j["sum"].abs().max()), 3),
            "spearman": round(float(j[["iss_scatter_v", "iss_scatter_min_v"]].corr(method="spearman").iloc[0, 1]), 3)}

    # B. smoke arrival: ISS scatter, ion B, DustTrak B
    s = h.dropna(subset=[f"{k}_response_s" for k in SMOKE]).copy()
    t = s[[f"{k}_response_s" for k in SMOKE]]
    t.columns = SMOKE
    s["first_channel"] = t.idxmin(axis=1)
    s["after_heating_end_s"] = t.min(axis=1) - s.heating_s
    N["smoke_arrival"] = {
        "tests_all_three_responded": int(len(s)), "of_tests": int(len(h)),
        "median_response_s": {k: float(t[k].median()) for k in SMOKE},
        "response_s_range": {k: [float(t[k].min()), float(t[k].max())] for k in SMOKE},
        "first_response_after_heating_end_tests": int((s.after_heating_end_s > 0).sum()),
        "first_response_after_heating_end_median_s": float(s.after_heating_end_s.median()),
        "first_response_after_heating_end_iqr_s": [float(x) for x in s.after_heating_end_s.quantile([0.25, 0.75])],
        "first_channel_counts": {k: int(v) for k, v in s.first_channel.value_counts().items()},
        "median_spread_between_three_s": float((t.max(axis=1) - t.min(axis=1)).median()),
    }
    rob = []
    for k_sd, fm, run in [(3, 1, 5), (5, 1, 5), (8, 1, 5), (5, 2, 5), (5, 0.5, 3), (10, 3, 10)]:
        firsts = {}
        for p, tn, g, _ in load_tests():
            hh = g[g.HeatingInProgress == 1]
            if hh.empty:
                continue
            gg = g.assign(t=g.Time - hh.Time.iloc[0])
            pre = gg[(gg.t >= PRE[0]) & (gg.t <= PRE[1])]
            post = gg[(gg.t >= POST[0]) & (gg.t <= POST[1])]
            r = {}
            for k in SMOKE:
                col, floor = CH[k]
                base = pre[col].median()
                thr = max(k_sd * 1.4826 * np.median(np.abs(pre[col] - base)), floor * fm)
                exc = ((post[col] - base).abs() > thr).astype(int)
                rl = exc.groupby((exc != exc.shift()).cumsum()).transform("sum") * exc
                hit = post[rl >= run]
                r[k] = hit.t.iloc[0] if len(hit) else np.nan
            if all(pd.notna(v) for v in r.values()):
                firsts[tn] = min(r, key=r.get)
        c = pd.Series(firsts).value_counts()
        rob.append({"k_sd": k_sd, "floor_factor": fm, "run": run, "tests": int(len(firsts)),
                    "iss_scatter_first": int(c.get("iss_scatter_v", 0)), "dustrak_b_first": int(c.get("dustrak_b_mg_m3", 0)),
                    "ion_b_first": int(c.get("ion_b_v", 0))})
    N["smoke_arrival"]["robustness"] = rob

    # C. ISS obscuration channel barely moves while scatter swings by volts
    N["obscuration_vs_scatter"] = {
        "obscuration_baseline_median_v": round(float(h.iss_obscuration_v_baseline.median()), 3),
        "obscuration_peak_dev_median_v": round(float(h.iss_obscuration_v_peak_dev.median()), 3),
        "obscuration_peak_dev_range_v": [round(float(h.iss_obscuration_v_peak_dev.min()), 3), round(float(h.iss_obscuration_v_peak_dev.max()), 3)],
        "obscuration_responded_tests": int(h.iss_obscuration_v_response_s.notna().sum()),
        "scatter_peak_dev_median_v": round(float(h.iss_scatter_v_peak_dev.median()), 3),
        "scatter_responded_tests": int(h.iss_scatter_v_response_s.notna().sum())}

    # D. DustTrak A column holds codes, not mass concentrations
    a = pd.concat(dta_all)
    coded = a[(a == 0) | ((a >= 10000) & (a <= 20100))]
    N["dustrak_a_column"] = {"samples": int(len(a)), "zero_or_10000_to_20100": int(len(coded)),
                             "other_values": int(len(a) - len(coded)),
                             "nonzero_min": float(a[a > 0].min()) if (a > 0).any() else None,
                             "nonzero_max": float(a.max())}
    (REC / "tables" / "derived_hkp_numbers.json").write_text(json.dumps(N, indent=2, default=str) + "\n", encoding="utf-8")

    # data log (between own markers)
    dl = REC / "data_log.md"
    text = dl.read_text(encoding="utf-8")
    block = "\n".join([LOG_START, *logs, LOG_END])
    if LOG_START in text and LOG_END in text:
        head, rest = text.split(LOG_START, 1)
        text = head + block + rest.split(LOG_END, 1)[1]
    else:
        text = text.rstrip("\n") + "\n\n" + block + "\n"
    dl.write_text(text, encoding="utf-8")

    # charts
    plt.rcParams.update({"font.family": "DejaVu Sans", "figure.facecolor": SURF})
    fig, ax = plt.subplots(figsize=(7.2, 4.2), dpi=150)
    show = [x for x in N["iss_scatter"]["pinned_tests"] if x in (60, 64, 99, 103)]
    for i, tn in enumerate(show):
        tt, vv = traces[tn]
        m = (tt >= -60) & (tt <= 900)
        ax.plot(tt[m], vv[m], color=BLUE, linewidth=1.4, alpha=0.9, label="tests at the floor (60, 64, 99, 103)" if i == 0 else None)
    if 61 in traces:
        tt, vv = traces[61]
        m = (tt >= -60) & (tt <= 900)
        ax.plot(tt[m], vv[m], color=ORANGE, linewidth=1.6, label="test 61 (does not reach it)")
    ax.axvspan(0, float(np.median(h.heating_s)), color="#ecebe6", zorder=0)
    ax.text(3, -3.2, "heater on", fontsize=8, color=MUTED)
    ax.set_ylabel("raw scatter signal (V)", color=MUTED, fontsize=9)
    ax.legend(frameon=False, fontsize=8.5, loc="upper left", bbox_to_anchor=(0.30, 0.62))
    style(ax, f"ISS detector scatter signal stops at about -6.27 V in {N['iss_scatter']['tests_min_at_or_below_minus_6_2_v']} of "
              f"{N['iss_scatter']['of_tests']} tests", "seconds after heater start")
    ax.grid(axis="y", color="#ecebe6", linewidth=0.8)
    fig.text(0.01, 0.01, "SAME-R flight housekeeping data, 1 sample/s. Source: PSI-101 Raw Data HKPData files.",
             fontsize=7.5, color=MUTED)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(REC / "charts" / "iss_scatter_floor.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.2, 3.8), dpi=150)
    for i, k in enumerate(SMOKE):
        v = t[k].values
        y = i + (np.random.RandomState(i).rand(len(v)) - 0.5) * 0.3
        ax.scatter(v, y, s=26, color=BLUE, edgecolor=SURF, linewidth=1.0, zorder=3)
        med = float(np.median(v))
        ax.vlines(med, i - 0.3, i + 0.3, color=INK, linewidth=2, zorder=4)
        ax.text(med + 8, i + 0.32, f"median {med:.0f} s", fontsize=8.5, color=INK)
    ax.axvspan(0, float(np.median(h.heating_s)), color="#ecebe6", zorder=0)
    ax.text(3, -0.55, "heater on", fontsize=8, color=MUTED)
    ax.set_yticks(range(len(SMOKE)), [LABEL[k] for k in SMOKE])
    ax.set_xlim(-10, 400)
    ax.set_ylim(-0.7, len(SMOKE) - 0.3)
    style(ax, "Smoke reaches all three sensors about 2 minutes after the heater starts", "seconds after heater start")
    fig.text(0.01, 0.01, f"{len(s)} SAME-R flight tests; {int((t.max(axis=1) > 400).sum())} later responses beyond the axis. "
             "Source: PSI-101 Raw Data HKPData files.", fontsize=7.5, color=MUTED)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(REC / "charts" / "smoke_arrival_times.png")
    plt.close(fig)
    print(json.dumps({k: N[k] for k in ("tests", "tests_with_heating", "tests_without_heating", "heating_s_range",
                                         "plume_temp_response_s_range", "iss_scatter", "obscuration_vs_scatter",
                                         "dustrak_a_column")}, default=str))
    print(json.dumps(N["smoke_arrival"], default=str))
    print("log lines:", len(logs))


if __name__ == "__main__":
    main()
