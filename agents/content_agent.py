"""
Content Agent — deep analysis of text quality, structure, and readability.
Returns List[issues]. Raises Exception on failure.
"""

import re
import sys
import os
from collections import Counter

import requests
from bs4 import BeautifulSoup
from textblob import TextBlob
import textstat

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from issue_schema import create_issue

HEADERS = {"User-Agent": "Mozilla/5.0"}
MIN_HTML_LENGTH = 500


def _fetch(url: str) -> tuple[str, str]:
    try:
        res = requests.get(url, headers=HEADERS, timeout=12)
    except Exception as e:
        raise Exception(f"Content Agent → URL unreachable: {e}")

    html = res.text
    if len(html) < MIN_HTML_LENGTH or "<html" not in html.lower():
        raise Exception(f"Content Agent → Invalid HTML ({len(html)} chars)")

    soup = BeautifulSoup(html, "lxml")
    text = re.sub(r"\s+", " ", soup.get_text(separator=" ")).strip()
    return html, text


def run_content_grammar_visual_audit(url: str) -> list:
    html, text = _fetch(url)
    soup = BeautifulSoup(html, "lxml")

    words = text.split()
    word_count = len(words)
    issues = []

    # ===== THIN CONTENT =====
    if word_count < 300:
        issues.append(create_issue(
            "Content",
            "Thin Content",
            "HIGH",
            "Low ranking potential",
            f"Only {word_count} words found",
            "Increase content to at least 800+ words"
        ))

    # ===== SPELLING =====
    errors = []
    for word in words[:500]:
        if re.match(r"^[a-zA-Z]{4,}$", word):
            corrected = str(TextBlob(word).correct())
            if corrected.lower() != word.lower():
                errors.append(f"{word}->{corrected}")

    if errors:
        issues.append(create_issue(
            "Content",
            f"Spelling Errors ({len(errors)})",
            "MEDIUM",
            "Reduces credibility",
            f"Examples: {', '.join(errors[:5])}",
            "Run a spell checker"
        ))

    # ===== READABILITY =====
    sample_text = text[:5000]
    fre = textstat.flesch_reading_ease(sample_text)

    if fre < 30:
        issues.append(create_issue(
            "Content",
            "Very Low Readability",
            "HIGH",
            "Hard to understand",
            f"FRE score: {round(fre,1)}",
            "Simplify sentences and reduce jargon"
        ))
    elif fre < 60:
        issues.append(create_issue(
            "Content",
            "Moderate Readability",
            "MEDIUM",
            "Some users may struggle",
            f"FRE score: {round(fre,1)}",
            "Use shorter sentences and simpler words"
        ))

    # ===== SENTIMENT =====
    polarity = TextBlob(sample_text).sentiment.polarity
    if polarity < -0.25:
        issues.append(create_issue(
            "Content",
            "Negative Tone",
            "LOW",
            "May reduce engagement",
            f"Polarity: {round(polarity,2)}",
            "Use more positive language"
        ))

    # ===== CTA =====
    cta_words = ["buy", "sign up", "register", "download", "contact"]
    if not any(word in text.lower() for word in cta_words):
        issues.append(create_issue(
            "Content",
            "No Call-To-Action",
            "MEDIUM",
            "Low conversion rate",
            "No CTA found",
            "Add a clear CTA like 'Sign up' or 'Get started'"
        ))

    # ===== KEYWORD DENSITY =====
    stopwords = {"the","a","an","is","it","in","on","at","to","of","and","or","for"}
    freq = Counter(w.lower() for w in words if w.lower() not in stopwords and len(w) > 3)

    for word, count in freq.most_common(5):
        density = (count / word_count) * 100 if word_count else 0
        if density > 3:
            issues.append(create_issue(
                "Content",
                f"Keyword Stuffing: {word}",
                "HIGH",
                "SEO penalty risk",
                f"{word} appears {round(density,2)}%",
                "Reduce repetition and use synonyms"
            ))
            break

    # ===== DUPLICATE PARAGRAPHS =====
    paragraphs = [p.get_text(strip=True) for p in soup.find_all("p")]
    seen = set()
    duplicates = []

    for p in paragraphs:
        if p in seen:
            duplicates.append(p[:80])
        seen.add(p)

    if duplicates:
        issues.append(create_issue(
            "Content",
            "Duplicate Content",
            "MEDIUM",
            "SEO penalty risk",
            f"{len(duplicates)} duplicate paragraphs found",
            "Rewrite duplicate sections"
        ))

    # ===== H1 CHECK =====
    h1s = soup.find_all("h1")
    if not h1s:
        issues.append(create_issue(
            "Content",
            "Missing H1",
            "HIGH",
            "SEO signal loss",
            "No H1 tag",
            "Add one H1 with main keyword"
        ))
    elif len(h1s) > 1:
        issues.append(create_issue(
            "Content",
            "Multiple H1 Tags",
            "MEDIUM",
            "SEO confusion",
            f"{len(h1s)} H1 tags",
            "Keep only one H1"
        ))

    # ===== IMAGE ALT =====
    imgs = soup.find_all("img")
    missing_alt = [img for img in imgs if not img.get("alt")]

    if missing_alt:
        issues.append(create_issue(
            "Content",
            "Images Missing ALT",
            "HIGH",
            "Accessibility + SEO impact",
            f"{len(missing_alt)} images missing alt",
            "Add descriptive alt text",
            location="<img>"
        ))

    return issues