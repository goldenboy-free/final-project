"""
Broken Links Agent — checks for dead or 404 links on the page.
"""

import requests
from bs4 import BeautifulSoup
import sys
import os
from urllib.parse import urljoin

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from issue_schema import create_issue

def check_link(url: str) -> bool:
    """Returns True if link is broken (400+ status code) or unresolvable."""
    try:
        # Fast HEAD request first
        res = requests.head(url, timeout=5, allow_redirects=True)
        if res.status_code >= 400:
            # Fallback to GET to be sure
            res_get = requests.get(url, timeout=5)
            if res_get.status_code >= 400:
                return True
        return False
    except requests.RequestException:
        return True

def run_broken_links_agent(html_content: str, base_url: str) -> list:
    if not html_content:
        return []

    soup = BeautifulSoup(html_content, "lxml")
    links = [a.get('href') for a in soup.find_all('a', href=True)]
    
    unique_links = list(set(links))
    # Limit to 15 links to prevent scanning taking too long
    unique_links = unique_links[:15]
    
    broken_links = []
    issues = []

    for link in unique_links:
        # Ignore mailto, tel, javascript links
        if link.startswith(('mailto:', 'tel:', 'javascript:')):
            continue
            
        full_url = urljoin(base_url, link)
        if check_link(full_url):
            broken_links.append(full_url)

    if broken_links:
        for link in broken_links[:5]:  # limit the number of reported issues to avoid spam
            issues.append(create_issue(
                "Broken Links",
                "Dead Link Found",
                "HIGH",
                "Negative UX and SEO penalty",
                f"Link returns an error or is unreachable: {link}",
                "Remove or update the dead link."
            ))

    return issues
