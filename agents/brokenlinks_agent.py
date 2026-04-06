import asyncio
import os
from agents import (
    content_agent,
    frontend_agent,
    backend_agent,
    seo_agent,
    brokenlinks_agent,
    security_agent,
    grammar_agent
)

REPORTS_DIR = "reports"
os.makedirs(REPORTS_DIR, exist_ok=True)

async def run_pipeline(url):
    print(f"\n🌐 Starting audit for: {url}\n")

    # --------- 1. Content Agent ---------
    content_report = content_agent.run_content_agent(url)
    text_content = "\n".join(content_report.get("text_content", []))
    html_content = content_report.get("raw_html", "")

    # --------- 2. Grammar Agent ---------
    grammar_report = grammar_agent.run_grammar_agent(text_content)
    print("\n✍️ Grammar audit completed")

    # --------- 3. SEO Agent ---------
    seo_report = seo_agent.run_seo_agent(html_content, url)
    print(f"\n📈 SEO AUDIT COMPLETED for {url}")
    print(f"🔴 High   : {seo_report['summary']['high_priority']}")
    print(f"🟠 Medium : {seo_report['summary']['medium_priority']}")
    print(f"🟢 Low    : {seo_report['summary']['low_priority']}")
    print(f"📊 Score  : {seo_report['scores']['after_fix']} / 100")

    # --------- 4. Frontend Agent ---------
    frontend_report = frontend_agent.run_frontend_agent(html_content)
    print("\n🎨 Frontend audit completed")

    # --------- 5. Backend Agent ---------
    backend_report = backend_agent.run_backend_agent(url)
    print("\n⚙️ Backend audit completed")

    # --------- 6. Broken Links Agent ---------
    broken_report = brokenlinks_agent.run_brokenlinks_agent(html_content)
    print("\n🔗 Broken links audit completed")

    # --------- 7. Security Agent ---------
    security_report = security_agent.run_security_agent(url)
    print("\n🔐 Security audit completed")

    # --------- Merge all reports ---------
    final_report = {
        "url": url,
        "content_agent": content_report,
        "grammar_agent": grammar_report,
        "seo_agent": seo_report,
        "frontend_agent": frontend_report,
        "backend_agent": backend_report,
        "brokenlinks_agent": broken_report,
        "security_agent": security_report
    }

    final_path = os.path.join(REPORTS_DIR, "final_audit_report.json")
    with open(final_path, "w", encoding="utf-8") as f:
        import json
        json.dump(final_report, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Full audit completed for {url}")
    print(f"📁 Final report saved: {final_path}")
    return final_report


if __name__ == "__main__":
    url = input("Website URL (with http/https): ").strip()
    if not url.startswith(("http://", "https://")):
        print("❌ Invalid URL")
    else:
        asyncio.run(run_pipeline(url))