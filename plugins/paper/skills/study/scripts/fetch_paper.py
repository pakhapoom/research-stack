#!/usr/bin/env python3
"""Resolve a paper reference (URL, ID, DOI, or local PDF) and fetch it locally.

Standard library only. Prints a JSON report to stdout describing what was found:

  {
    "source_type": "arxiv" | "openreview" | "acl" | "doi" | "semanticscholar" | "pdf" | "web" | "local",
    "id": "...", "title": "...", "authors": [...], "year": ..., "venue": "...",
    "abstract": "...", "landing_url": "...", "pdf_url": "...", "html_url": "...",
    "pdf_path": "/abs/path/paper.pdf" | null,
    "text_path": "/abs/path/paper.txt" | null,
    "notes": ["..."]
  }

Usage:
  fetch_paper.py <url-or-id-or-path> [--work-root DIR | --out DIR] [--no-download]

Files go to <work-root>/<slug>/ (default ./paper-notes/.work/<slug>/). The work root
gets a .gitignore so downloaded papers are never committed by accident.

Everything fetched is treated as untrusted data: it is saved to disk and never executed.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

USER_AGENT = "research-stack-paper/0.1 (Claude Code plugin; +https://github.com/pakhapoom/research-stack)"
TIMEOUT = 30
MAX_BYTES = 100 * 1024 * 1024  # 100 MB

ARXIV_NEW = r"\d{4}\.\d{4,5}(?:v\d+)?"
ARXIV_OLD = r"[a-z\-]+(?:\.[A-Z]{2})?/\d{7}(?:v\d+)?"
ARXIV_ID = rf"(?:{ARXIV_NEW}|{ARXIV_OLD})"
DOI_RE = r"10\.\d{4,9}/[^\s\"<>]+"


# ---------------------------------------------------------------- http helpers

def _request(url: str, method: str = "GET", accept: str | None = None):
    headers = {"User-Agent": USER_AGENT}
    if accept:
        headers["Accept"] = accept
    req = urllib.request.Request(url, headers=headers, method=method)
    return urllib.request.urlopen(req, timeout=TIMEOUT)


def get_text(url: str, accept: str | None = None) -> str | None:
    try:
        with _request(url, accept=accept) as r:
            data = r.read(MAX_BYTES)
            charset = r.headers.get_content_charset() or "utf-8"
            return data.decode(charset, errors="replace")
    except (urllib.error.URLError, TimeoutError, ValueError):
        return None


def get_json(url: str):
    txt = get_text(url, accept="application/json")
    if not txt:
        return None
    try:
        return json.loads(txt)
    except json.JSONDecodeError:
        return None


def url_ok(url: str) -> bool:
    try:
        with _request(url, method="HEAD") as r:
            return 200 <= r.status < 400
    except (urllib.error.URLError, TimeoutError, ValueError):
        return False


def download(url: str, dest: str) -> tuple[bool, str | None]:
    """Download url to dest. Returns (is_pdf, final_content_type)."""
    with _request(url) as r:
        ctype = (r.headers.get("Content-Type") or "").lower()
        total = 0
        with open(dest, "wb") as f:
            while True:
                chunk = r.read(1 << 16)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_BYTES:
                    raise ValueError("file exceeds 100 MB limit")
                f.write(chunk)
    with open(dest, "rb") as f:
        is_pdf = f.read(5) == b"%PDF-"
    return is_pdf, ctype


# ---------------------------------------------------------------- resolvers

def blank(source_type: str, ref: str) -> dict:
    return {
        "source_type": source_type, "id": None, "title": None, "authors": [],
        "year": None, "venue": None, "abstract": None, "landing_url": None,
        "pdf_url": None, "html_url": None, "pdf_path": None, "text_path": None,
        "input": ref, "notes": [],
    }


def resolve_arxiv(arxiv_id: str, ref: str) -> dict:
    info = blank("arxiv", ref)
    info["id"] = arxiv_id
    info["landing_url"] = f"https://arxiv.org/abs/{arxiv_id}"
    info["pdf_url"] = f"https://arxiv.org/pdf/{arxiv_id}"
    info["venue"] = "arXiv"
    xml_txt = get_text(f"https://export.arxiv.org/api/query?id_list={urllib.parse.quote(arxiv_id)}")
    if xml_txt:
        try:
            ns = {"a": "http://www.w3.org/2005/Atom"}
            entry = ET.fromstring(xml_txt).find("a:entry", ns)
            if entry is not None:
                t = entry.findtext("a:title", default="", namespaces=ns)
                s = entry.findtext("a:summary", default="", namespaces=ns)
                p = entry.findtext("a:published", default="", namespaces=ns)
                info["title"] = " ".join(t.split()) or None
                info["abstract"] = " ".join(s.split()) or None
                info["year"] = int(p[:4]) if p[:4].isdigit() else None
                info["authors"] = [
                    a.findtext("a:name", default="", namespaces=ns)
                    for a in entry.findall("a:author", ns)
                ]
        except ET.ParseError:
            info["notes"].append("arXiv API returned unparseable XML; metadata missing.")
    html_url = f"https://arxiv.org/html/{arxiv_id}"
    if url_ok(html_url):
        info["html_url"] = html_url
        info["notes"].append("arXiv HTML render available: best source for clean text and equations.")
    return info


def resolve_semantic_scholar(paper_key: str, ref: str, source_type: str) -> dict:
    """paper_key is e.g. 'DOI:10.x/y', 'ARXIV:2401.1', or a 40-char S2 id."""
    fields = "title,authors,year,abstract,venue,openAccessPdf,externalIds,url"
    data = get_json(
        f"https://api.semanticscholar.org/graph/v1/paper/{urllib.parse.quote(paper_key, safe=':')}?fields={fields}"
    )
    info = blank(source_type, ref)
    info["id"] = paper_key
    if not data or "title" not in data:
        info["notes"].append("Semantic Scholar lookup failed (rate limit or unknown paper).")
        return info
    ext = data.get("externalIds") or {}
    if ext.get("ArXiv"):
        arx = resolve_arxiv(ext["ArXiv"], ref)
        arx["source_type"] = source_type
        arx["venue"] = data.get("venue") or arx["venue"]
        arx["notes"].insert(0, f"Resolved to arXiv:{ext['ArXiv']} via Semantic Scholar.")
        if ext.get("DOI"):
            arx["doi"] = ext["DOI"]
        return arx
    info.update({
        "title": data.get("title"),
        "authors": [a.get("name") for a in data.get("authors") or []],
        "year": data.get("year"),
        "venue": data.get("venue"),
        "abstract": data.get("abstract"),
        "landing_url": data.get("url"),
        "pdf_url": (data.get("openAccessPdf") or {}).get("url") or None,
    })
    if ext.get("DOI"):
        info["doi"] = ext["DOI"]
        info["landing_url"] = f"https://doi.org/{ext['DOI']}"
    if not info["pdf_url"]:
        info["notes"].append("No open-access PDF known; the paper may be paywalled.")
    return info


def resolve_doi(doi: str, ref: str) -> dict:
    doi = doi.rstrip(".,;)")
    m = re.match(r"10\.48550/arxiv\.(.+)", doi, re.I)
    if m:
        return resolve_arxiv(m.group(1), ref)
    info = resolve_semantic_scholar(f"DOI:{doi}", ref, "doi")
    if not info.get("title"):
        cr = get_json(f"https://api.crossref.org/works/{urllib.parse.quote(doi)}")
        msg = (cr or {}).get("message") or {}
        if msg:
            info["title"] = (msg.get("title") or [None])[0]
            info["authors"] = [
                " ".join(filter(None, [a.get("given"), a.get("family")]))
                for a in msg.get("author") or []
            ]
            parts = ((msg.get("issued") or {}).get("date-parts") or [[None]])[0]
            info["year"] = parts[0] if parts else None
            info["venue"] = (msg.get("container-title") or [None])[0]
            if msg.get("abstract"):
                info["abstract"] = re.sub(r"<[^>]+>", "", msg["abstract"]).strip()
            info["notes"].append("Metadata from Crossref.")
    info["landing_url"] = info.get("landing_url") or f"https://doi.org/{doi}"
    info["doi"] = doi
    return info


_ATTR_RE = re.compile(r'([a-zA-Z_:-]+)\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|([^\s>]+))')


def find_meta(page_html: str, name: str) -> list[str]:
    """Return content values of <meta name=NAME content=...> in any attribute order/quoting.

    Highwire `citation_*` tags are used by most publishers, arXiv, PMLR, NeurIPS, ACL, ACM, ...
    """
    out = []
    for tag in re.findall(r"<meta\b[^>]*>", page_html, re.I):
        attrs = {m.group(1).lower(): html.unescape(m.group(2) or m.group(3) or m.group(4) or "")
                 for m in _ATTR_RE.finditer(tag)}
        if attrs.get("name", "").lower() == name.lower() and "content" in attrs:
            out.append(attrs["content"].strip())
    return out


def find_meta_pdf(page_html: str, base_url: str) -> str | None:
    urls = find_meta(page_html, "citation_pdf_url")
    return urllib.parse.urljoin(base_url, urls[0]) if urls else None


def resolve_web(url: str, ref: str) -> dict:
    info = blank("web", ref)
    info["landing_url"] = url
    page = get_text(url, accept="text/html,application/pdf;q=0.9,*/*;q=0.8")
    if page is None:
        info["notes"].append("Could not fetch the URL; try WebFetch or ask the user for a PDF.")
        return info
    if page.startswith("%PDF-"):
        info["source_type"] = "pdf"
        info["pdf_url"] = url
        return info
    # A DOI or arXiv id on the page lets us use a richer resolver.
    arx = find_meta(page, "citation_arxiv_id")
    if arx:
        return resolve_arxiv(arx[0], ref)
    info["pdf_url"] = find_meta_pdf(page, url)
    titles = find_meta(page, "citation_title")
    info["title"] = titles[0] if titles else None
    info["authors"] = find_meta(page, "citation_author")
    dates = find_meta(page, "citation_publication_date") or find_meta(page, "citation_date")
    if dates and dates[0][:4].isdigit():
        info["year"] = int(dates[0][:4])
    venues = find_meta(page, "citation_conference_title") or find_meta(page, "citation_journal_title")
    info["venue"] = venues[0] if venues else None
    dois = find_meta(page, "citation_doi")
    if dois:
        info["doi"] = dois[0]
    if not info["pdf_url"]:
        info["notes"].append("No PDF link found on the page; read the landing page with WebFetch instead.")
    return info


def resolve(ref: str) -> dict:
    ref = ref.strip().strip("<>")

    # Local file
    path = os.path.expanduser(ref)
    if os.path.isfile(path):
        info = blank("local", ref)
        info["pdf_path"] = os.path.abspath(path)
        return info

    # Bare arXiv id ("2401.12345", "arXiv:2401.12345")
    m = re.fullmatch(rf"(?:arxiv:)?({ARXIV_ID})", ref, re.I)
    if m:
        return resolve_arxiv(m.group(1), ref)

    # Bare DOI
    m = re.fullmatch(rf"(?:doi:)?({DOI_RE})", ref, re.I)
    if m:
        return resolve_doi(m.group(1), ref)

    if not re.match(r"https?://", ref, re.I):
        ref_url = "https://" + ref
    else:
        ref_url = ref
    parsed = urllib.parse.urlparse(ref_url)
    host = parsed.netloc.lower().removeprefix("www.")

    if host.endswith("arxiv.org") or host in {"alphaxiv.org", "huggingface.co"}:
        m = re.search(rf"({ARXIV_ID})", parsed.path)
        if m and (host != "huggingface.co" or parsed.path.startswith("/papers/")):
            return resolve_arxiv(re.sub(r"\.pdf$", "", m.group(1)), ref)

    if host == "openreview.net":
        q = urllib.parse.parse_qs(parsed.query)
        oid = (q.get("id") or [None])[0]
        if oid:
            info = blank("openreview", ref)
            info["id"] = oid
            info["landing_url"] = f"https://openreview.net/forum?id={oid}"
            info["pdf_url"] = f"https://openreview.net/pdf?id={oid}"
            note = get_json(f"https://api2.openreview.net/notes?id={urllib.parse.quote(oid)}")
            notes = (note or {}).get("notes") or []
            if notes:
                c = notes[0].get("content") or {}
                val = lambda k: (c.get(k) or {}).get("value") if isinstance(c.get(k), dict) else c.get(k)
                info["title"] = val("title")
                info["authors"] = val("authors") or []
                info["abstract"] = val("abstract")
                info["venue"] = val("venue")
            info["notes"].append("OpenReview forum may contain reviews and author rebuttals worth reading.")
            return info

    if host == "aclanthology.org":
        slug = parsed.path.strip("/").removesuffix(".pdf")
        if slug:
            info = resolve_web(f"https://aclanthology.org/{slug}/", ref)
            info["source_type"] = "acl"
            info["id"] = slug
            info["pdf_url"] = info["pdf_url"] or f"https://aclanthology.org/{slug}.pdf"
            return info

    if host in {"doi.org", "dx.doi.org"}:
        m = re.search(DOI_RE, urllib.parse.unquote(parsed.path))
        if m:
            return resolve_doi(m.group(0), ref)

    if host.endswith("semanticscholar.org"):
        m = re.search(r"([0-9a-f]{40})", parsed.path)
        if m:
            return resolve_semantic_scholar(m.group(1), ref, "semanticscholar")

    if parsed.path.lower().endswith(".pdf"):
        info = blank("pdf", ref)
        info["pdf_url"] = ref_url
        return info

    return resolve_web(ref_url, ref)


# ---------------------------------------------------------------- extraction

from html.parser import HTMLParser


class _HtmlToText(HTMLParser):
    """Verbatim text from an arXiv (LaTeXML) HTML render. Math becomes $LaTeX$ from alttext."""

    SKIP = {"script", "style", "nav", "header", "footer", "button", "svg", "noscript"}
    BLOCK = {"p", "div", "section", "article", "li", "tr", "figcaption", "caption",
             "blockquote", "table", "ul", "ol", "dd", "dt", "br"}
    HEAD = {"h1": "#", "h2": "##", "h3": "###", "h4": "####", "h5": "#####", "h6": "######"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out: list[str] = []
        self.skip = 0
        self.math = 0
        self.cell = 0  # depth inside <td>/<th>
        self.row = 0   # depth inside <tr>: keep each table row on one line

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if self.skip or self.math:
            if tag in self.SKIP:
                self.skip += 1
            if tag == "math":
                self.math += 1
            return
        if tag in self.SKIP or "ltx_page_footer" in (a.get("class") or ""):
            self.skip += 1
        elif tag == "math":
            self.math += 1
            tex = (a.get("alttext") or "").strip()
            disp = a.get("display") == "block"
            self.out.append(f"\n$$ {tex} $$\n" if disp else f" ${tex}$ ")
        elif tag in self.HEAD:
            self.out.append(f"\n\n{self.HEAD[tag]} ")
        elif tag == "tr":
            self.row += 1
            self.out.append("\n")
        elif tag in ("td", "th"):
            self.cell += 1
            self.out.append(" | ")
        elif tag == "img" and a.get("alt"):
            self.out.append(f" [image: {a['alt']}] ")
        elif tag in self.BLOCK and not self.cell:
            self.out.append("\n")

    def handle_endtag(self, tag):
        if self.math:
            if tag == "math":
                self.math -= 1
            return
        if self.skip:
            if tag in self.SKIP:
                self.skip -= 1
            return
        if tag in ("td", "th"):
            self.cell = max(0, self.cell - 1)
        elif tag == "tr":
            self.row = max(0, self.row - 1)
            self.out.append(" |\n")
        elif (tag in self.HEAD or tag in self.BLOCK) and not self.cell:
            self.out.append("\n")

    def handle_data(self, data):
        if not self.skip and not self.math:
            self.out.append(data.replace("\n", " ") if self.row else data)

    def text(self) -> str:
        t = "".join(self.out)
        t = re.sub(r"[ \t ]+", " ", t)
        t = re.sub(r" *\n *", "\n", t)
        return re.sub(r"\n{3,}", "\n\n", t).strip()


def html_to_text(url: str, txt_path: str) -> bool:
    page = get_text(url)
    if not page:
        return False
    parser = _HtmlToText()
    parser.feed(page)
    text = parser.text()
    if len(text) < 2000:  # error page or stub
        return False
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"Source: {url}\n\n{text}\n")
    return True


def slugify(info: dict) -> str:
    base = info.get("id") or info.get("title") or info.get("input") or "paper"
    s = re.sub(r"[^A-Za-z0-9]+", "-", str(base)).strip("-").lower()
    return s[:80] or "paper"


def extract_text(pdf_path: str, txt_path: str) -> str | None:
    """Try pdftotext, then pypdf. Returns the tool used, or None."""
    if shutil.which("pdftotext"):
        r = subprocess.run(["pdftotext", "-layout", pdf_path, txt_path], capture_output=True)
        if r.returncode == 0 and os.path.getsize(txt_path) > 200:
            return "pdftotext"
    try:
        from pypdf import PdfReader  # type: ignore
        reader = PdfReader(pdf_path)
        with open(txt_path, "w", encoding="utf-8") as f:
            for i, page in enumerate(reader.pages, 1):
                f.write(f"\n\n===== page {i} =====\n\n")
                f.write(page.extract_text() or "")
        if os.path.getsize(txt_path) > 200:
            return "pypdf"
    except Exception:
        pass
    if os.path.exists(txt_path):
        os.remove(txt_path)
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ref", help="paper URL, arXiv id, DOI, or local PDF path")
    ap.add_argument("--work-root", default=os.path.join("paper-notes", ".work"),
                    help="parent of the per-paper work directory (default: ./paper-notes/.work)")
    ap.add_argument("--out", help="exact work directory to use instead of <work-root>/<slug>")
    ap.add_argument("--no-download", action="store_true", help="resolve metadata only")
    args = ap.parse_args()

    info = resolve(args.ref)
    out = os.path.abspath(args.out or os.path.join(args.work_root, slugify(info)))
    if not args.out and not args.no_download:
        os.makedirs(args.work_root, exist_ok=True)
        gi = os.path.join(args.work_root, ".gitignore")
        if not os.path.exists(gi):
            with open(gi, "w") as f:
                f.write("# research-stack paper plugin: working files (downloaded papers, extracted text, notes)\n*\n")
    info["work_dir"] = out

    if not args.no_download and info["html_url"]:
        os.makedirs(out, exist_ok=True)
        html_txt = os.path.join(out, "paper.html.txt")
        if html_to_text(info["html_url"], html_txt):
            info["text_path"] = os.path.abspath(html_txt)
            info["notes"].append(
                "text_path is verbatim text of the arXiv HTML render (math as $LaTeX$). "
                "Use it as the primary source; check figures in the PDF."
            )

    if not args.no_download and info["pdf_url"] and not info["pdf_path"]:
        os.makedirs(out, exist_ok=True)
        dest = os.path.join(out, "paper.pdf")
        try:
            is_pdf, ctype = download(info["pdf_url"], dest)
            if is_pdf:
                info["pdf_path"] = os.path.abspath(dest)
            else:
                os.remove(dest)
                info["notes"].append(
                    f"pdf_url did not return a PDF (Content-Type: {ctype or 'unknown'}); "
                    "it may be paywalled or behind a login."
                )
        except (urllib.error.URLError, TimeoutError, ValueError) as e:
            info["notes"].append(f"PDF download failed: {e}")
            if info["source_type"] == "openreview":
                info["notes"].append(
                    "OpenReview blocks automated downloads with a human-verification challenge. "
                    "Ask the user to download the PDF and give you the local path, or look for an "
                    "arXiv version of the same paper."
                )

    if info["pdf_path"] and not info["text_path"]:
        if info["source_type"] == "local":
            os.makedirs(out, exist_ok=True)
            txt_path = os.path.join(out, "paper.txt")
        else:
            txt_path = os.path.splitext(info["pdf_path"])[0] + ".txt"
        tool = extract_text(info["pdf_path"], txt_path)
        if tool:
            info["text_path"] = os.path.abspath(txt_path)
            info["notes"].append(f"Text extracted with {tool}; check figures/tables/equations against the PDF.")
        else:
            info["notes"].append(
                "No local PDF text extractor (pdftotext/pypdf). Read pdf_path directly with the Read tool. "
                "If Read cannot open it, tell the user that installing poppler (pdftotext) fixes this."
            )

    print(json.dumps(info, indent=2, ensure_ascii=False))
    return 0 if (info["pdf_path"] or info["html_url"] or info["landing_url"]) else 1


if __name__ == "__main__":
    sys.exit(main())
