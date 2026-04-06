"""
Backend Agent — HTTP health, performance, caching, and security audit.
Returns list of issues.
"""

import sys
import os
import re
import time
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from issue_schema import create_issue


SLOW_THRESHOLD = 2.0
VERY_SLOW_THRESHOLD = 6.0
REQUEST_TIMEOUT = 8


def _deduplicate(issues):
    unique = []
    seen = set()

    for i in issues:
        key = (i.get("title"), i.get("description"))
        if key not in seen:
            seen.add(key)
            unique.append(i)

    return unique


def run_backend_agent(url: str) -> list:
    if not url or not url.startswith("http"):
        raise Exception("Backend Agent → Invalid URL")

    issues = []

    try:
        t0 = time.time()
        res = requests.get(url, allow_redirects=True, timeout=REQUEST_TIMEOUT)
        elapsed = round(time.time() - t0, 3)
    except Exception as e:
        raise Exception(f"Backend Agent → URL unreachable: {e}")

    headers = res.headers
    body = res.text

    # ===== STATUS CODE =====
    if res.status_code >= 500:
        issues.append(create_issue(
            "Backend",
            f"Server Error ({res.status_code})",
            "HIGH",
            "Application unavailable",
            f"HTTP status {res.status_code}",
            "Fix server-side errors immediately",
            confidence="HIGH"
        ))

    elif res.status_code >= 400:
        issues.append(create_issue(
            "Backend",
            f"Client Error ({res.status_code})",
            "HIGH",
            "Broken endpoint",
            f"HTTP status {res.status_code}",
            "Fix route or configure redirects",
            confidence="HIGH"
        ))

    # ===== RESPONSE TIME =====
    if elapsed >= VERY_SLOW_THRESHOLD:
        issues.append(create_issue(
            "Performance",
            f"Very slow response ({elapsed}s)",
            "HIGH",
            "Severe UX degradation",
            f"Response time exceeded {VERY_SLOW_THRESHOLD}s",
            "Optimize backend, add caching, use CDN",
            confidence="HIGH"
        ))

    elif elapsed >= SLOW_THRESHOLD:
        issues.append(create_issue(
            "Performance",
            f"Slow response ({elapsed}s)",
            "MEDIUM",
            "Poor user experience",
            f"Response time exceeded {SLOW_THRESHOLD}s",
            "Optimize queries and enable caching",
            confidence="HIGH"
        ))

    # ===== HEADER LEAKS =====
    for hdr in ["Server", "X-Powered-By"]:
        if hdr in headers:
            val = headers[hdr]
            if re.search(r"\d", val):
                issues.append(create_issue(
                    "Security",
                    f"Server version exposed ({hdr})",
                    "HIGH",
                    "Attackers can target known vulnerabilities",
                    f"{hdr}: {val}",
                    "Hide or obfuscate server version",
                    confidence="HIGH",
                    location=f"Header: {hdr}"
                ))

    # ===== CACHE =====
    if "Cache-Control" not in headers:
        issues.append(create_issue(
            "Performance",
            "Missing Cache-Control",
            "MEDIUM",
            "No browser caching",
            "Cache-Control header missing",
            "Add caching headers for static assets",
            confidence="HIGH"
        ))

    # ===== COMPRESSION =====
    if "Content-Encoding" not in headers:
        issues.append(create_issue(
            "Performance",
            "No compression enabled",
            "MEDIUM",
            "Larger payload size",
            "No gzip/brotli detected",
            "Enable compression on server",
            confidence="MEDIUM"
        ))

    # ===== ERROR LEAKS =====
    leak_patterns = [
        "traceback",
        "sql syntax",
        "exception",
        "php warning",
        "java.lang"
    ]

    for pattern in leak_patterns:
        if re.search(pattern, body, re.IGNORECASE):
            issues.append(create_issue(
                "Security",
                "Error details exposed",
                "HIGH",
                "Sensitive internal info leak",
                f"Detected pattern: {pattern}",
                "Disable debug output in production",
                confidence="HIGH"
            ))
            break

    # ===== API EXPOSURE =====
    api_paths = re.findall(r'["\'](/api/[^"\']+)["\']', body)
    if api_paths:
        unique_paths = list(set(api_paths))[:5]

        issues.append(create_issue(
            "Security",
            "API endpoints exposed",
            "MEDIUM",
            "Attack surface increased",
            f"Endpoints found: {', '.join(unique_paths)}",
            "Secure endpoints with auth and validation",
            confidence="MEDIUM"
        ))

    # ===== CORS =====
    if headers.get("Access-Control-Allow-Origin") == "*":
        issues.append(create_issue(
            "Security",
            "CORS wildcard enabled",
            "HIGH",
            "Any domain can access resources",
            "Access-Control-Allow-Origin: *",
            "Restrict allowed origins",
            confidence="HIGH"
        ))

    return _deduplicate(issues)