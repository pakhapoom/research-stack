#!/usr/bin/env python3
"""Build a three-pass reading plan from a paper's extracted text.

Standard library only. Reads the text file produced by fetch_paper.py (`text_path`) and
prints, with 1-based line numbers usable as Read tool offsets:

  - the section outline, with each section's kind and opening sentence
  - figure/table captions
  - PASS 1 reading list: abstract, intro framing paragraph + contributions, conclusion
  - PASS 2 reading list: body sections in order (references/appendix skipped)

Usage:
  outline_paper.py <text_path> [--max-chunk LINES]
"""
from __future__ import annotations

import argparse
import re
import sys

MD_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
# Plain-text (pdftotext/pypdf) headings: "3 Method", "3.2. Training", "A.1 Proofs"
NUM_HEADING = re.compile(r"^\s*((?:\d{1,2}|[A-H])(?:\.\d+)*)\.?\s+([A-Z][^\n]{2,90})$")
WORD_HEADING = re.compile(
    r"^\s*(abstract|references|bibliography|acknowledge?ments?|"
    r"appendi(?:x|ces)(?:\s+[A-Z])?(?:[:.]?\s+[A-Z][\w ,:&\-]*)?|"
    r"conclusions?|discussion|limitations)\s*$",
    re.I,
)
CAPTION = re.compile(r"^(Figure|Fig\.|Table|Algorithm)\s+([A-Z]?\d+)\s*[:.]\s*(.*)", re.I)
CONTRIB = re.compile(
    r"\b(contributions?|we summarize|in summary|to summarize|our main|key advantages|"
    r"we make the following|this paper makes|specifically, we)\b",
    re.I,
)
ROADMAP = re.compile(
    r"\b(rest of (this|the) (paper|article|work)|organi[sz]ed as follows|paper is (structured|organi[sz]ed)|"
    r"in section \d+,? we)\b",
    re.I,
)
FRAMING = re.compile(r"\b(in this (paper|work)|we propose|we introduce|we present|here,? we)\b", re.I)

KINDS = [
    ("abstract", re.compile(r"^abstract$", re.I)),
    ("intro", re.compile(r"\bintroduction\b", re.I)),
    ("related", re.compile(r"\b(related work|prior work|literature review)", re.I)),
    ("setup", re.compile(r"\b(background|preliminar|problem (statement|setting|formulation)|notation)", re.I)),
    ("conclusion", re.compile(r"\b(conclusion|concluding|summary|future work|discussion)", re.I)),
    ("limitations", re.compile(r"\b(limitation|broader impact|ethic)", re.I)),
    ("references", re.compile(r"^(references|bibliography)$", re.I)),
    ("acknowledgments", re.compile(r"^acknowledge?ments?$", re.I)),
    ("appendix", re.compile(r"^(appendix|appendices|supplementary)", re.I)),
]
SKIP_KINDS = {"references", "appendix", "acknowledgments"}


def strip_num(title: str) -> str:
    return re.sub(r"^(appendix\s+)?([A-H]|\d+)(\.\d+)*\.?\s+", "", title, flags=re.I).strip()


def find_headings(lines: list[str]) -> list[dict]:
    heads = []
    # Markdown mode only for the arXiv HTML render. PDF text can contain stray lines that
    # start with "#" (e.g. table rows like "# of roles 100"), which are not headings.
    md_heads = [m for l in lines if (m := MD_HEADING.match(l)) and re.match(r"[A-Z0-9]", m.group(2))]
    md = len(md_heads) >= 3
    seen_refs = False
    for i, line in enumerate(lines, 1):
        if md:
            m = MD_HEADING.match(line)
            if m:
                heads.append({"line": i, "level": len(m.group(1)), "title": m.group(2)})
            continue
        s = line.strip()
        if not s or len(s) > 100 or s.endswith((".", ",", ";", ":")):
            continue
        if re.fullmatch(r"(references|bibliography)", s, re.I):
            seen_refs = True
        m = NUM_HEADING.match(s)
        if m and m.group(1)[0].isalpha() and not seen_refs:
            m = None  # letter-numbered headings ("A Proofs") only exist in appendices
        if m and not re.search(r"\d{3,}|[=<>±]", m.group(2)):
            heads.append({"line": i, "level": 2 + m.group(1).count("."), "title": s})
        elif WORD_HEADING.match(s):
            heads.append({"line": i, "level": 2, "title": s})
    return heads


def build_sections(lines: list[str], heads: list[dict]) -> list[dict]:
    n = len(lines)
    # The paper title is usually the only level-1 markdown heading; treat sections relative
    # to the shallowest level that has a numbered or known section.
    levels = [h["level"] for h in heads if h["level"] > 1 or len(heads) < 3]
    top = min(levels) if levels else 1
    after_refs = False
    for idx, h in enumerate(heads):
        end = n
        for nxt in heads[idx + 1:]:
            if nxt["level"] <= h["level"] or (h["level"] > top and nxt["level"] <= top):
                end = nxt["line"] - 1
                break
        h["end"] = end
        title = strip_num(h["title"])
        kind = "body"
        for k, rx in KINDS:
            if rx.search(title) or rx.search(h["title"]):
                kind = k
                break
        if kind == "references":
            after_refs = True
        elif after_refs and kind not in ("acknowledgments",):
            kind = "appendix"
        h["kind"] = kind
        h["top"] = h["level"] <= top
    first_abs = next((h["line"] for h in heads if h["kind"] == "abstract"), None)
    for h in heads:
        if h["level"] < top or (first_abs and h["line"] < first_abs):  # paper title / front matter
            h["kind"], h["top"] = "title", False
        # Abstract headings are often deeper (e.g. ######); treat them as top-level.
        if h["kind"] == "abstract":
            h["top"] = True
            nxt = next((x for x in heads if x["line"] > h["line"]), None)
            h["end"] = (nxt["line"] - 1) if nxt else n
    # Inherit skip kinds for subsections (e.g. D.1 under Appendix D).
    parent = None
    for h in heads:
        if h["top"]:
            parent = h
        elif parent and parent["kind"] in SKIP_KINDS:
            h["kind"] = parent["kind"]
    return heads


def paragraphs(lines: list[str], start: int, end: int) -> list[tuple[int, int, str]]:
    """Blank-line separated paragraphs in [start, end], skipping headings/captions/bullets."""
    out, cur, cur_start = [], [], None

    def flush(last):
        nonlocal cur, cur_start
        text = " ".join(cur).strip()
        if len(text) > 15:
            out.append((cur_start, last, text))
        cur, cur_start = [], None

    for i in range(start, end + 1):
        s = lines[i - 1].strip()
        if not s or MD_HEADING.match(s) or CAPTION.match(s):
            if cur:
                flush(i - 1)
            continue
        if s in {"•", "-", "–", "*"} or re.fullmatch(r"\d{1,2}", s) or s.startswith("|"):
            continue  # bullet markers / footnote numbers / table rows
        if cur_start is None:
            cur_start = i
        cur.append(s)
    if cur:
        flush(end)
    return out


def first_sentence(lines: list[str], h: dict, heads: list[dict], width: int = 150) -> str:
    stop = min([x["line"] - 1 for x in heads if x["line"] > h["line"]] + [h["end"], h["line"] + 60])
    for start, _, text in paragraphs(lines, h["line"] + 1, stop):
        sent = re.split(r"(?<=[.!?])\s+", text)[0]
        return sent if len(sent) <= width else sent[: width - 1] + "…"
    return ""


def intro_plan(lines: list[str], intro: dict, sections: list[dict]) -> dict:
    # Intro text ends at its first subsection (e.g. "Terminologies") or the next top section.
    sub = next((h for h in sections if h["line"] > intro["line"] and h["line"] <= intro["end"]), None)
    end = (sub["line"] - 1) if sub else intro["end"]
    paras = paragraphs(lines, intro["line"] + 1, end)
    if not paras:
        return {}
    ri = next((i for i, p in enumerate(paras) if ROADMAP.search(p[2])), None)
    roadmap = paras[ri] if ri is not None else None
    body = [p for i, p in enumerate(paras) if i != ri]
    ci = next((i for i, p in enumerate(body) if CONTRIB.search(p[2]) and i > 0), None)
    if ci is not None:
        framing = body[ci - 1]
        # A contribution list runs until the roadmap paragraph or the end of the intro.
        stop = roadmap[0] - 1 if roadmap and roadmap[0] > body[ci][0] else end
        contrib = (body[ci][0], stop)
    else:
        fi = max((i for i, p in enumerate(body) if FRAMING.search(p[2])), default=len(body) - 1)
        framing, contrib = body[fi], None
    return {
        "framing": (framing[0], framing[1]),
        "contrib": contrib,
        "roadmap": (roadmap[0], roadmap[1]) if roadmap else None,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("text_path")
    ap.add_argument("--max-chunk", type=int, default=250,
                    help="split pass-2 sections longer than this many lines into subsections")
    args = ap.parse_args()

    with open(args.text_path, encoding="utf-8", errors="replace") as f:
        lines = f.read().split("\n")
    heads = build_sections(lines, find_headings(lines))
    if len(heads) < 3:
        print(f"Could not detect section headings in {args.text_path} ({len(lines)} lines).")
        print("Fall back to: pass 1 = first ~120 lines + last body section; pass 2 = read in 250-line chunks.")
        return 1

    tops = [h for h in heads if h["top"]]
    print(f"OUTLINE of {args.text_path} ({len(lines)} lines)\n")
    for h in heads:
        if h["kind"] == "title":
            print(f"TITLE: {h['title']}\n")
            continue
        if h["kind"] in SKIP_KINDS and not h["top"]:
            continue
        indent = "" if h["top"] else "    "
        tag = f"[{h['kind']}]" if h["kind"] not in SKIP_KINDS else f"[skip:{h['kind']}]"
        print(f"{indent}{tag:<18} L{h['line']}-{h['end']}  {h['title']}")
        if h["kind"] not in SKIP_KINDS and h["kind"] != "abstract":
            fs = first_sentence(lines, h, heads)
            if fs:
                print(f"{indent}{'':<18}   ↳ {fs}")

    caps = [(i, m) for i, l in enumerate(lines, 1) if (m := CAPTION.match(l.strip()))]
    skip_from = min((h["line"] for h in tops if h["kind"] in SKIP_KINDS), default=len(lines) + 1)
    caps = [(i, m) for i, m in caps if i < skip_from]
    if caps:
        print("\nFIGURES AND TABLES (main text)")
        for i, m in caps:
            cap = m.group(3)
            print(f"  L{i:<6} {m.group(1)} {m.group(2)}: {cap[:110] + ('…' if len(cap) > 110 else '')}")

    # ---- reading plan
    abstract = next((h for h in heads if h["kind"] == "abstract"), None)
    intro = next((h for h in tops if h["kind"] == "intro"), None)
    concl = [h for h in tops if h["kind"] == "conclusion"]
    print("\nPASS 1 — OVERVIEW (read only these, plus this outline)")
    if abstract:
        print(f"  abstract              L{abstract['line']}-{abstract['end']}")
    else:
        print(f"  abstract              not detected: read L1-{min(len(lines), 80)} to find it")
    ip = intro_plan(lines, intro, heads) if intro else {}
    if ip:
        print(f"  intro framing ¶       L{ip['framing'][0]}-{ip['framing'][1]}")
        if ip["contrib"]:
            print(f"  contributions         L{ip['contrib'][0]}-{ip['contrib'][1]}")
        else:
            print("  contributions         no explicit list found; take claims from framing ¶ and abstract")
        if ip["roadmap"]:
            print(f"  paper roadmap ¶       L{ip['roadmap'][0]}-{ip['roadmap'][1]}")
    elif intro:
        print(f"  intro (tail)          L{max(intro['line'], intro['end'] - 40)}-{intro['end']}")
    if concl:
        c = concl[-1]
        print(f"  conclusion            L{c['line']}-{c['end']}")
    else:
        body_tops = [h for h in tops if h["kind"] not in SKIP_KINDS]
        if body_tops:
            c = body_tops[-1]
            print(f"  conclusion            not detected: read last body section L{c['line']}-{c['end']}")

    print("\nPASS 2 — UNDERSTAND (one chunk at a time, in order)")
    for h in tops:
        if h["kind"] in SKIP_KINDS or h["kind"] == "abstract":
            continue
        size = h["end"] - h["line"] + 1
        subs = [s for s in heads if not s["top"] and h["line"] < s["line"] <= h["end"]]
        note = {
            "related": "  (skim: positioning only)",
            "setup": "  (setup and notation: read carefully)",
            "intro": "  (full intro, now with pass-1 context)",
        }.get(h["kind"], "")
        if size > args.max_chunk and subs:
            print(f"  {h['title']}  L{h['line']}-{h['end']}  → in parts:")
            print(f"      (lead-in)  L{h['line']}-{subs[0]['line'] - 1}")
            for s in subs:
                if s["level"] == subs[0]["level"]:
                    print(f"      {s['title']}  L{s['line']}-{s['end']}")
        else:
            print(f"  {h['title']}  L{h['line']}-{h['end']}{note}")

    skipped = [h for h in tops if h["kind"] in SKIP_KINDS]
    if skipped:
        print("\nSKIPPED (open only to look up something the main text explicitly defers there)")
        for h in skipped:
            print(f"  [{h['kind']}] L{h['line']}-{h['end']}  {h['title']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
