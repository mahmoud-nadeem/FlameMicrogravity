# Independent T5 numerical verification — 2026-11-15

All counts below were recomputed from the untouched starter-kit CSVs using Python csv.DictReader:
- PSI-10: 327 entries (Normal 207; Inverse 120); Normal fuels {'C2H4': 187, 'C3H8': 20}.
- PSI-20: 18 days; sum 194; min 0; max 21; mean 10.78; median 10.0.
- PSI-22: 32 physical rows, 21 numeric count rows, 11 non-count continuation rows; sum over count rows 230; 20 distinct Test Day IDs; 18319 repeated source lines [(26, '11'), (30, '11')].
- PSI-23: 18 count-bearing days; sum 276; first round 152, second round 124.
- PSI-20 prior approved package source hashes from Task04C and Task05 matched historical Technical Lead review; new integrated package does not modify any original source files.
- Cards: archived DOI/title match local NASA PSI API metadata for all 4. NASA Science official overview independently cross-checked. Interactive PSI page version/file-listing/“Cite this Investigation” text not fully verified.
- Site manual browser click-through: NOT DONE by this file review.

- PSI-10 standardised `source_file` now has team-kit-relative path prefix; verified 327/327 paths resolve to actual source CSVs. No measured cell changed.
