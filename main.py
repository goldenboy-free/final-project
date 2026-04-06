import sys
import os
import time
import json
from typing import List, Dict

import requests
from bs4 import BeautifulSoup
from colorama import Fore, init

# Standard UTF-8 encoding support for Windows terminals
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

init(autoreset=True)

# Schema
from issue_schema import Issue

# Agents
from agents import (
    content_agent,
    frontend_agent,
    security_agent,
    seo_agent,
    backend_agent,
    plagiarism_agent,
    image_agent
)

SEVERITY_COLOR = {
    "HIGH": Fore.RED,
    "MEDIUM": Fore.YELLOW,
    "LOW": Fore.CYAN,
}

MIN_HTML_LENGTH = 500


def run_agent(name: str, fn, *args) -> List[Issue]:
    """Wraps each agent call safely and returns a list of Issue objects."""
    print(Fore.BLUE + f"⚙ Running {name}...", end=" ", flush=True)
    try:
        issues = fn(*args)
        if not isinstance(issues, list):
            issues = []
        print(Fore.GREEN + f"✔ {len(issues)} issue(s)")
        return issues
    except Exception as e:
        print(Fore.RED + f"✘ FAILED — {e}")
        return []


def print_dashboard(all_issues: List[Issue], runtime: float):
    """Prints the structured report to the console by category and priority."""
    print(Fore.MAGENTA + "\n" + "═" * 60)
    print(Fore.MAGENTA + "  🚀  AI WEBSITE AUDIT — ACTIONABLE ISSUES")
    print(Fore.MAGENTA + "═" * 60)

    if not all_issues:
        print(Fore.GREEN + "\n✅ No issues detected. Website looks clean.\n")
    else:
        # Sort by priority (P1 -> P3)
        sorted_issues = sorted(all_issues, key=lambda i: (i.priority, i.category))
        
        # Group by category
        grouped = {}
        for issue in sorted_issues:
            if issue.category not in grouped:
                grouped[issue.category] = []
            grouped[issue.category].append(issue)

        for category, issues in grouped.items():
            print(Fore.WHITE + Style.BRIGHT + f"\n=== {category.upper()} ===")
            for i in issues:
                color = SEVERITY_COLOR.get(i.severity, Fore.WHITE)
                print(color + f"[P{i.priority}] {i.title}")
                print(Fore.WHITE + f"Severity: {i.severity}")
                print(Fore.GREEN + f"Fix: {i.suggestion}")
                if i.location:
                    print(Fore.CYAN + f"Location: {i.location}")

    # Summary Stats
    counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for i in all_issues:
        counts[i.severity] += 1

    print(Fore.MAGENTA + "\n" + "─" * 60)
    print(
        Fore.RED + f" HIGH: {counts['HIGH']}  " +
        Fore.YELLOW + f" MEDIUM: {counts['MEDIUM']}  " +
        Fore.CYAN + f" LOW: {counts['LOW']}"
    )
    print(Fore.WHITE + f" Total Issues : {len(all_issues)}")
    print(Fore.WHITE + f" Runtime      : {runtime}s")
    print(Fore.MAGENTA + "═" * 60 + "\n")


def fetch_page(url: str):
    """Fetches HTML and validates content length."""
    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=12)
        html = res.text
        if len(html) < MIN_HTML_LENGTH:
            raise Exception(f"URL returned insufficient content ({len(html)} chars). Minimum required: {MIN_HTML_LENGTH}.")
        
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(separator=" ", strip=True)
        return html, text
    except Exception as e:
        raise Exception(f"Failed to fetch or validate page: {str(e)}")


def run_pipeline(url: str, show_output=True):
    """The core audit orchestration pipeline."""
    if show_output:
        print(Fore.CYAN + f"\n🌐 AI Website Audit — {url}\n")

    start = time.time()

    try:
        html, text = fetch_page(url)
    except Exception as e:
        if show_output:
            print(Fore.RED + f"✘ FATAL: {e}")
        raise e

    # 1. Content Agent (URL-based for spelling/external checks)
    content_issues = run_agent("Content + Grammar", content_agent.run_content_grammar_visual_audit, url)

    # 2. Frontend Agent (HTML-based)
    frontend_issues = run_agent("Frontend / Accessibility", frontend_agent.run_frontend_agent, html)

    # 3. Security Agent (URL-based for headers)
    security_issues = run_agent("Security Audit", security_agent.run_security_agent, url)

    # 4. SEO Agent (HTML-based)
    seo_issues = run_agent("SEO Audit", seo_agent.run_seo_agent, html, url)

    # 5. Backend Agent (URL-based for performance/TTFB)
    backend_issues = run_agent("Backend Performance", backend_agent.run_backend_agent, url)

    # 6. Plagiarism Agent (URL-based for content sourcing)
    plagiarism_issues = run_agent("Plagiarism Check", plagiarism_agent.run_plagiarism_agent, url)

    # 7. Image Agent (HTML-based)
    image_issues = run_agent("Image Deep Audit", image_agent.run_image_agent, html, url)

    # Combine all Issue objects
    all_issues: List[Issue] = (
        content_issues +
        frontend_issues +
        security_issues +
        seo_issues +
        backend_issues +
        plagiarism_issues +
        image_issues
    )

    runtime = round(time.time() - start, 2)

    if show_output:
        from colorama import Style
        print_dashboard(all_issues, runtime)

    # Save structured reports
    os.makedirs("reports", exist_ok=True)
    
    report_data = {
        "url": url,
        "runtime": runtime,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_issues": len(all_issues),
        "issues": [i.to_dict() for i in all_issues]
    }
    
    output_path = os.path.join("reports", "final_audit_report.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)

    if show_output:
        print(Fore.WHITE + f"📁 Full JSON report saved: {output_path}")

    return report_data


if __name__ == "__main__":
    url = input("Enter Website URL (with http/https): ").strip()
    if not url.startswith(("http://", "https://")):
        print(Fore.RED + "Invalid URL format. Must start with http:// or https://")
        sys.exit(1)
    
    try:
        run_pipeline(url)
    except Exception:
        sys.exit(1)