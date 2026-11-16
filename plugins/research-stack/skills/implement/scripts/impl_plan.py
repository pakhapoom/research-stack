#!/usr/bin/env python3
"""Build a targeted reading plan for implementing a paper.

Standard library only. Reads the text file produced by fetch_paper.py (`text_path`) and
prints, with 1-based line numbers usable as Read tool offsets, only what code needs:

  - method and setup sections (read in full)
  - experiment sections, split into setup parts (read) and result parts (targets only)
  - algorithm / pseudocode boxes
  - appendix sections that hold implementation details (the study skill skips these)
  - stray hyperparameter mentions outside those ranges
  - code and data links
  - what can be skipped

Usage:
  impl_plan.py <text_path>
"""
from __future__ import annotations

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "study", "scripts"))
from outline_paper import CAPTION, SKIP_KINDS, build_sections, find_headings  # noqa: E402

EXPERIMENT = re.compile(
    r"\b(experiment|evaluation|results?|empirical|analys[ei]s|ablation|discussion|case stud|findings)", re.I)
SETUP = re.compile(
    r"\b(set-?up|settings?|implementation|details?|datasets?|data|baselines?|metrics?|training|"
    r"hyper-?param|protocol|configurations?|benchmarks?|architecture|pseudo-?code|algorithms?|"
    r"reproduc|compute|prompts?)", re.I)
DETAILS = [
    ("learning rate", re.compile(r"learning[- ]rate|\blr\b", re.I)),
    ("batch size", re.compile(r"batch[- ]size|mini-?batch", re.I)),
    ("optimizer", re.compile(r"\b(adamw?|sgd|rmsprop|adafactor|optimi[sz]er)\b", re.I)),
    ("schedule", re.compile(r"warm-?up|\bscheduler?\b|cosine (decay|anneal)|linear decay", re.I)),
    ("epochs/steps", re.compile(r"\bepochs?\b|training steps|\biterations\b", re.I)),
    ("regularization", re.compile(r"dropout|weight decay|label smoothing|gradient clip", re.I)),
    ("seed/init", re.compile(r"\b(random )?seeds?\b|initiali[sz]ed? (with|from|to|as)", re.I)),
    ("hardware", re.compile(r"\bGPUs?\b|\bTPUs?\b|GPU[- ]hours|\b[AV]100\b|\bH100\b")),
    ("model size", re.compile(r"hidden (size|dim)|attention heads|\b\d+ layers\b|embedding dim", re.I)),
    ("decoding", re.compile(r"temperature|top-?[pk]\b|beam (size|search)|max(imum)? (new )?tokens", re.I)),
    ("hyperparameter", re.compile(r"hyper-?parameters?", re.I)),
]
LINK = re.compile(
    r"(?:https?://)?(?:www\.)?(?:github\.com|gitlab\.com|huggingface\.co|zenodo\.org|bitbucket\.org)/[^\s)\]}>,;\"']+",
    re.I)
SKIM_KINDS = {"intro", "related", "conclusion", "limitations"}


def detail_hits(line: str) -> list[str]:
    return [name for name, rx in DETAILS if rx.search(line)]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("text_path")
    args = ap.parse_args()

    with open(args.text_path, encoding="utf-8", errors="replace") as f:
        lines = f.read().split("\n")
    n = len(lines)
    heads = build_sections(lines, find_headings(lines))
    hits = {i: h for i, l in enumerate(lines, 1) if (h := detail_hits(l))}
    read: list[tuple[int, int]] = []  # ranges the plan says to read

    def span_hits(a: int, b: int) -> list[str]:
        kinds: dict[str, int] = {}
        for i in range(a, b + 1):
            for k in hits.get(i, []):
                kinds[k] = kinds.get(k, 0) + 1
        return [k for k, _ in sorted(kinds.items(), key=lambda kv: -kv[1])]

    print(f"IMPLEMENTATION READING PLAN of {args.text_path} ({n} lines)\n")

    if len(heads) < 3:
        print("Could not detect section headings. Use the keyword hits below to find the method,")
        print("the experimental setup and the hyperparameters, and read around them.\n")
        tops = []
    else:
        tops = [h for h in heads if h["top"]]

    refs_start = min((h["line"] for h in tops if h["kind"] == "references"), default=n + 1)
    refs_end = max((h["end"] for h in tops if h["kind"] == "references"), default=0)

    def subs_of(h: dict) -> list[dict]:
        inner = [s for s in heads if not s["top"] and h["line"] < s["line"] <= h["end"]]
        return [s for s in inner if s["level"] == inner[0]["level"]] if inner else []

    # ---- method and setup
    # Very short "sections" are list items or wrapped lines misread as headings.
    method = [h for h in tops if h["kind"] in ("body", "setup") and not EXPERIMENT.search(h["title"])
              and h["end"] - h["line"] >= 12]
    if method:
        print("METHOD AND SETUP (read in full, in order: exact equations and definitions)")
        for h in method:
            print(f"  L{h['line']}-{h['end']}  {h['title']}")
            read.append((h["line"], h["end"]))

    # ---- experiments
    exps = [h for h in tops if h["kind"] == "body" and EXPERIMENT.search(h["title"])]
    if exps:
        print("\nEXPERIMENTS (read the setup parts; from result parts take only target numbers)")
        for h in exps:
            subs = subs_of(h)
            if not subs:
                print(f"  L{h['line']}-{h['end']}  {h['title']}  → skim for setup: {', '.join(span_hits(h['line'], h['end'])[:4]) or 'no keyword hits'}")
                continue
            print(f"  {h['title']}")
            for s in subs:
                kinds = span_hits(s["line"], s["end"])
                is_setup = bool(SETUP.search(s["title"])) or len(kinds) >= 3
                tag = "READ   " if is_setup else "targets"
                extra = f"  ({', '.join(kinds[:4])})" if kinds else ""
                print(f"    {tag} L{s['line']}-{s['end']}  {s['title']}{extra}")
                if is_setup:
                    read.append((s["line"], s["end"]))

    # ---- algorithms
    algos = [(i, m) for i, l in enumerate(lines, 1)
             if (m := CAPTION.match(l.strip())) and m.group(1).lower() == "algorithm"]
    if algos:
        print("\nALGORITHMS / PSEUDOCODE (read the box around each line, appendix included)")
        for i, m in algos:
            print(f"  L{i:<6} Algorithm {m.group(2)}: {m.group(3)[:100]}")

    # ---- appendix
    apps = [h for h in tops if h["kind"] == "appendix"]
    if apps:
        useful, rest = [], []
        for h in apps:
            kinds = span_hits(h["line"], h["end"])
            (useful if SETUP.search(h["title"]) or len(kinds) >= 3 else rest).append((h, kinds))
        if useful:
            print("\nAPPENDIX WITH IMPLEMENTATION DETAILS (the study skill does not read these)")
            for h, kinds in useful:
                extra = f"  ({', '.join(kinds[:5])})" if kinds else ""
                print(f"  L{h['line']}-{h['end']}  {h['title']}{extra}")
                if h["end"] - h["line"] > 200:
                    first = [i for i in range(h["line"], h["end"] + 1) if i in hits]
                    if first:
                        print(f"      long section: keyword lines between L{first[0]} and L{first[-1]}; read around those")
                read.append((h["line"], h["end"]))
        if rest:
            print("\nOTHER APPENDIX SECTIONS (open only if the spec has a gap they could fill)")
            for h, _ in rest:
                print(f"  L{h['line']}-{h['end']}  {h['title']}")

    # ---- stray detail mentions
    def covered(i: int) -> bool:
        return any(a <= i <= b for a, b in read) or refs_start <= i <= refs_end

    stray = sorted(i for i in hits if not covered(i))
    clusters: list[list[int]] = []
    for i in stray:
        if clusters and i - clusters[-1][-1] <= 6:
            clusters[-1].append(i)
        else:
            clusters.append([i])
    clusters = [c for c in clusters if len({k for i in c for k in hits[i]}) >= 2 or len(c) >= 2]
    if clusters:
        print("\nDETAIL MENTIONS ELSEWHERE (hyperparameter keywords outside the ranges above)")
        for c in clusters[:25]:
            kinds = sorted({k for i in c for k in hits[i]})
            print(f"  L{c[0]}-{c[-1]}  {', '.join(kinds)}")
        if len(clusters) > 25:
            print(f"  … {len(clusters) - 25} more")

    # ---- links
    links: dict[str, int] = {}
    for i, l in enumerate(lines, 1):
        if refs_start <= i <= refs_end:
            continue
        for m in LINK.finditer(l):
            links.setdefault(m.group(0).rstrip("."), i)
    if links:
        print("\nCODE AND DATA LINKS (outside the reference list)")
        for url, i in list(links.items())[:15]:
            print(f"  L{i:<6} {url}")

    # ---- result tables
    tables = [(i, m) for i, l in enumerate(lines, 1)
              if i < refs_start and (m := CAPTION.match(l.strip())) and m.group(1).lower() == "table"]
    if tables:
        print("\nRESULT TABLES IN THE MAIN TEXT (targets to reproduce; read only the ones you will check against)")
        for i, m in tables:
            print(f"  L{i:<6} Table {m.group(2)}: {m.group(3)[:100]}")

    # ---- skip
    skip = [h for h in tops if h["kind"] in SKIM_KINDS or h["kind"] in ("references", "acknowledgments")]
    if skip:
        print("\nSKIP (not needed for code; the abstract is enough for orientation)")
        for h in skip:
            print(f"  L{h['line']}-{h['end']}  {h['title']}")

    total = sum(b - a + 1 for a, b in read)
    if tops:
        print(f"\nPlanned reading: about {total} of {n} lines ({round(100 * total / max(n, 1))}%).")
    return 0 if tops else 1


if __name__ == "__main__":
    sys.exit(main())
