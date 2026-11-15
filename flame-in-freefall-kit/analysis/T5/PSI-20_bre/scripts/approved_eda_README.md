# Reproduce PSI-20 BRE EDA

Python 3.10+ with `numpy`, `pandas`, `matplotlib`. Run from the existing approved project root with the original source CSVs at their approved paths:

```bash
python eda/run_eda.py
```

Outputs: four PNG charts, `eda_summary.md`, `findings.md`. Input hashes are checked before analysis; original CSVs are never written. All dates on charts are original CSV dates, including known cross-source differences. No calibration, extinction classification, or inference of NASA-wide coverage.
