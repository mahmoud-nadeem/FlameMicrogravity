# How to hand over your work

Your work is handed over when your files sit in `content/` and this prints `OK`:

```bash
python -m pipeline.validate
```

The validator checks every field, author name, investigation ID and evidence path, and tells you the
exact file and field to fix. Every item you add shows on the site under your name.

## What you can add

| You add | Where | Start from |
| --- | --- | --- |
| Yourself (once) | `content/members/<your-id>.yaml` | `templates/member.yaml` |
| Investigation card | `content/investigations/<PSI-ID>/card.yaml` | `templates/card.yaml` |
| Finding | `content/findings/<short-slug>.md` | `templates/finding.md` |
| Mini-model | `content/models/<model-id>/model.yaml` (+ `predictions.json`) | `templates/model.yaml` |

## Steps

1. Claim your investigations in the team doc (one owner per PSI ID).
2. Copy the template and fill it from the PSI page, its experimental table and its documents.
   Never edit `psi.json`: it is regenerated from NASA's API.
3. Run `python -m pipeline.validate` until it prints `OK`.
4. Push a branch and open a pull request. No Git? Zip your files and send them to the integrator.
5. The integrator runs `python -m pipeline.build`; the site redeploys with your work.

## Rules

- IDs are lowercase with dashes (`moon-base-gap`, `mahmoud`).
- Every number cites a source: a repo path, a PSI URL or a DOI.
- Images go in `content/findings/img/`, under 1 MB each.
- If an AI tool helped, set `si_assisted: true` (competition rule: SI use must be disclosed).
- Findings need a claim with a number, evidence and a confidence level.
- Models need a validation method, metrics **and** a trivial baseline to compare against.
