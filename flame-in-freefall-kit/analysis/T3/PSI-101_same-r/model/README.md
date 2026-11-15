# Model: PSI-101 SAME-R (with SAME flight rows of the same workbook)

A model result is OUR INFERENCE, never a NASA finding.

Question: how well can the number-mean smoke particle diameter of a flight test be estimated from material, flight (SAME or SAME-R), air flow, heater setting and aging time?
Data: PSI-101 results workbook, sheet 'Reduced Data with ISS Det'; 121 flight tests with a size result and all inputs (kept out: DBP rows and 3 Kapton runs without a P-Trak count, which have no size; 6 internally inconsistent size rows, F-T3-23).
Features: material (one-hot), mission (one-hot), inlet velocity (cm/s), Rt/R0, log(net aging time, s).
Target: log of 'M1/M0 (micro-m)--AMD'.
Split: 5 repeats of 5-fold GroupKFold; a test and its aged re-measurement (NN, NNa) are always in the same fold (78 groups), so the same smoke is never in train and test.
Baseline: median log diameter of the test's material in the training folds.
Metrics (mean +- sd over 25 folds, model/evaluation.json): baseline MAE 0.372 +- 0.089 in log units (typical error factor 1.45); ridge regression MAE 0.274 +- 0.027 (typical error factor 1.32).

Gate (Phase 5):
1. Clearly defined target: yes (log number-mean diameter).
2. Enough usable labelled rows: yes, 121 rows in 78 independent groups.
3. Trivial baseline exists and is beaten: yes on average (0.10 lower log error); fold-to-fold spread is about 0.03-0.09, so the gain is modest.
4. Held-out split by run family: yes (GroupKFold by test pair).

Limits: only the five flown materials (it cannot predict a new material); flight hardware of 2007/2010; diameters are moment-method estimates; Rt/R0 is set per material, so its coefficient mixes material and temperature. Use it to show how conditions shift size, not to predict real fires.
How to re-run: python analysis/T3/PSI-101_same-r/scripts/same_results_analysis.py
