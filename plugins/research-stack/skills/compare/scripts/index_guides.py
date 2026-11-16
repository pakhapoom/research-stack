#!/usr/bin/env python3
"""Index the study guides in a directory so several papers can be worked on together.

Standard library only. Scans <dir>/*.md for guides written by the study skill (front
matter with a title and a `studied` or `content_basis` field) and prints, per guide:

  - metadata from the front matter (year, type, tags, datasets, metrics, depth, basis)
  - the TL;DR, shortened
  - each section's line range, usable as Read tool offsets

With --query, guides are ranked by how well they match the terms, and the output shows
which sections (and lines) mention each term, so only those ranges need to be read.

Usage:
  index_guides.py [DIR] [--query TERM[,TERM...]] [--top N]

DIR defaults to ./paper-notes. Terms are case-insensitive phrases separated by commas.
"""
from __future__ import annotations

import argparse
import os
import re
import sys

LIST_FIELDS = ("tags", "datasets", "metrics", "baselines")
META_FIELDS = ("title", "paper_type", "venue") + LIST_FIELDS


def parse_front_matter(text: str) -> tuple[dict, int]:
    """Return (fields, line number of the closing ---). Handles `key: value` and `key: [a, b]`."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return {}, 0
    fields: dict = {}
    for i, line in enumerate(lines[1:], 2):
        if line.strip() == "---":
            return fields, i
        m = re.match(r"^(\w+):\s*(.*)$", line)
        if not m:
            continue
        key, val = m.group(1), m.group(2).split("  #")[0].strip()
        if val.startswith("[") and val.endswith("]"):
            fields[key] = [v.strip().strip("\"'") for v in val[1:-1].split(",") if v.strip()]
        else:
            fields[key] = val.strip("\"'")
    return {}, 0


def load_guide(path: str) -> dict | None:
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            text = f.read()
    except OSError:
        return None
    fm, fm_end = parse_front_matter(text)
    if not fm.get("title") or not (fm.get("studied") or fm.get("content_basis")):
        return None
    lines = text.split("\n")
    sections = []
    fence = False
    for i, line in enumerate(lines, 1):
        if line.lstrip().startswith("```"):
            fence = not fence
        m = None if fence or i <= fm_end else re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            if sections:
                sections[-1]["end"] = i - 1
            sections.append({"title": m.group(1), "line": i, "end": len(lines)})
    tldr = ""
    for s in sections:
        if re.match(r"tl;?dr", s["title"], re.I):
            tldr = " ".join(" ".join(lines[s["line"]:s["end"]]).split())
            break
    for k in LIST_FIELDS:
        if not isinstance(fm.get(k), list):
            fm[k] = [fm[k]] if fm.get(k) else []
    return {"path": path, "name": os.path.basename(path)[:-3], "fm": fm, "lines": lines,
            "sections": sections, "tldr": tldr}


def match(guide: dict, terms: list[str]) -> dict:
    """Per term: metadata fields that contain it, and body hits grouped by section."""
    out = {}
    fm = guide["fm"]
    for term in terms:
        rx = re.compile(re.escape(term), re.I)
        meta = [k for k in META_FIELDS
                if rx.search(" | ".join(fm[k]) if isinstance(fm.get(k), list) else str(fm.get(k) or ""))]
        body = []
        for s in guide["sections"]:
            hit_lines = [i for i in range(s["line"], s["end"] + 1) if rx.search(guide["lines"][i - 1])]
            if hit_lines:
                body.append((s["title"], hit_lines))
        if meta or body:
            out[term] = {"meta": meta, "body": body}
    return out


def score(hits: dict) -> int:
    return sum(5 * len(h["meta"]) + min(sum(len(l) for _, l in h["body"]), 10) for h in hits.values())


def describe(g: dict) -> None:
    fm = g["fm"]
    print(f"{g['name']}  ({g['path']})")
    print(f"  title: {fm['title']}")
    bits = [str(fm.get("year") or "?"), fm.get("paper_type") or "?", f"depth {fm.get('depth') or '?'}",
            f"basis {fm.get('content_basis') or '?'}", f"studied {fm.get('studied') or '?'}"]
    if fm.get("purpose") and fm["purpose"] != "general":
        bits.append(f"for {fm['purpose']}")
    print(f"  {' · '.join(bits)}")
    for k in LIST_FIELDS:
        if fm[k]:
            print(f"  {k}: {', '.join(fm[k])}")
    if g["tldr"]:
        print(f"  TL;DR: {g['tldr'][:300] + ('…' if len(g['tldr']) > 300 else '')}")
    print("  sections: " + " · ".join(f"{s['title']} L{s['line']}-{s['end']}" for s in g["sections"]))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dir", nargs="?", default="paper-notes")
    ap.add_argument("--query", help="comma-separated terms to rank and locate (case-insensitive phrases)")
    ap.add_argument("--top", type=int, default=12, help="with --query, show at most this many guides in full")
    args = ap.parse_args()

    try:
        names = sorted(n for n in os.listdir(args.dir) if n.endswith(".md") and not n.endswith(".notes.md"))
    except OSError:
        print(f"No guide directory at {args.dir}.")
        return 1
    guides = [g for n in names if (g := load_guide(os.path.join(args.dir, n)))]
    print(f"GUIDE INDEX of {args.dir}: {len(guides)} study guide(s)\n")
    if not guides:
        return 1

    if args.query:
        terms = [t.strip() for t in args.query.split(",") if t.strip()]
        ranked = sorted(((score(h), g, h) for g in guides if (h := match(g, terms))),
                        key=lambda x: (-x[0], x[1]["name"]))
        print(f"QUERY: {', '.join(terms)}  → {len(ranked)} matching guide(s)\n")
        for sc, g, hits in ranked[:args.top]:
            describe(g)
            for term, h in hits.items():
                where = [f"front matter ({', '.join(h['meta'])})"] if h["meta"] else []
                where += [f"{title} L{','.join(map(str, ls[:4]))}{'…' if len(ls) > 4 else ''}"
                          for title, ls in h["body"]]
                print(f"  ▸ \"{term}\": {'; '.join(where)}")
            missing = [t for t in terms if t not in hits]
            if missing:
                print(f"  ▸ not mentioned: {', '.join(missing)}")
            print()
        if len(ranked) > args.top:
            print("ALSO MATCHING: " + ", ".join(g["name"] for _, g, _ in ranked[args.top:]) + "\n")
        matched = {g["name"] for _, g, _ in ranked}
        rest = [g["name"] for g in guides if g["name"] not in matched]
        if rest:
            print("NO MATCH: " + ", ".join(rest))
    else:
        for g in guides:
            describe(g)
            print()

    # What the library has in common: the natural axes for a comparison.
    shared = []
    for k in LIST_FIELDS:
        seen: dict[str, list[str]] = {}
        for g in guides:
            for v in g["fm"][k]:
                seen.setdefault(v.lower(), []).append(g["name"])
        shared += [(k, v, ns) for v, ns in seen.items() if len(ns) >= 2]
    if shared:
        print("\nSHARED ACROSS GUIDES (front matter values that two or more guides have)")
        for k, v, ns in sorted(shared, key=lambda x: (-len(x[2]), x[0], x[1])):
            print(f"  {k}: {v}  → {', '.join(ns)}")
    weak = [g["name"] for g in guides
            if g["fm"].get("depth") == "quick" or (g["fm"].get("content_basis") or "full-text") != "full-text"]
    if weak:
        print("\nWEAKER EVIDENCE (quick depth, or not based on the full text): " + ", ".join(weak))
    return 0


if __name__ == "__main__":
    sys.exit(main())
