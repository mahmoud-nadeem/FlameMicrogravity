#!/usr/bin/env python3
"""Check every contribution in content/ before it reaches the site.

Run it before you hand over your work:   python -m pipeline.validate
Exit code 0 = everything is valid; 1 = errors (each one names the file and the field).

Checks
  * every file matches its JSON Schema in schemas/
  * file and folder names match the ids inside them
  * every author is a member in content/members/
  * every investigation referenced exists (content/investigations/<ID>/)
  * every repo path given as evidence or artifact exists
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

from .common import CONTENT, PSI_ID, ROOT, SCHEMAS, load_markdown, load_yaml


def _validator(name: str) -> Draft202012Validator:
    return Draft202012Validator(json.loads((SCHEMAS / f"{name}.schema.json").read_text(encoding="utf-8")))


def _rel(p: Path) -> str:
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def _schema_errors(validator: Draft202012Validator, obj, where: Path) -> list[str]:
    errs = []
    for e in sorted(validator.iter_errors(obj), key=lambda e: list(e.path)):
        field = "/".join(str(x) for x in e.path) or "(top level)"
        errs.append(f"{_rel(where)}: {field}: {e.message}")
    return errs


def _is_repo_path(ref: str) -> bool:
    return not (ref.startswith("http://") or ref.startswith("https://") or ref.startswith("10.") or ref.startswith("doi:"))


def validate(content: Path = CONTENT) -> tuple[list[str], dict]:
    errors: list[str] = []
    counts = {"members": 0, "scenarios": 0, "investigations": 0, "cards": 0, "findings": 0, "models": 0}

    members = set()
    v = _validator("member")
    for p in sorted((content / "members").glob("*.yaml")):
        if p.name.startswith("_"):
            continue
        obj = load_yaml(p) or {}
        errors += _schema_errors(v, obj, p)
        if obj.get("id") != p.stem:
            errors.append(f"{_rel(p)}: id '{obj.get('id')}' must equal the file name '{p.stem}'")
        members.add(p.stem)
        counts["members"] += 1

    v = _validator("scenario")
    for p in sorted((content / "scenarios").glob("*.yaml")):
        obj = load_yaml(p) or {}
        errors += _schema_errors(v, obj, p)
        for key in ("o2_percent", "pressure_psi"):
            rng = obj.get(key) or [0, 0]
            if len(rng) == 2 and rng[0] > rng[1]:
                errors.append(f"{_rel(p)}: {key}: min {rng[0]} is larger than max {rng[1]}")
        counts["scenarios"] += 1

    investigations = set()
    v = _validator("investigation_card")
    for d in sorted((content / "investigations").glob("*")):
        if not d.is_dir() or d.name.startswith("_"):
            continue
        if not PSI_ID.match(d.name):
            errors.append(f"{_rel(d)}: folder must be named like PSI-69")
            continue
        investigations.add(d.name)
        counts["investigations"] += 1
        card = d / "card.yaml"
        if card.exists():
            obj = load_yaml(card) or {}
            errors += _schema_errors(v, obj, card)
            if obj.get("id") != d.name:
                errors.append(f"{_rel(card)}: id '{obj.get('id')}' must equal the folder name '{d.name}'")
            if obj.get("author") and obj["author"] not in members:
                errors.append(f"{_rel(card)}: author '{obj['author']}' is not in content/members/")
            for r in obj.get("reviewed_by") or []:
                if r not in members:
                    errors.append(f"{_rel(card)}: reviewed_by '{r}' is not in content/members/")
            for key in ("o2_percent", "pressure_atm", "flow_cm_s"):
                rng = (obj.get("conditions") or {}).get(key)
                if isinstance(rng, list) and len(rng) == 2 and rng[0] > rng[1]:
                    errors.append(f"{_rel(card)}: conditions/{key}: min {rng[0]} is larger than max {rng[1]}")
            counts["cards"] += 1
        elif not (d / "psi.json").exists():
            errors.append(f"{_rel(d)}: needs psi.json (run build_catalog) or card.yaml")

    v = _validator("finding")
    for p in sorted((content / "findings").glob("*.md")):
        if p.name.startswith("_"):
            continue
        try:
            meta, body = load_markdown(p)
        except Exception as e:  # noqa: BLE001 - report any parse problem to the contributor
            errors.append(f"{_rel(p)}: {e}")
            continue
        if hasattr(meta.get("date"), "isoformat"):
            meta["date"] = meta["date"].isoformat()  # YAML turns 2026-11-14 into a date object
        errors += _schema_errors(v, meta, p)
        if meta.get("author") and meta["author"] not in members:
            errors.append(f"{_rel(p)}: author '{meta['author']}' is not in content/members/")
        for inv in meta.get("investigations") or []:
            if inv not in investigations:
                errors.append(f"{_rel(p)}: investigation '{inv}' has no folder in content/investigations/")
        for ev in meta.get("evidence") or []:
            ref = str(ev.get("ref", ""))
            if ref and _is_repo_path(ref) and not (ROOT / ref).exists():
                errors.append(f"{_rel(p)}: evidence path '{ref}' does not exist in the repo")
        if len(body) < 200:
            errors.append(f"{_rel(p)}: body is too short ({len(body)} chars); explain method and caveats")
        counts["findings"] += 1

    v = _validator("model")
    for d in sorted((content / "models").glob("*")):
        if not d.is_dir() or d.name.startswith("_"):
            continue
        p = d / "model.yaml"
        if not p.exists():
            errors.append(f"{_rel(d)}: missing model.yaml")
            continue
        obj = load_yaml(p) or {}
        errors += _schema_errors(v, obj, p)
        if obj.get("id") != d.name:
            errors.append(f"{_rel(p)}: id '{obj.get('id')}' must equal the folder name '{d.name}'")
        if obj.get("author") and obj["author"] not in members:
            errors.append(f"{_rel(p)}: author '{obj['author']}' is not in content/members/")
        for inv in obj.get("investigations") or []:
            if inv not in investigations:
                errors.append(f"{_rel(p)}: investigation '{inv}' has no folder in content/investigations/")
        art = obj.get("artifact")
        if art and not (d / art).exists():
            errors.append(f"{_rel(p)}: artifact '{art}' not found in {_rel(d)}")
        counts["models"] += 1

    return errors, counts


def main() -> int:
    errors, counts = validate()
    summary = ", ".join(f"{v} {k}" for k, v in counts.items())
    if errors:
        print(f"FAILED: {len(errors)} problem(s)  [{summary}]")
        for e in errors:
            print("  - " + e)
        return 1
    print(f"OK  [{summary}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
