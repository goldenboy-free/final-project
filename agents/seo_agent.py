import sys
import os
import re
from collections import Counter
from bs4 import BeautifulSoup
from issue_schema import create_issue

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

MIN_HTML_LENGTH = 500

def extract_text(soup):
    for script in soup(["script", "style"]):
        script.decompose()
    return soup.get_text(separator=" ").lower()

def run_seo_agent(html_content: str, url: str) -> list:
    if not html_content or len(html_content.strip()) < MIN_HTML_LENGTH:
        raise Exception(f"SEO Agent → HTML too small ({len(html_content or '')} chars)")

    soup = BeautifulSoup(html_content, "lxml")
    issues = []

    # ===== TITLE =====
    title_tag = soup.title
    title_text = (title_tag.string or "").strip() if title_tag else ""

    if not title_text:
        issues.append(create_issue(
            "SEO", "Missing Page Title", "HIGH",
            "Search ranking",
            "No <title> tag found.",
            "Add a 50–60 character title with primary keyword."
        ))
    elif len(title_text) > 60:
        issues.append(create_issue(
            "SEO", "Title Too Long", "MEDIUM",
            "SERP truncation",
            f"Length: {len(title_text)} chars",
            "Reduce to 50–60 characters."
        ))

    # ===== META DESCRIPTION =====
    meta = soup.find("meta", attrs={"name": "description"})
    desc = (meta.get("content") or "").strip() if meta else ""

    if not desc:
        issues.append(create_issue(
            "SEO", "Missing Meta Description", "MEDIUM",
            "Low CTR",
            "Meta description missing",
            "Add 120–160 character description."
        ))

    # ===== H1 =====
    h1s = soup.find_all("h1")
    if not h1s:
        issues.append(create_issue(
            "SEO", "Missing H1", "HIGH",
            "Ranking signal lost",
            "No H1 tag",
            "Add one H1 with keyword."
        ))
    elif len(h1s) > 1:
        issues.append(create_issue(
            "SEO", "Multiple H1 Tags", "LOW",
            "SEO confusion",
            f"{len(h1s)} H1 tags found",
            "Use only one H1."
        ))

    # ===== CANONICAL =====
    if not soup.find("link", rel="canonical"):
        issues.append(create_issue(
            "SEO", "Missing Canonical Tag", "MEDIUM",
            "Duplicate content risk",
            "No canonical link tag",
            "Add <link rel='canonical'> to define primary URL."
        ))

    # ===== STRUCTURED DATA =====
    if not soup.find("script", attrs={"type": "application/ld+json"}):
        issues.append(create_issue(
            "SEO", "No Structured Data", "LOW",
            "No rich results",
            "Missing JSON-LD",
            "Add structured data markup."
        ))

    # ===== KEYWORD DENSITY =====
    text = extract_text(soup)
    words = re.findall(r'\b\w+\b', text)

    if len(words) > 50:
        freq = Counter(words)
        total = len(words)

        for word, count in freq.most_common(5):
            density = (count / total) * 100

            if density > 3:
                issues.append(create_issue(
                    "SEO",
                    f"Keyword Stuffing Detected: '{word}' ({density:.2f}%)",
                    "HIGH",
                    "Search penalty risk",
                    f"Keyword '{word}' appears too frequently.",
                    "Reduce repetition and use natural variations."
                ))
                break

    return issues