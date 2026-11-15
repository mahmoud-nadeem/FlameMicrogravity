#!/usr/bin/env python3
"""T3 analysis of the SAME / SAME-R flight results workbook (PSI-101 Analyzed Data).

Run from the kit root:  python analysis/T3/PSI-101_same-r/scripts/same_results_analysis.py

Reads sheet "Reduced Data with ISS Det" (header on Excel row 2, one row per flight test,
SAME = 2007 flight, SAME-R = 2010 flight). Nothing is changed in the workbook. Writes:
  tables/derived_same_results_flight_tests.csv   one row per test, with source_file, sheet, source_row
  tables/derived_numbers.json                    every number quoted in findings.md
  charts/*.png                                   charts listed in charts/CAPTIONS.md
  model/evaluation.json                          model-gate numbers (model/README.md)
Diameter used: "M1/M0 (micro-m)--AMD" = first moment / zeroth moment = number-mean diameter.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

KIT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(KIT))
from tools import kitlib as K  # noqa: E402

REC = Path(__file__).resolve().parents[1]
WB = "PSI-101/Analyzed Data/PSI-101_Analyzed Data_SAME, SAME-R_Results.xlsx"
SHEET = "Reduced Data with ISS Det"
COLS = ["flight", "material", "same_no", "description", "vel_cm_s", "rt_r0", "net_aging_s", "iss_scatter_v",
        "sts_v", "sts_offset_v", "m0", "m1", "mpass3", "dtA_mpass", "dtA_cal", "dustrak_b_mg_m3", "mean_diam_um",
        "diam_avg_mass_um", "mpass32", "sigma_g", "dg_um", "ionB_moment", "sample_temp_c", "mass_loss_mg",
        "yield", "sts_delta"]
NUM = ["vel_cm_s", "rt_r0", "net_aging_s", "iss_scatter_v", "sts_v", "dustrak_b_mg_m3", "mean_diam_um",
       "diam_avg_mass_um", "sigma_g", "dg_um", "sample_temp_c", "mass_loss_mg"]
ORDER = ["Kapton", "Teflon", "Lampwick", "Pyrell", "Silicone"]
BLUE, ORANGE = "#2a78d6", "#eb6834"      # validated categorical slots 1-2 (dataviz reference palette)
INK, MUTED, SURF = "#1f1f1e", "#6b6a64", "#fcfcfb"
LOG_START = "<!-- same_results_analysis: start (generated, do not edit between these markers) -->"
LOG_END = "<!-- same_results_analysis: end -->"
SCRIPT = "analysis/T3/PSI-101_same-r/scripts/same_results_analysis.py"


def load() -> pd.DataFrame:
    src = K.find_source(KIT, WB)
    if src is None:
        raise SystemExit(f"missing {WB}: run python scripts/psi_fetch.py --datasets same")
    df, rows = K.read_source(src, header_row=2, sheet=SHEET)
    df = df.iloc[:, : len(COLS)].copy()
    df.columns = COLS
    df.insert(0, "source_row", rows)
    df.insert(0, "sheet", SHEET)
    df.insert(0, "source_file", WB)
    df = df[df.material.str.strip() != ""].copy()
    for c in NUM:
        df[c] = pd.to_numeric(df[c].str.strip(), errors="coerce")
    df["mission"] = df.flight.str.strip().map({"1": "SAME", "2": "SAME-R"})
    df["same_no"] = df.same_no.str.strip()
    df["aged_measurement"] = df.same_no.str.endswith("a")        # 'NNa' = same smoke measured again after aging
    df["parent_test"] = df.same_no.str.rstrip("a")
    df["has_size"] = df.mean_diam_um > 0                          # DBP rows carry 0 = no size result
    # For any size distribution the diameter of average mass (M3/M0)^(1/3) is >= the number mean M1/M0.
    # A row that breaks this has at least one wrong size column, so it is kept out of the size analyses.
    df["size_consistent"] = ~((df.diam_avg_mass_um > 0) & (df.diam_avg_mass_um < df.mean_diam_um * 0.999))
    return df


def style(ax, title, ylabel):
    ax.set_title(title, loc="left", fontsize=11, color=INK, pad=10)
    ax.set_ylabel(ylabel, color=MUTED, fontsize=9)
    ax.tick_params(colors=MUTED, labelsize=9, length=0)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color("#d9d8d2")
    ax.grid(axis="y", color="#ecebe6", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.set_facecolor(SURF)


def main() -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    df = load()
    (REC / "tables").mkdir(exist_ok=True)
    (REC / "charts").mkdir(exist_ok=True)
    (REC / "model").mkdir(exist_ok=True)
    df.to_csv(REC / "tables" / "derived_same_results_flight_tests.csv", index=False, encoding="utf-8-sig")
    N: dict = {"source_file": WB, "sheet": SHEET}
    v_all = df[df.has_size].copy()
    v = v_all[v_all.size_consistent].copy()          # size analyses use internally consistent rows only
    N["tests_in_sheet"] = int(len(df))
    N["tests_by_mission_material"] = {f"{m}|{t}": int(n) for (m, t), n in df.groupby(["mission", "material"]).size().items()}
    N["tests_with_size"] = int(len(v_all))
    N["dbp_rows_without_size"] = df[~df.has_size & (df.material == "DBP")].source_row.tolist()
    N["other_rows_without_size"] = df[~df.has_size & (df.material != "DBP")].source_row.tolist()   # no P-Trak count
    bad = v_all[~v_all.size_consistent]
    N["excluded_inconsistent_size_rows"] = bad.source_row.tolist()
    N["tests_with_consistent_size"] = int(len(v))
    # sensitivity: the aging result with the inconsistent rows kept
    pa = v_all[~v_all.aged_measurement].merge(v_all[v_all.aged_measurement], on=["mission", "parent_test"], suffixes=("", "_aged"))
    ga = pa.mean_diam_um_aged / pa.mean_diam_um
    N["aging_sensitivity_inconsistent_rows_kept"] = {"pairs": int(len(pa)), "grew": int((ga > 1).sum()),
                                                     "median_growth": round(float(ga.median()), 2)}

    # 1. aging: same smoke measured before (NN) and after aging (NNa)
    pairs = v[~v.aged_measurement].merge(v[v.aged_measurement], on=["mission", "parent_test"], suffixes=("", "_aged"))
    pairs["growth"] = pairs.mean_diam_um_aged / pairs.mean_diam_um
    w = stats.wilcoxon(pairs.mean_diam_um_aged, pairs.mean_diam_um)
    N["aging"] = {
        "pairs": int(len(pairs)), "grew": int((pairs.growth > 1).sum()),
        "median_growth": round(float(pairs.growth.median()), 2),
        "iqr_growth": [round(float(q), 2) for q in pairs.growth.quantile([0.25, 0.75])],
        "aged_net_aging_s_range": [round(float(pairs.net_aging_s_aged.min())), round(float(pairs.net_aging_s_aged.max()))],
        "wilcoxon_p": float(w.pvalue),
        "by_material": {m: {"pairs": int(len(g)), "median_growth": round(float(g.growth.median()), 2)}
                        for m, g in pairs.groupby("material")},
        "rows_unaged": pairs.source_row.tolist(), "rows_aged": pairs.source_row_aged.tolist(),
        "shrank_rows": pairs.loc[pairs.growth <= 1, ["source_row", "source_row_aged"]].values.tolist(),
    }

    # 2. flow: unaged SAME-R tests, <=2 cm/s vs 8 cm/s at the SAME heater setting (Rt/R0)
    u = v[(~v.aged_measurement) & (v.net_aging_s < 300) & (v.mission == "SAME-R")]
    flow = []
    for m, g in u.groupby("material"):
        low = g[g.vel_cm_s <= 2]
        for rt in sorted(low.rt_r0.unique()):
            lo = low[np.isclose(low.rt_r0, rt)]
            hi = g[(g.vel_cm_s >= 8) & np.isclose(g.rt_r0, rt)]
            if len(lo) and len(hi):
                flow.append({"material": m, "rt_r0": float(rt), "n_low": int(len(lo)), "median_low": round(float(lo.mean_diam_um.median()), 3),
                             "n_8": int(len(hi)), "median_8": round(float(hi.mean_diam_um.median()), 3),
                             "rows_low": lo.source_row.tolist(), "rows_8": hi.source_row.tolist()})
    N["flow_matched_heater"] = flow

    # 3. material at its baseline: SAME-R, unaged, 8 cm/s, lowest heater setting of that material
    b = u[u.vel_cm_s >= 8]
    b = b[np.isclose(b.rt_r0, b.groupby("material").rt_r0.transform("min"))]
    N["baseline_by_material"] = {m: {"n": int(len(g)), "median_um": round(float(g.mean_diam_um.median()), 3),
                                     "min_um": round(float(g.mean_diam_um.min()), 3), "max_um": round(float(g.mean_diam_um.max()), 3),
                                     "rt_r0": float(g.rt_r0.iloc[0]), "median_temp_c": round(float(g.sample_temp_c.median())),
                                     "rows": g.source_row.tolist()} for m, g in b.groupby("material")}

    # 4. heater temperature, Kapton (SAME-R unaged, 8 cm/s)
    k = u[(u.material == "Kapton") & (u.vel_cm_s >= 8)].dropna(subset=["sample_temp_c"])
    rho = stats.spearmanr(k.sample_temp_c, k.mean_diam_um)
    N["kapton_temperature"] = {"n": int(len(k)), "spearman_rho": round(float(rho.statistic), 2), "p": round(float(rho.pvalue), 4),
                               "low_temp_range_um": [round(float(x), 3) for x in k[k.rt_r0 <= 1.38].mean_diam_um.agg(["min", "max"])],
                               "high_temp_range_um": [round(float(x), 3) for x in k[k.rt_r0 >= 1.48].mean_diam_um.agg(["min", "max"])],
                               "rows": k.source_row.tolist()}
    others = {}
    for m, g in u[(u.material != "Kapton") & (u.vel_cm_s >= 8)].dropna(subset=["sample_temp_c"]).groupby("material"):
        r = stats.spearmanr(g.sample_temp_c, g.mean_diam_um)
        others[m] = {"n": int(len(g)), "rho": round(float(r.statistic), 2), "p": round(float(r.pvalue), 3)}
    N["other_materials_temperature"] = others

    # 5. SAME (2007) vs SAME-R (2010) at matching conditions: unaged, 8 cm/s, same material and Rt/R0
    cmp_ = []
    uu = v[(~v.aged_measurement) & (v.net_aging_s < 300) & (v.vel_cm_s >= 8)]
    for (m, rt), g in uu.groupby(["material", "rt_r0"]):
        s1, s2 = g[g.mission == "SAME"], g[g.mission == "SAME-R"]
        if len(s1) and len(s2):
            cmp_.append({"material": m, "rt_r0": float(rt), "SAME_um": s1.mean_diam_um.round(3).tolist(), "SAME_rows": s1.source_row.tolist(),
                         "SAME_R_median_um": round(float(s2.mean_diam_um.median()), 3), "SAME_R_n": int(len(s2)), "SAME_R_rows": s2.source_row.tolist()})
    N["same_vs_same_r"] = cmp_

    # 6. ISS smoke detector scatter channel: readings bunch at a ceiling
    iss = v_all.dropna(subset=["iss_scatter_v"])     # detector readings do not depend on the size columns
    N["iss_scatter"] = {"tests": int(len(iss)), "at_or_above_6_2_v": int((iss.iss_scatter_v >= 6.2).sum()),
                        "max_v": round(float(iss.iss_scatter_v.max()), 3),
                        "spearman_vs_dustrak_b": round(float(stats.spearmanr(iss.iss_scatter_v, iss.dustrak_b_mg_m3, nan_policy="omit").statistic), 2)}

    # 7. model gate: log mean diameter from material, mission, flow, heater setting, aging time
    from sklearn.linear_model import RidgeCV
    from sklearn.model_selection import GroupKFold
    m = v.dropna(subset=["vel_cm_s", "rt_r0", "net_aging_s"]).copy()
    m["y"] = np.log(m.mean_diam_um)
    m["log_aging"] = np.log(m.net_aging_s.clip(lower=1))
    X = pd.get_dummies(m[["material", "mission"]]).astype(float).join(m[["vel_cm_s", "rt_r0", "log_aging"]])
    groups = m.mission + "-" + m.parent_test            # a test and its aged re-measurement stay together
    base_err, model_err = [], []
    rng = np.random.RandomState(0)
    for _ in range(5):
        idx = rng.permutation(len(m))
        for tr, te in GroupKFold(n_splits=5).split(X.iloc[idx], m.y.iloc[idx], groups.iloc[idx]):
            tr, te = idx[tr], idx[te]
            med = m.iloc[tr].groupby("material").y.median()
            base = m.iloc[te].material.map(med).fillna(m.iloc[tr].y.median())
            base_err.append(float(np.mean(np.abs(base - m.y.iloc[te]))))
            r = RidgeCV(alphas=np.logspace(-3, 2, 20)).fit(X.iloc[tr], m.y.iloc[tr])
            model_err.append(float(np.mean(np.abs(r.predict(X.iloc[te]) - m.y.iloc[te]))))
    ev = {"rows": int(len(m)), "groups": int(groups.nunique()), "folds": "5 x GroupKFold(5), groups = test + its aged re-measurement",
          "baseline": "median log diameter of the material in the training folds",
          "baseline_mae_log": [round(float(np.mean(base_err)), 3), round(float(np.std(base_err)), 3)],
          "ridge_mae_log": [round(float(np.mean(model_err)), 3), round(float(np.std(model_err)), 3)],
          "baseline_typical_factor": round(float(np.exp(np.mean(base_err))), 2),
          "ridge_typical_factor": round(float(np.exp(np.mean(model_err))), 2),
          "features": list(X.columns)}
    full = RidgeCV(alphas=np.logspace(-3, 2, 20)).fit(X, m.y)
    ev["coefficients_full_fit"] = {c: round(float(x), 3) for c, x in zip(X.columns, full.coef_)}
    (REC / "model" / "evaluation.json").write_text(json.dumps(ev, indent=2) + "\n", encoding="utf-8")
    N["model_gate"] = ev
    (REC / "tables" / "derived_numbers.json").write_text(json.dumps(N, indent=2, default=str) + "\n", encoding="utf-8")

    # data log: rows kept out of the size analyses (between own markers)
    logs = [f"{WB} | {K.compact_ranges(N['dbp_rows_without_size'])} | M1/M0, Diameter of Average mass | 0 | (row kept out of size analyses) | "
            f"DBP rows carry zeros in every size column = no size result | {SCRIPT} (load: has_size)"]
    for _, r in df[~df.has_size & (df.material != "DBP")].iterrows():
        logs.append(f"{WB} | {r.source_row} | M1/M0, Diameter of Average mass | 0 ({r.mission} test {r.same_no}, {r.material}, "
                    f"description '{r.description.strip()}') | (row kept out of size analyses) | no P-Trak count (M0 empty or 0), "
                    f"so no size result | {SCRIPT} (load: has_size)")
    for _, r in bad.iterrows():
        logs.append(f"{WB} | {r.source_row} | M1/M0, Diameter of Average mass | {r.mean_diam_um:.4f}, {r.diam_avg_mass_um:.4f} um "
                    f"({r.mission} test {r.same_no}, {r.material}) | (row kept out of size analyses) | diameter of average mass below the "
                    f"number-mean diameter, impossible for any size distribution; no sigma_g in the row | {SCRIPT} (load: size_consistent)")
    dl = REC / "data_log.md"
    text = dl.read_text(encoding="utf-8")
    block = "\n".join([LOG_START, *logs, LOG_END])
    if LOG_START in text and LOG_END in text:
        head, rest = text.split(LOG_START, 1)
        text = head + block + rest.split(LOG_END, 1)[1]
    else:
        text = text.rstrip("\n") + "\n\n" + block + "\n"
    dl.write_text(text, encoding="utf-8")

    # ---- charts
    plt.rcParams.update({"font.family": "DejaVu Sans", "figure.facecolor": SURF})
    # A: growth after aging, per material
    fig, ax = plt.subplots(figsize=(7.2, 4.2), dpi=150)
    order = [x for x in ORDER if x in set(pairs.material)]
    for i, mat in enumerate(order):
        g = pairs[pairs.material == mat].growth.values
        xs = i + (np.random.RandomState(i).rand(len(g)) - 0.5) * 0.25
        ax.scatter(xs, g, s=34, color=BLUE, edgecolor=SURF, linewidth=1.2, zorder=3)
        ax.hlines(np.median(g), i - 0.25, i + 0.25, color=INK, linewidth=2, zorder=4)
        ax.text(i + 0.3, np.median(g), f"x{np.median(g):.2f}", va="center", fontsize=8.5, color=INK)
    ax.axhline(1, color=MUTED, linewidth=1, linestyle=(0, (3, 3)))
    ax.text(len(order) - 0.55, 1.02, "no change", fontsize=8, color=MUTED)
    ax.set_xticks(range(len(order)), order)
    style(ax, f"Smoke particles grew after aging in {N['aging']['grew']} of {N['aging']['pairs']} flight tests",
          "mean diameter after / before aging")
    fig.text(0.01, 0.01, "Each dot: one SAME or SAME-R flight test. Bar: median. Source: PSI-101 SAME, SAME-R Results workbook.",
             fontsize=7.5, color=MUTED)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(REC / "charts" / "aging_growth_by_material.png")
    plt.close(fig)

    # B: low flow vs 8 cm/s at matched heater setting
    fdf = pd.DataFrame(flow)
    fig, ax = plt.subplots(figsize=(7.2, 4.2), dpi=150)
    labels = [f"{r.material}\nRt/R0 {r.rt_r0:g}" for r in fdf.itertuples()]
    x = np.arange(len(fdf))
    ax.scatter(x - 0.12, fdf.median_8, s=48, color=BLUE, edgecolor=SURF, linewidth=1.2, zorder=3, label="8 cm/s air flow")
    ax.scatter(x + 0.12, fdf.median_low, s=48, color=ORANGE, edgecolor=SURF, linewidth=1.2, zorder=3, label="0-2 cm/s air flow")
    for i, r in enumerate(fdf.itertuples()):
        ax.plot([i - 0.12, i + 0.12], [r.median_8, r.median_low], color="#c9c8c0", linewidth=1.5, zorder=2)
        ax.text(i + 0.12, r.median_low, f"  n={r.n_low}", fontsize=7.5, color=MUTED, va="center")
        ax.text(i - 0.12, r.median_8, f"n={r.n_8}  ", fontsize=7.5, color=MUTED, va="center", ha="right")
    ax.set_xticks(x, labels, fontsize=8)
    ax.legend(frameon=False, fontsize=8.5, loc="upper left")
    style(ax, "Less air flow, larger smoke particles (3 of 5 materials, same heater setting)", "median mean diameter (µm)")
    fig.text(0.01, 0.01, "SAME-R flight tests before aging. Small groups: read as a pattern, not a law. Source: PSI-101 Results workbook.",
             fontsize=7.5, color=MUTED)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(REC / "charts" / "flow_vs_particle_size.png")
    plt.close(fig)

    # C: material at its own baseline
    fig, ax = plt.subplots(figsize=(7.2, 4.0), dpi=150)
    order = [x for x in ORDER if x in N["baseline_by_material"]]
    for i, mat in enumerate(order):
        g = b[b.material == mat].mean_diam_um.values
        ax.scatter(np.full(len(g), i), g, s=40, color=BLUE, edgecolor=SURF, linewidth=1.2, zorder=3)
        ax.text(i + 0.12, np.median(g), f"{np.median(g) * 1000:.0f} nm (n={len(g)})", fontsize=8.5, color=INK, va="center")
    ax.set_xticks(range(len(order)), order)
    ax.set_xlim(-0.5, len(order) - 0.2)
    style(ax, "Smoke particle size depends on the material (about 4x range)", "mean diameter (µm)")
    fig.text(0.01, 0.01, "SAME-R flight, fresh smoke, 8 cm/s, each material at its lowest heater setting. Source: PSI-101 Results workbook.",
             fontsize=7.5, color=MUTED)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(REC / "charts" / "particle_size_by_material.png")
    plt.close(fig)
    print(json.dumps({k: N[k] for k in ("aging", "flow_matched_heater", "baseline_by_material", "kapton_temperature",
                                         "other_materials_temperature", "same_vs_same_r", "iss_scatter")}, indent=1, default=str)[:6000])
    print("model:", ev["baseline_mae_log"], ev["ridge_mae_log"], ev["baseline_typical_factor"], ev["ridge_typical_factor"])


if __name__ == "__main__":
    main()
