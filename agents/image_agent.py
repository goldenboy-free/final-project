"""
Image Agent — checks alt text, broken images, lazy loading, and large image file sizes.
Returns List[Issue]. Raises Exception on failure.
"""
import sys
import os
import re
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from issue_schema import Issue

HEADERS = {"User-Agent": "Mozilla/5.0"}
LARGE_IMAGE_THRESHOLD_KB = 200   # > 200 KB is considered unoptimised
VERY_LARGE_IMAGE_KB = 1024       # > 1 MB is HIGH severity


def _check_image(img_url: str) -> dict:
    """Returns status, size_kb for one image URL."""
    try:
        r = requests.head(img_url, headers=HEADERS, timeout=6, allow_redirects=True)
        status = r.status_code
        cl = r.headers.get("Content-Length")
        size_kb = int(cl) // 1024 if cl else None
        if size_kb is None and status == 200:
            # Fall back to GET for size
            r2 = requests.get(img_url, headers=HEADERS, timeout=8, stream=True)
            content = b""
            for chunk in r2.iter_content(1024 * 16):
                content += chunk
                if len(content) > 2 * 1024 * 1024:  # stop at 2 MB
                    break
            size_kb = len(content) // 1024
        return {"url": img_url, "status": status, "size_kb": size_kb}
    except Exception:
        return {"url": img_url, "status": None, "size_kb": None}


def run_image_agent(html: str, base_url: str) -> list:
    if not html or len(html.strip()) < 500:
        raise Exception(f"Image Agent → HTML too small ({len(html or '')} chars)")

    soup = BeautifulSoup(html, "html.parser")
    images = soup.find_all("img")

    if not images:
        return []  # no images to analyse

    issues = []

    # ── ALT text ─────────────────────────────────────────────────────────────
    missing_alt = [img for img in images if not img.get("alt")]
    if missing_alt:
        issues.append(Issue(
            category="Image Quality",
            title=f"Images Missing ALT Text ({len(missing_alt)}/{len(images)})",
            severity="HIGH",
            impact="WCAG 2.1 Level A failure; screen readers skip the image; Google cannot index image content",
            description=f"{len(missing_alt)} <img> elements have no alt attribute. Example src: '{missing_alt[0].get('src', 'unknown')}'",
            suggestion="Add alt='[concise image description]' to every content image. Use alt='' only for purely decorative images.",
            confidence="HIGH",
            location="<img> tags without alt",
        ))

    # ── Empty/whitespace-only ALT ─────────────────────────────────────────────
    empty_alt = [img for img in images
                 if img.get("alt") is not None and not img.get("alt", "").strip()]
    content_empty_alt = [img for img in empty_alt
                         if not _is_decorative(img)]
    if content_empty_alt:
        issues.append(Issue(
            category="Image Quality",
            title=f"Content Images with Empty ALT Text ({len(content_empty_alt)})",
            severity="MEDIUM",
            impact="Screen readers skip images with alt='', causing context loss for informational images",
            description=f"{len(content_empty_alt)} images appear to be content images but have alt=''.",
            suggestion="Replace empty alt with a meaningful description for non-decorative images.",
            confidence="MEDIUM",
        ))

    # ── Lazy loading ─────────────────────────────────────────────────────────
    no_lazy = [img for img in images if not img.get("loading")]
    if no_lazy:
        issues.append(Issue(
            category="Performance",
            title=f"Images Missing lazy Loading ({len(no_lazy)}/{len(images)})",
            severity="MEDIUM",
            impact="All images load immediately, increasing initial page payload and delaying above-the-fold content",
            description=f"{len(no_lazy)} images have no loading='lazy'.",
            suggestion="Add loading='lazy' to all images below the fold. Keep loading='eager' only for hero/above-the-fold images.",
            confidence="HIGH",
        ))

    # ── Resolve absolute URLs for probe ──────────────────────────────────────
    src_list = []
    for img in images:
        src = img.get("src", "").strip()
        if not src or src.startswith("data:"):
            continue
        absolute = urljoin(base_url, src)
        src_list.append(absolute)

    if not src_list:
        return issues

    # ── Broken images & file size (parallel) ──────────────────────────────────
    results = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(_check_image, url): url for url in src_list[:30]}
        for future in as_completed(futures):
            results.append(future.result())

    broken = [r for r in results if r["status"] and r["status"] >= 400]
    if broken:
        sample = broken[0]["url"]
        issues.append(Issue(
            category="Image Quality",
            title=f"Broken Image Links ({len(broken)})",
            severity="HIGH",
            impact="Broken images show placeholder icons, damaging user trust and perceived quality",
            description=f"{len(broken)} image URL(s) return HTTP errors. First: {sample}",
            suggestion="Fix or remove broken image paths. Use a site crawler (Screaming Frog / broken-link-checker) to audit all images.",
            confidence="HIGH",
            location=sample,
        ))

    very_large = [r for r in results if r["size_kb"] and r["size_kb"] > VERY_LARGE_IMAGE_KB]
    if very_large:
        sample = very_large[0]
        issues.append(Issue(
            category="Performance",
            title=f"Very Large Images ({len(very_large)} over 1 MB)",
            severity="HIGH",
            impact=f"Images over 1 MB dramatically slow page load — especially on mobile connections",
            description=f"Example: {sample['url']} is {sample['size_kb']} KB.",
            suggestion="Compress images with Squoosh or ImageOptim. Convert to WebP/AVIF. Serve appropriately sized images per viewport using <picture> or srcset.",
            confidence="HIGH",
            location=sample["url"],
        ))
    else:
        large = [r for r in results if r["size_kb"] and r["size_kb"] > LARGE_IMAGE_THRESHOLD_KB]
        if large:
            sample = large[0]
            issues.append(Issue(
                category="Performance",
                title=f"Unoptimised Images ({len(large)} over {LARGE_IMAGE_THRESHOLD_KB} KB)",
                severity="MEDIUM",
                impact="Oversized images increase page weight and slow Core Web Vital scores (LCP)",
                description=f"{len(large)} images exceed {LARGE_IMAGE_THRESHOLD_KB} KB. Example: {sample['url']} ({sample['size_kb']} KB).",
                suggestion="Compress to WebP. Use srcset to serve smaller images on mobile. Target < 100 KB per image.",
                confidence="HIGH",
                location=sample["url"],
            ))

    # ── Modern format check ───────────────────────────────────────────────────
    legacy_imgs = [r for r in results
                   if re.search(r"\.(jpe?g|png|gif|bmp)(\?.*)?$", r["url"], re.IGNORECASE)]
    if legacy_imgs:
        issues.append(Issue(
            category="Performance",
            title=f"Images Not Using Modern Formats ({len(legacy_imgs)} JPEG/PNG/GIF)",
            severity="LOW",
            impact="JPEG/PNG files are 25–50% larger than equivalent WebP/AVIF images",
            description=f"{len(legacy_imgs)} images use legacy formats (JPEG/PNG/GIF).",
            suggestion="Convert images to WebP or AVIF. Use <picture> with <source type='image/webp'> for progressive enhancement.",
            confidence="HIGH",
        ))

    return issues


def _is_decorative(img) -> bool:
    """Heuristic: icon/logo/spacer images are likely decorative."""
    src = img.get("src", "").lower()
    cls = " ".join(img.get("class", [])).lower()
    return any(kw in src or kw in cls
               for kw in ["icon", "logo", "spacer", "separator", "divider"])
