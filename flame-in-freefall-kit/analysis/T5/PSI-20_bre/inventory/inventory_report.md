# PSI-20 BRE — local run inventory

## OBSERVED IN LOCAL FILES
- Recognized CSV files: 2
- Unrelated files (not inspected): 0
- Unique filename-derived candidate runs: 1
- Complete validated local pairs: 1
- Incomplete/conflicting run entries: 0
- Pairing issues: 0

## OUR INFERENCE
- A validated pair means filename Test Point and experiment calendar date agree, not that full measurements are valid.
- No unobserved runs are considered missing without an explicitly supplied expected-run manifest.
- Duplicates are unresolved, even when their content hashes match.

## REPORTED BY NASA
- None. No external NASA documentation was consulted or used to infer a complete run list.

## Unrelated files (relative paths)
- None

## Unresolved questions
- Is there an authoritative complete expected-run list and provenance?
- Are experiment date and Test Point sufficient to uniquely identify source exports?
- Are source CSVs complete beyond their metadata and header records?
- Clock synchronization, timezones, calibration and scientific outcomes are not assessed.

## Input manifest provenance
No expected-run manifest supplied.
