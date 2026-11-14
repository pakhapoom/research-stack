#!/usr/bin/env python3
"""List numbers in a study guide that do not appear in the paper's text.

Standard library only. Ignores the YAML front matter, line references (L123),
section/table/figure/equation labels, years, and list numbering. A number that is
reported missing is either a transcription error to fix or a value derived by the
writer (ratios, differences) that the guide should label as derived.

Usage:
  verify_numbers.py <guide.md> <text_path>
Exit code: 0 if every number was found, 1 otherwise.
"""
from __future__ import annotations

import re
import sys

NUM = re.compile(r"(?<![\w.$\\])(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+\.\d+|\d{2,})(?![\w])")
LABEL = re.compile(
    r"(?:\bL|§|\b(?:Sec(?:tion)?|Table|Tab|Fig(?:ure)?|Eq(?:uation)?|Appendix|App|Alg(?:orithm)?|"
    r"Theorem|Lemma|Q|C)\.?\s*)\s*\d+(?:\.\d+)*(?:\s*[-–]\s*L?\d+)?",
    re.I,
)


def normalize(n: str) -> str:
    return n.replace(",", "")


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    guide = open(sys.argv[1], encoding="utf-8").read()
    paper = open(sys.argv[2], encoding="utf-8", errors="replace").read()

    # Blank out front matter but keep its lines, so reported line numbers match the file.
    guide = re.sub(r"\A---\n.*?\n---\n", lambda m: "\n" * m.group(0).count("\n"), guide, flags=re.S)
    guide = LABEL.sub(" ", guide)
    guide = re.sub(r"https?://\S+", " ", guide)
    guide = re.sub(r"^[ \t]*\d+\.[ \t]", " ", guide, flags=re.M)  # numbered lists

    paper_nums = {normalize(m) for m in NUM.findall(paper)}
    paper_flat = paper.replace(",", "")

    missing: dict[str, list[int]] = {}
    for lineno, line in enumerate(guide.split("\n"), 1):
        for m in NUM.findall(line):
            n = normalize(m)
            if re.fullmatch(r"(19|20)\d{2}", n):  # years
                continue
            if n in paper_nums or n in paper_flat:
                continue
            missing.setdefault(m, []).append(lineno)

    if not missing:
        print("All numbers in the guide appear in the paper text.")
        return 0
    print(f"{len(missing)} number(s) in the guide not found in the paper text:")
    for n, where in missing.items():
        print(f"  {n:<14} line(s) {', '.join(map(str, where[:5]))}")
    print("For each: fix it if it is a transcription error. Values you computed yourself "
          "(worked examples, ratios, differences) are expected here: recheck the arithmetic "
          "and make sure the guide presents them as derived, not as reported results.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
