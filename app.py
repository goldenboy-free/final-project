from flask import Flask, request, jsonify, send_file
from main import run_pipeline
import traceback
import json
import os
from datetime import datetime

# Initialize Flask to serve frontend from the "frontend" directory
app = Flask(__name__, static_folder="frontend", static_url_path="")

REPORT_PATH = "reports/final_audit_report.json"


# -----------------------------------
# 🏠 HOME ROUTE (SERVES FRONTEND)
# -----------------------------------
@app.route("/")
def index():
    """Serves the main frontend UI."""
    return app.send_static_file("index.html")


# -----------------------------------
# ❤️ REST API STATUS & HEALTH
# -----------------------------------
@app.route("/api", methods=["GET"])
def api_home():
    return jsonify({
        "status": "running",
        "message": "🚀 AI Website Analyzer API is LIVE",
        "version": "2.0",
        "endpoints": {
            "/api/analyze": "POST → Analyze website",
            "/api/report": "GET → Get latest JSON report",
            "/api/download": "GET → Download JSON report",
            "/api/health": "GET → Server health check"
        }
    })


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })


# -----------------------------------
# 🚀 ANALYZE WEBSITE
# -----------------------------------
@app.route("/api/analyze", methods=["POST"])
def analyze():
    try:
        data = request.get_json()

        # 🔍 Validation
        if not data or "url" not in data:
            return jsonify({
                "status": "error",
                "message": "❌ URL is required"
            }), 400

        url = data["url"].strip()

        if not url.startswith(("http://", "https://")):
            return jsonify({
                "status": "error",
                "message": "❌ Invalid URL format (use http/https)"
            }), 400

        print(f"\n🌐 API Request Received: {url}")

        start_time = datetime.now()

        # 🔥 Run pipeline
        result = run_pipeline(url, show_output=False)

        end_time = datetime.now()

        return jsonify({
            "status": "success",
            "url": url,
            "analysis_time": str(end_time - start_time),
            "total_issues": result.get("total_issues", 0),
            "issues": result.get("issues", []),
            "runtime": result.get("runtime", 0)
        })

    except Exception as e:
        print("❌ API ERROR:", str(e))
        traceback.print_exc()

        return jsonify({
            "status": "error",
            "message": str(e),
            "hint": "Check logs for full traceback"
        }), 500


# -----------------------------------
# 📄 GET LAST REPORT
# -----------------------------------
@app.route("/api/report", methods=["GET"])
def get_report():
    try:
        if not os.path.exists(REPORT_PATH):
            return jsonify({
                "status": "error",
                "message": "⚠️ No report found. Run /api/analyze first."
            }), 404

        with open(REPORT_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        return jsonify({
            "status": "success",
            "data": data
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# -----------------------------------
# 📥 DOWNLOAD REPORT
# -----------------------------------
@app.route("/api/download", methods=["GET"])
def download_report():
    try:
        if not os.path.exists(REPORT_PATH):
            return jsonify({
                "status": "error",
                "message": "⚠️ No report to download"
            }), 404

        return send_file(
            REPORT_PATH,
            as_attachment=True,
            download_name="website_audit_report.json"
        )

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# -----------------------------------
# ❌ GLOBAL ERROR HANDLER
# -----------------------------------
@app.errorhandler(404)
def not_found(e):
    return jsonify({
        "status": "error",
        "message": "Endpoint not found"
    }), 404


@app.errorhandler(500)
def internal_error(e):
    return jsonify({
        "status": "error",
        "message": "Internal server error"
    }), 500


# -----------------------------------
# ▶️ RUN SERVER
# -----------------------------------
if __name__ == "__main__":
    os.makedirs("reports", exist_ok=True)

    print("\n🚀 Starting AI Website Analyzer Flask API...")
    print("📡 Server running at: http://127.0.0.1:5000/")
    print("🖥️  Frontend UI      : http://127.0.0.1:5000/")
    print("📌 Endpoints:")
    print("   POST   /api/analyze")
    print("   GET    /api/report")
    print("   GET    /api/download")
    print("   GET    /api/health\n")

    app.run(debug=True, host="0.0.0.0", port=5000)