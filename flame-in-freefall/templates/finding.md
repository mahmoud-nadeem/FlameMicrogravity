---
# Finding — copy to content/findings/<short-slug>.md (lowercase, dashes)
title: "The finding as a headline, with its number"
author: your-id
date: 2026-11-15
investigations: [PSI-00]
pillars: [prevention]          # prevention | detection | suppression
habitats: [moon-base]          # spacecraft | space-station | moon-base | pressurized-rover | mars-base | spacesuit | earth
claim: "One sentence a judge can check, with the number and its unit."
evidence:
  - kind: computation          # computation | table | figure | model | publication | psi-metadata
    ref: notebooks/your-notebook.ipynb   # repo path, URL or DOI
    note: "What in this source supports the claim"
confidence: medium             # high | medium | low
si_assisted: false             # true if an AI tool helped produce it (challenge rule: disclose)
---

## What we did
Data, filters and method in 2-4 sentences.

## What we found
The result: a small table or a figure (put images in content/findings/img/).

## Why it matters
The fire-safety meaning for the habitats above.

## Caveats
What could make this wrong.
