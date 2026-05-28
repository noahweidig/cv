#!/usr/bin/env python3
"""Fetch Zotero pubs + website profile, render LaTeX CV."""
import re, sys, html, urllib.request, json, datetime, pathlib
import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined

ROOT = pathlib.Path(__file__).parent.parent
TPL  = ROOT / "template" / "cv.tex.j2"
OUT  = ROOT / "cv.tex"

ZOTERO_URL = (
    "https://api.zotero.org/users/11988712/publications/items"
    "?format=json&include=data,bibtex&limit=200"
)
ME_URL = (
    "https://raw.githubusercontent.com/noahweidig/"
    "noahweidig.github.io/main/data/authors/me.yaml"
)

TYPE_MAP = {
    "journalArticle": "journal",
    "thesis":         "thesis",
    "presentation":   "talk",
    "conferencePaper":"talk",
    "preprint":       "preprint",
    "magazineArticle":"media",
    "newspaperArticle":"media",
    "blogPost":       "media",
    "webpage":        "media",
    "report":         "report",
    "book":           "book",
    "bookSection":    "chapter",
}


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "cv-builder/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode()


def tex_esc(s: str) -> str:
    s = str(s)
    replacements = [
        ("\\", r"\textbackslash{}"),
        ("&",  r"\&"),
        ("%",  r"\%"),
        ("$",  r"\$"),
        ("#",  r"\#"),
        ("_",  r"\_"),
        ("{",  r"\{"),
        ("}",  r"\}"),
        ("~",  r"\textasciitilde{}"),
        ("^",  r"\textasciicircum{}"),
    ]
    for ch, rep in replacements:
        s = s.replace(ch, rep)
    return s


def strip_html(s: str) -> str:
    return re.sub(r"<[^>]+>", "", html.unescape(str(s))).strip()


def fmt_date(iso, fmt="%b %Y") -> str:
    if not iso:
        return ""
    try:
        return datetime.datetime.strptime(str(iso)[:10], "%Y-%m-%d").strftime(fmt)
    except Exception:
        return str(iso)[:7]


def extract_year(s) -> int:
    m = re.search(r"\b(19|20)\d{2}\b", str(s))
    return int(m.group()) if m else 0


def fmt_authors(creators: list, owner_family="weidig") -> str:
    parts = []
    for c in creators:
        if not c:
            continue
        if c.get("name"):
            words = c["name"].split()
            family = words[-1] if words else c["name"]
            given_init = "".join(w[0] + "." for w in words[:-1]) if len(words) > 1 else ""
            display = f"{family}, {given_init}" if given_init else family
        else:
            family = c.get("lastName", "")
            given  = c.get("firstName", "")
            given_init = "".join(p[0] + "." for p in given.split()) if given else ""
            display = f"{family}, {given_init}" if given_init else family

        is_owner = family.lower() == owner_family
        parts.append(
            f"\\textbf{{{tex_esc(display)}}}" if is_owner else tex_esc(display)
        )

    if len(parts) <= 7:
        return ", ".join(parts)
    return ", ".join(parts[:7]) + ", \\ldots{}"


def categorize(item: dict) -> str:
    itype = item["data"].get("itemType", "")
    haystack = " ".join([
        item["data"].get("title", ""),
        item["data"].get("event", ""),
        item["data"].get("genre", ""),
        item["data"].get("presentationType", ""),
    ]).lower()
    if "webinar" in haystack:
        return "webinar"
    if "referee report" in item["data"].get("title", "").lower():
        return "review"
    return TYPE_MAP.get(itype, "other")


def process_pubs(items: list) -> dict:
    cats = ["journal", "thesis", "talk", "preprint",
            "report", "chapter", "book", "media", "webinar", "review", "other"]
    pubs = {c: [] for c in cats}

    for it in items:
        if it["data"].get("itemType") == "attachment":
            continue
        d   = it["data"]
        cat = categorize(it)
        doi = d.get("DOI", "")
        url = d.get("url", "") or (f"https://doi.org/{doi}" if doi else "")

        pubs[cat].append({
            "title":   strip_html(d.get("title", "Untitled")),
            "authors": fmt_authors(d.get("creators", [])),
            "year":    extract_year(d.get("date", "")),
            "journal": (d.get("publicationTitle") or d.get("bookTitle")
                        or d.get("proceedingsTitle") or d.get("meetingName")
                        or d.get("event") or d.get("publisher") or ""),
            "volume":  d.get("volume", ""),
            "issue":   d.get("issue", ""),
            "pages":   d.get("pages", ""),
            "doi":     doi,
            "url":     url,
            "place":   d.get("place", ""),
        })

    for cat in pubs:
        pubs[cat].sort(key=lambda x: x["year"], reverse=True)

    return pubs


def main():
    print("Fetching profile ...", flush=True)
    me = yaml.safe_load(fetch(ME_URL))

    print("Fetching Zotero ...", flush=True)
    items = json.loads(fetch(ZOTERO_URL))
    pubs  = process_pubs(items)

    total = sum(len(v) for v in pubs.values())
    print(f"  {total} items across {sum(1 for v in pubs.values() if v)} categories")

    env = Environment(
        loader=FileSystemLoader(str(TPL.parent)),
        undefined=StrictUndefined,
        block_start_string="<<",
        block_end_string=">>",
        variable_start_string="<{",
        variable_end_string="}>",
        comment_start_string="<#",
        comment_end_string="#>",
        autoescape=False,
        keep_trailing_newline=True,
    )
    env.filters["tex"]      = tex_esc
    env.filters["fmt_date"] = fmt_date

    rendered = env.get_template(TPL.name).render(
        me=me,
        pubs=pubs,
        updated=datetime.date.today().isoformat(),
    )
    OUT.write_text(rendered, encoding="utf-8")
    print(f"Wrote {OUT}", flush=True)


if __name__ == "__main__":
    main()
