---
title: "Only 20 PSI tests burned in a Moon-base-like atmosphere, and none of them burned a solid"
author: mahmoud
date: 2026-11-14
investigations: [PSI-159, PSI-10, PSI-69, PSI-25, PSI-20]
pillars: [prevention]
habitats: [moon-base, pressurized-rover, spacesuit]
claim: "Of 1,009 PSI tests with recorded oxygen and pressure, only 20 ran in an ambient atmosphere inside the expected Moon-base envelope (at least 30% O2, at most 10.2 psi), all of them gas flames, and no solid-material test exceeded 22.2% O2."
evidence:
  - kind: computation
    ref: pipeline/envelope.py
    note: "Run `python -m pipeline.envelope` after `python -m pipeline.build_catalog`; writes data/derived/scenario_coverage.json."
  - kind: psi-metadata
    ref: https://psi.nasa.gov/physci/repo/data/investigations/PSI-159
    note: "CFI-G normal- and inverse-flame experimental tables"
  - kind: psi-metadata
    ref: https://psi.nasa.gov/physci/repo/data/investigations/PSI-25
    note: "BASS-II experimental table: calibrated initial O2 13.6-22.2%"
confidence: medium
si_assisted: true
---

## What we did

We read the experimental tables of the six PSI tables that record both oxygen and pressure per test
(FLEX, CFI, CFI-G normal and inverse, ACME Flame Design normal and inverse): 1,021 tests, 1,009 with
both values. We placed each test on an oxygen-versus-pressure map and counted the tests inside the
habitat envelopes given in the challenge statement: Moon base and pressurized rover at 30% oxygen or
more and 10.2 psi or less, and spacesuits at 100% oxygen and 4.3 psi.

## What we found

| Group | Tests inside the Moon-base envelope |
| --- | --- |
| CFI-G normal flames (oxygen in the ambient atmosphere) | 20 (17 ignited a hot flame, 3 did not) |
| CFI-G inverse flames (oxygen blown from the burner) | 28 |
| Flame Design inverse flames (oxygen blown from the burner) | 18 |
| FLEX droplets | 0 inside; 17 just outside at 30-34% O2 and 10.3-10.5 psi (14 disrupted, 3 burned out, none extinguished) |
| Solid materials | 0: BASS-II never exceeded 22.2% initial O2; SAFFIRE ran near 21.5-22.1% |
| Spacesuit atmosphere | 0: the lowest pressure in any test is 0.42 atm (6.2 psi) |

Inverse flames are counted apart because their oxygen comes from the burner while the chamber holds
fuel, which is not how a cabin fire meets oxygen. The ACME Burning Rate Emulator (PSI-20) ran gas
burners that stand in for solids at 21-40% oxygen, but its table does not record pressure, so it cannot
be placed on the map yet.

## Why it matters

The expected Moon-base atmosphere makes materials more flammable than Earth air, and fabrics and
plastics are what burn in a habitat. PSI's microgravity data at those oxygen levels are gas flames and a
gas-fed emulator; real solid materials were only tested near 21-22% oxygen. Predictive models for
Moon-base material flammability therefore have to extrapolate from data outside the envelope, and new
solid-material tests at 30% oxygen or more and about 10 psi would close the largest gap.

## Caveats

- Counts use only values in the experimental tables. Tests with RAMP or LOW O2 entries, and FLEX test
  114 (pressure recorded as 0), are left out.
- BASS (PSI-26) records no oxygen in its table, and SAFFIRE values come from its short sample tables.
- PSI holds no partial-gravity data, so this map shows oxygen and pressure only.
