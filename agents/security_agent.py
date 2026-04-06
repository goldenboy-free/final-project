"""
Security Agent — detects XSS, CSRF risks, sensitive data exposure, and insecure patterns.
Returns list of issues.
"""

import re
import sys
import os
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from issue_schema import create_issue


MIN_CONTENT_LENGTH = 200


def _deduplicate(issues):
    unique = []
    seen = set()

    for i in issues:
        key = (i.get("title"), i.get("description"))
        if key not in seen:
            seen.add(key)
            unique.append(i)

    return unique


def _detect_xss(soup, raw_html):
    issues = []

    # Inline script tags
    scripts = soup.find_all("script")
    if scripts:
        issues.append(create_issue(
            "Security",
            "Inline scripts detected",
            "MEDIUM",
            "Potential XSS risk",
            f"{len(scripts)} inline script tags found",
            "Move scripts to external files and sanitize inputs",
            confidence="MEDIUM"
        ))

    # Dangerous inline event handlers
    events = re.findall(r'on\w+="[^"]+"', raw_html, re.IGNORECASE)
    if events:
        issues.append(create_issue(
            "Security",
            "Inline event handlers detected",
            "HIGH",
            "High XSS risk",
            f"{len(events)} inline JS event handlers found",
            "Remove inline JS and use safe event listeners",
            confidence="HIGH"
        ))

    return issues


def _detect_csrf(soup):
    issues = []

    forms = soup.find_all("form")
    risky_forms = []

    for f in forms:
        if f.find("input", {"type": "hidden", "name": re.compile("csrf|token", re.I)}):
            continue
        risky_forms.append(f)

    if risky_forms:
        issues.append(create_issue(
            "Security",
            "Forms without CSRF protection",
            "HIGH",
            "CSRF attack risk",
            f"{len(risky_forms)} forms missing CSRF tokens",
            "Add CSRF tokens and validate server-side",
            confidence="HIGH"
        ))

    return issues


def _detect_sensitive_data(content):
    issues = []

    patterns = {
        "Email exposure": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b',
        "API key exposure": r'api[_-]?key\s*=\s*["\']?[A-Za-z0-9_\-]{16,}',
        "Token exposure": r'(token|auth)\s*=\s*["\']?[A-Za-z0-9_\-]{16,}'
    }

    for label, pattern in patterns.items():
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            issues.append(create_issue(
                "Security",
                f"{label} detected",
                "HIGH",
                "Sensitive data exposure",
                f"Detected {len(matches)} potential instances",
                "Remove or secure sensitive data",
                confidence="HIGH"
            ))

    return issues


def _detect_iframe_risks(soup):
    issues = []

    iframes = soup.find_all("iframe")
    external = []

    for iframe in iframes:
        src = iframe.get("src", "")
        if src.startswith("http"):
            external.append(src)

    if external:
        issues.append(create_issue(
            "Security",
            "External iframes detected",
            "MEDIUM",
            "Potential clickjacking or malicious embedding",
            f"{len(external)} external iframe sources found",
            "Validate and restrict iframe sources",
            confidence="MEDIUM"
        ))

    return issues


def _detect_unsafe_links(soup):
    issues = []

    links = soup.find_all("a", href=True)
    javascript_links = [a for a in links if a["href"].startswith("javascript:")]

    if javascript_links:
        issues.append(create_issue(
            "Security",
            "Unsafe javascript links",
            "HIGH",
            "XSS or phishing risk",
            f"{len(javascript_links)} javascript: links found",
            "Avoid javascript: URLs",
            confidence="HIGH"
        ))

    return issues


def run_security_agent(content: str) -> list:
    if not content or len(content.strip()) < MIN_CONTENT_LENGTH:
        raise Exception(f"Security Agent → Content too small ({len(content or '')} chars)")

    soup = BeautifulSoup(content, "html.parser")

    issues = []

    # Core checks
    issues.extend(_detect_xss(soup, content))
    issues.extend(_detect_csrf(soup))
    issues.extend(_detect_sensitive_data(content))
    issues.extend(_detect_iframe_risks(soup))
    issues.extend(_detect_unsafe_links(soup))

    return _deduplicate(issues)