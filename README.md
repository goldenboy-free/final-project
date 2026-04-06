# AuditX — AI Website Audit System

<div align="center">

![AuditX](https://img.shields.io/badge/AuditX-v2.0-6366f1?style=for-the-badge&logo=shield&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge)

**A multi-agent AI website audit platform built with Flask.**
Scan any URL for Security, SEO, Performance, Content, and Plagiarism issues — in seconds.

[🚀 Quick Start](#-quick-start) · [📐 Architecture](#-architecture) · [🔌 API Reference](#-api-reference)

</div>

---

## ✨ Features

| Category | Capabilities |
|---|---|
| 🔒 **Security** | XSS risks, CSRF exposure, inline event handlers, sensitive data leaks, unsafe JS links, CORS wildcard |
| 📈 **SEO** | Title & meta analysis, H1/H2 structure, canonical tags, structured data, keyword density |
| ⚡ **Performance** | Response time, caching headers, compression, render-blocking scripts, image count |
| 📝 **Content** | Readability (Flesch), spelling errors, thin content, CTA detection, keyword stuffing |
| 🎨 **Frontend** | Viewport, DOCTYPE, broken images, inline CSS abuse, accessibility labels |
| 🖼 **Image Audit** | Missing alt text, oversized images, broken image URLs, lazy-loading checks |
| 🔍 **Plagiarism** | TF-IDF cosine similarity, exact repetition, n-gram patterns, vocab diversity |
| 🏆 **Severity** | Issues categorized as HIGH / MEDIUM / LOW with actionable suggestions |
| 📄 **Reports** | JSON report saved per scan, downloadable via API |
| 🌗 **Theme** | Dark / Light mode toggle with persistent preference |

---

## 🏗 Architecture

```
fin_project/
├── agents/                     # 7 specialized AI audit agents
│   ├── content_agent.py        # Text quality, readability, CTA, spelling
│   ├── frontend_agent.py       # HTML structure, accessibility, performance
│   ├── security_agent.py       # XSS, CSRF, data exposure, unsafe links
│   ├── seo_agent.py            # Title, meta, canonical, structured data
│   ├── backend_agent.py        # HTTP headers, response time, CORS, leaks
│   ├── plagiarism_agent.py     # TF-IDF similarity, repetition analysis
│   └── image_agent.py          # Image accessibility & optimization
│
├── frontend/                   # Vanilla HTML + CSS + JS
│   ├── index.html              # Main UI
│   ├── styles.css              # Styling (dark/light mode)
│   └── scripts.js              # Frontend logic & API calls
│
├── app.py                      # Flask server — serves frontend + REST API
├── main.py                     # Core pipeline — orchestrates all agents
├── issue_schema.py             # Standardized issue format (Issue class)
├── requirements.txt            # Python dependencies
└── reports/                    # Generated JSON audit reports
```

### Data Flow

```
User → Browser → POST /api/analyze { url }
    → Flask → run_pipeline(url)
        → Content Agent → SEO Agent → Security Agent
        → Frontend Agent → Backend Agent → Plagiarism Agent → Image Agent
    → Collect all issues → Save JSON report
    → JSON response → UI renders dashboard
```

---

## 🚀 Quick Start

### 1. Clone & Enter the Project

```bash
git clone https://github.com/goldenboy-free/final-project.git
cd final-project/fin_project
```

### 2. Create & Activate Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

> **Note**: First run downloads NLTK punkt tokenizer automatically.
> `language-tool-python` downloads a Java grammar tool on first run.

### 4. Start the Server

```bash
python app.py
```

### 5. Open Browser

```
http://localhost:5000
```

The Flask server serves both the frontend UI and the REST API on port **5000**.

---

## 🔌 API Reference

### Health Check

```http
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-04-06 15:30:00"
}
```

### Analyze a URL

```http
POST /api/analyze
Content-Type: application/json

{ "url": "https://example.com" }
```

**Response:**
```json
{
  "status": "success",
  "url": "https://example.com",
  "analysis_time": "0:00:04.213",
  "total_issues": 12,
  "runtime": 4.2,
  "issues": [
    {
      "title": "Missing meta description",
      "category": "SEO",
      "severity": "HIGH",
      "impact": "Poor search visibility",
      "description": "No meta description tag found",
      "suggestion": "Add a compelling meta description under 160 characters"
    }
  ]
}
```

### Get Last Report

```http
GET /api/report
```

Returns the most recent scan report as JSON.

### Download Report

```http
GET /api/download
```

Downloads the latest `website_audit_report.json` file.

---

## 🎯 Issue Severity

Each detected issue is tagged with a severity level:

| Severity | Meaning | Color |
|---|---|---|
| 🔴 **HIGH** | Critical — fix immediately | Red |
| 🟡 **MEDIUM** | Important — should address | Orange |
| 🔵 **LOW** | Minor — nice to fix | Blue |

Issues are grouped by category (Security, SEO, Content, etc.) in the dashboard UI.

---

## 🧰 Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Flask (Python) |
| **Frontend** | Vanilla HTML + CSS + JavaScript |
| **Agents** | BeautifulSoup, requests, NLTK, textstat, scikit-learn, language-tool-python |
| **Reports** | JSON (saved to `reports/` directory) |

---

## 🔮 Future Improvements

- [ ] Real-time streaming scan progress via WebSocket
- [ ] Multi-URL batch scanning
- [ ] Historical trend graphs per domain
- [ ] PDF report generation
- [ ] Email report delivery
- [ ] Headless browser support for JS-rendered pages (Playwright)
- [ ] User authentication & scan history
- [ ] Scheduled recurring scans

---

## 🛠 Development Notes

- Agents raise `Exception` on critical failures — the pipeline catches them gracefully
- The `run_pipeline()` function orchestrates all 7 agents sequentially
- Reports are saved as JSON to the `reports/` directory after each scan
- The Flask app serves the `frontend/` directory as static files
- Dark/light theme preference is saved in `localStorage`

---

<div align="center">

Built with ❤ using **Flask** · **BeautifulSoup** · **NLTK** · **scikit-learn** · **language-tool-python**

</div>
