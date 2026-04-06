"""
Frontend Agent — advanced frontend audit (UI, accessibility, performance, SEO).
Returns list of issues.
"""

import re
import sys
import os
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from issue_schema import create_issue

MIN_HTML_LENGTH = 500


def run_frontend_agent(html: str) -> list:
    if not html or len(html.strip()) < MIN_HTML_LENGTH:
        raise Exception(f"Frontend Agent → HTML too small ({len(html or '')} chars)")

    soup = BeautifulSoup(html, "html.parser")
    issues = []

    # ===== BASIC STRUCTURE =====
    if not html.lower().lstrip().startswith("<!doctype"):
        issues.append(create_issue(
            "HTML",
            "Missing DOCTYPE",
            "HIGH",
            "Rendering issues",
            "DOCTYPE not found",
            "Add <!DOCTYPE html>"
        ))

    if not soup.find("html") or not soup.find("html").get("lang"):
        issues.append(create_issue(
            "Accessibility",
            "Missing lang attribute",
            "HIGH",
            "Screen readers fail",
            "<html> missing lang",
            "Add lang='en'"
        ))

    # ===== SEO =====
    if not soup.title or not (soup.title.string or "").strip():
        issues.append(create_issue(
            "SEO",
            "Missing title",
            "HIGH",
            "SEO impact",
            "No title tag",
            "Add <title>"
        ))

    if not soup.find("meta", attrs={"name": "description"}):
        issues.append(create_issue(
            "SEO",
            "Missing meta description",
            "MEDIUM",
            "Lower CTR",
            "No description",
            "Add meta description"
        ))

    # ===== H1 =====
    h1s = soup.find_all("h1")
    if len(h1s) == 0:
        issues.append(create_issue(
            "Structure",
            "Missing H1",
            "HIGH",
            "SEO unclear",
            "No H1 tag",
            "Add one H1"
        ))
    elif len(h1s) > 1:
        issues.append(create_issue(
            "Structure",
            "Multiple H1",
            "MEDIUM",
            "SEO confusion",
            f"{len(h1s)} H1 tags",
            "Keep one H1"
        ))

    # ===== IMAGES =====
    images = soup.find_all("img")

    missing_alt = [img for img in images if not img.get("alt")]
    if missing_alt:
        issues.append(create_issue(
            "Accessibility",
            "Missing ALT text",
            "HIGH",
            "Screen reader issue",
            f"{len(missing_alt)} images missing alt",
            "Add alt attributes",
            location="<img>"
        ))

    broken_imgs = [img for img in images if not img.get("src")]
    if broken_imgs:
        issues.append(create_issue(
            "UX",
            "Broken images",
            "MEDIUM",
            "Images not loading",
            f"{len(broken_imgs)} images missing src",
            "Fix image sources"
        ))

    if len(images) > 50:
        issues.append(create_issue(
            "Performance",
            "Too many images",
            "MEDIUM",
            "Slow loading",
            f"{len(images)} images detected",
            "Optimize and reduce images"
        ))

    # ===== PERFORMANCE =====
    inline_css = soup.find_all(style=True)
    if len(inline_css) > 20:
        issues.append(create_issue(
            "Performance",
            "Excessive inline CSS",
            "LOW",
            "Hard to maintain",
            f"{len(inline_css)} inline styles",
            "Move to external CSS"
        ))

    scripts = soup.find_all("script", src=True)
    if len(scripts) > 10:
        issues.append(create_issue(
            "Performance",
            "Too many JS files",
            "MEDIUM",
            "Slow loading",
            f"{len(scripts)} scripts",
            "Bundle JS files"
        ))

    head = soup.find("head")
    if head:
        blocking = [s for s in head.find_all("script", src=True)
                    if not s.get("async") and not s.get("defer")]
        if blocking:
            issues.append(create_issue(
                "Performance",
                "Render blocking scripts",
                "MEDIUM",
                "Delays page load",
                f"{len(blocking)} blocking scripts",
                "Use async/defer"
            ))

    # ===== ACCESSIBILITY =====
    for btn in soup.find_all("button"):
        if not btn.get_text(strip=True) and not btn.get("aria-label"):
            issues.append(create_issue(
                "Accessibility",
                "Button without label",
                "HIGH",
                "Screen reader issue",
                "Button has no label",
                "Add text or aria-label",
                location="<button>"
            ))
            break

    empty_links = [a for a in soup.find_all("a")
                   if not a.get_text(strip=True) and not a.get("aria-label")]

    if empty_links:
        issues.append(create_issue(
            "Accessibility",
            "Empty links",
            "MEDIUM",
            "No context",
            f"{len(empty_links)} empty links",
            "Add link text"
        ))

    # ===== RESPONSIVENESS =====
    if not soup.find("meta", attrs={"name": "viewport"}):
        issues.append(create_issue(
            "Responsive",
            "Missing viewport",
            "HIGH",
            "Mobile unusable",
            "No viewport meta tag",
            "Add responsive viewport"
        ))

    fixed_width = re.findall(r'width:\s*\d+px', html)
    if len(fixed_width) > 10:
        issues.append(create_issue(
            "Responsive",
            "Fixed width layout",
            "MEDIUM",
            "Not mobile friendly",
            f"{len(fixed_width)} fixed widths",
            "Use responsive units"
        ))

    return issues