#!/usr/bin/env python3
"""
scrape.py — Download and clean professor review documents.

Sources:
  - RateMyProfessors professor pages (GraphQL API, no JS rendering needed)
  - Coursicle course pages (requests + BeautifulSoup)
  - Koofers USC professor list (requests + BeautifulSoup)

Output: cleaned .txt files in documents/ with [Professor:] metadata tags
prepended to each review block so the embedding captures professor identity.

Usage:
  python scrape.py
"""

import base64
import re
import sys
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

DOCUMENTS_DIR = Path(__file__).parent / "documents"
DOCUMENTS_DIR.mkdir(exist_ok=True)

# RMP uses HTTP Basic auth with this public token on their own GraphQL endpoint.
# It decodes to "test:test" and is used by their React frontend.
RMP_GRAPHQL_URL = "https://www.ratemyprofessors.com/graphql"
RMP_AUTH = "Basic dGVzdDp0ZXN0"

# (rmp_numeric_id, display_name, primary_course_code, source_url)
RMP_PROFESSORS = [
    ("913088",  "Bill Cheng",        "CSCI 402", "https://www.ratemyprofessors.com/professor/913088"),
    ("860888",  "Mark Redekopp",     "CSCI 104", "https://www.ratemyprofessors.com/professor/860888"),
    ("2163737", "Andrew Goodney",    "CSCI 104", "https://www.ratemyprofessors.com/professor/2163737"),
    ("798241",  "Saty Raghavachary", "CSCI 585", "https://www.ratemyprofessors.com/professor/798241"),
    ("1746653", "Chi So",            "CSCI",     "https://www.ratemyprofessors.com/professor/1746653"),
]

# (url, course_code, display_name)
COURSICLE_COURSES = [
    ("https://www.coursicle.com/usc/courses/CSCI/104/", "CSCI 104", "Data Structures and OOP"),
    ("https://www.coursicle.com/usc/courses/CSCI/102/", "CSCI 102", "Intro to Programming"),
    ("https://www.coursicle.com/usc/courses/CSCI/",     "CSCI",     "All CSCI Courses Index"),
]

KOOFERS_URL = "https://www.koofers.com/university-of-southern-california-usc/professors"

# ── RateMyProfessors (GraphQL) ─────────────────────────────────────────────

_RMP_QUERY = """
query RatingsListQuery($id: ID!, $count: Int, $cursor: String) {
  node(id: $id) {
    ... on Teacher {
      firstName
      lastName
      numRatings
      avgRating
      department
      ratings(first: $count, after: $cursor) {
        edges {
          node {
            comment
            class
            qualityRating
            difficultyRating
            wouldTakeAgain
            date
          }
        }
        pageInfo { hasNextPage endCursor }
      }
    }
  }
}
"""


def _rmp_encoded_id(numeric_id: str) -> str:
    """Encode a numeric RMP professor ID into the base64 GraphQL node ID format."""
    return base64.b64encode(f"Teacher-{numeric_id}".encode()).decode()


def fetch_rmp_professor(numeric_id: str, name: str, course: str, url: str, max_reviews: int = 200) -> str:
    """
    Fetch professor reviews via RMP's GraphQL API.
    Returns cleaned text with [Professor: name] tags on every review line
    so chunker boundaries never strip the professor attribution.
    """
    encoded_id = _rmp_encoded_id(numeric_id)
    headers = {
        "Authorization": RMP_AUTH,
        "Content-Type": "application/json",
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Referer": url,
        "Origin": "https://www.ratemyprofessors.com",
    }

    all_reviews = []
    cursor = None

    while len(all_reviews) < max_reviews:
        batch = min(20, max_reviews - len(all_reviews))
        variables: dict = {"id": encoded_id, "count": batch}
        if cursor:
            variables["cursor"] = cursor

        resp = requests.post(
            RMP_GRAPHQL_URL,
            headers=headers,
            json={"query": _RMP_QUERY, "variables": variables},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        teacher = (data.get("data") or {}).get("node") or {}
        ratings_block = teacher.get("ratings") or {}
        edges = ratings_block.get("edges") or []

        if not edges:
            break

        for edge in edges:
            node = edge.get("node") or {}
            comment = (node.get("comment") or "").strip()
            if not comment:
                continue
            # wouldTakeAgain: 1 = yes, 0 = no, null = no answer
            wta_raw = node.get("wouldTakeAgain")
            wta = ("Yes" if wta_raw == 1 else "No") if wta_raw is not None else None
            all_reviews.append({
                "comment": comment,
                "class": (node.get("class") or "").strip(),
                "quality": node.get("qualityRating"),
                "difficulty": node.get("difficultyRating"),
                "would_take_again": wta,
                "date": (node.get("date") or "")[:10],  # keep YYYY-MM-DD only
            })

        page_info = ratings_block.get("pageInfo") or {}
        if not page_info.get("hasNextPage"):
            break
        cursor = page_info.get("endCursor")
        time.sleep(0.5)

    lines = [
        f"[Professor: {name}] [Course: {course}] [Source: RateMyProfessors] [URL: {url}]",
        "[School: University of Southern California]",
        "",
    ]
    for review in all_reviews:
        # Build a metadata prefix so every review line carries professor + course context.
        # This prevents cross-professor contamination when the chunker splits mid-file.
        parts = [f"[Professor: {name}]"]
        if review["class"]:
            parts.append(f"[Class: {review['class']}]")
        if review["quality"] is not None:
            parts.append(f"[Quality: {review['quality']}/5]")
        if review["difficulty"] is not None:
            parts.append(f"[Difficulty: {review['difficulty']}/5]")
        if review["would_take_again"] is not None:
            parts.append(f"[Would Take Again: {review['would_take_again']}]")
        lines.append(" ".join(parts))
        lines.append(review["comment"])
        lines.append("")

    return "\n".join(lines)


# ── Coursicle (BeautifulSoup) ──────────────────────────────────────────────

_BS4_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

_BOILERPLATE_CLASSES = re.compile(
    r"cookie|banner|popup|modal|nav|sidebar|ad-|footer|header|share|social|breadcrumb",
    re.I,
)


def _strip_boilerplate(soup: BeautifulSoup) -> None:
    """Remove navigation, scripts, ads, and other non-content elements in place."""
    for tag in soup(["nav", "footer", "script", "style", "header", "aside", "iframe", "noscript"]):
        tag.decompose()
    # Collect candidates first, then decompose — avoids modifying the tree while iterating
    to_remove = []
    for el in soup.find_all(True):
        cls_str = " ".join(el.get("class") or [])
        el_id = el.get("id") or ""
        if _BOILERPLATE_CLASSES.search(cls_str) or _BOILERPLATE_CLASSES.search(el_id):
            to_remove.append(el)
    for el in to_remove:
        el.decompose()


def _clean_text(text: str) -> str:
    """Collapse whitespace and remove leftover HTML entities."""
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&#\d+;", "", text)
    text = re.sub(r"&[a-z]+;", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def fetch_coursicle_course(url: str, course_code: str, course_name: str) -> str:
    """Fetch a Coursicle course page and extract review/comment text."""
    resp = requests.get(url, headers=_BS4_HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    _strip_boilerplate(soup)

    lines = [
        f"[Course: {course_code}] [Course Name: {course_name}] [Source: Coursicle] [URL: {url}]",
        "[School: University of Southern California]",
        "",
    ]

    # Coursicle review format: "Prof Name • timeago • Year Major  Review text..."
    # The entire block (header + review) lives in a single element with class matching "review".
    # We split on the bullet separator to isolate the professor name and the review body.
    _BULLET = re.compile(r"\s*•\s*")
    _YEAR_MAJOR = re.compile(r"^(Freshman|Sophomore|Junior|Senior|Graduate)\s+\w+", re.I)

    review_els = soup.find_all(class_=re.compile(r"review|comment|rating|feedback", re.I))

    if review_els:
        for el in review_els:
            text = _clean_text(el.get_text(separator=" "))
            if len(text) < 30:
                continue

            # Split "Prof Name • 3y • Sophomore BUAD  Review text" into parts
            parts = _BULLET.split(text, maxsplit=2)
            prof_name = parts[0].strip() if parts else None
            # The actual review text is the last segment after skipping metadata fields
            review_body = parts[-1].strip() if len(parts) > 1 else text
            # Drop metadata-only chunks that have no review body
            if _YEAR_MAJOR.match(review_body) or len(review_body) < 20:
                continue

            prefix = f"[Professor: {prof_name}] [Course: {course_code}] " if prof_name else f"[Course: {course_code}] "
            lines.append(f"{prefix}{review_body}")
            lines.append("")
    else:
        # Fallback: all paragraphs (covers JS-sparse pages)
        for p in soup.find_all("p"):
            text = _clean_text(p.get_text(separator=" "))
            if len(text) > 40:
                lines.append(text)
                lines.append("")

    return "\n".join(lines)


# ── Koofers (BeautifulSoup) ────────────────────────────────────────────────

def fetch_koofers(url: str) -> str:
    """Fetch the Koofers USC professor listing page."""
    resp = requests.get(url, headers=_BS4_HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    _strip_boilerplate(soup)

    lines = [
        f"[Source: Koofers] [URL: {url}]",
        "[School: University of Southern California]",
        "",
    ]

    for el in soup.find_all(class_=re.compile(r"professor|instructor|faculty|rating|review|card", re.I)):
        text = _clean_text(el.get_text(separator=" "))
        if len(text) > 20:
            lines.append(text)
            lines.append("")

    # Fallback: extract headings + following paragraphs
    if len(lines) < 5:
        for heading in soup.find_all(["h2", "h3", "h4"]):
            title = _clean_text(heading.get_text())
            sibling = heading.find_next_sibling("p")
            body = _clean_text(sibling.get_text()) if sibling else ""
            if title:
                lines.append(title)
                if body:
                    lines.append(body)
                lines.append("")

    return "\n".join(lines)


# ── Helpers ────────────────────────────────────────────────────────────────

def save_document(filename: str, content: str) -> None:
    path = DOCUMENTS_DIR / filename
    path.write_text(content, encoding="utf-8")
    word_count = len(content.split())
    review_count = content.count("[Professor:")
    print(f"    Saved {path.name}  ({word_count:,} words, {review_count} professor tags)")


# ── Main ───────────────────────────────────────────────────────────────────

def main() -> None:
    print("=" * 60)
    print("SCRAPING: RateMyProfessors (GraphQL API)")
    print("=" * 60)
    for numeric_id, name, course, url in RMP_PROFESSORS:
        print(f"  {name} ({course}) ...")
        try:
            text = fetch_rmp_professor(numeric_id, name, course, url)
            slug = name.lower().replace(" ", "_")
            save_document(f"rmp_{slug}.txt", text)
        except requests.HTTPError as e:
            print(f"    HTTP ERROR {e.response.status_code}: {e}", file=sys.stderr)
        except Exception as e:
            print(f"    ERROR: {e}", file=sys.stderr)
        time.sleep(1)

    print()
    print("=" * 60)
    print("SCRAPING: Coursicle (BeautifulSoup)")
    print("=" * 60)
    for url, course_code, course_name in COURSICLE_COURSES:
        print(f"  {course_code} — {course_name} ...")
        try:
            text = fetch_coursicle_course(url, course_code, course_name)
            slug = course_code.lower().replace(" ", "")
            save_document(f"coursicle_{slug}.txt", text)
        except requests.HTTPError as e:
            print(f"    HTTP ERROR {e.response.status_code}: {e}", file=sys.stderr)
        except Exception as e:
            print(f"    ERROR: {e}", file=sys.stderr)
        time.sleep(3)  # Coursicle rate-limits at ~1 req/s; 3s gives comfortable headroom

    print()
    print("=" * 60)
    print("SCRAPING: Koofers (BeautifulSoup)")
    print("=" * 60)
    print("  USC CS professor ratings ...")
    try:
        text = fetch_koofers(KOOFERS_URL)
        save_document("koofers_usc_cs.txt", text)
    except requests.HTTPError as e:
        print(f"    HTTP ERROR {e.response.status_code}: {e}", file=sys.stderr)
    except Exception as e:
        print(f"    ERROR: {e}", file=sys.stderr)

    print()
    print("Done. Check documents/ for output files.")
    print("Next step: run  python chunk.py")


if __name__ == "__main__":
    main()
