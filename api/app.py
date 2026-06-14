"""Flask API for AES scoring — 进阶版：多语言、多维输出、批量评分。"""
import sys
import os
import io
import csv
import logging
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from flask import Flask, request, jsonify
from flask_cors import CORS

from src.inference.advanced_predictor import get_advanced_predictor

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

predictor = None


def init_predictor():
    global predictor
    if predictor is None:
        logger.info("Loading models...")
        predictor = get_advanced_predictor(
            en_model_path="models/best_model.pt",
            cn_model_path=os.environ.get("CN_MODEL_PATH", "models/zh_bert/best_model.pt"),
        )
        logger.info("Model loaded successfully")
    return predictor


# ── Error handlers ──────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return jsonify({"success": False, "error": "Endpoint not found"}), 404


@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"success": False, "error": "Method not allowed"}), 405


@app.errorhandler(500)
def internal_error(e):
    logger.error(f"Internal server error: {e}")
    return jsonify({"success": False, "error": "Internal server error"}), 500


# ── Health ──────────────────────────────────────────────────────

@app.route("/api/v1/health", methods=["GET"])
def health():
    en_loaded = predictor is not None and predictor._en_model is not None
    cn_loaded = predictor is not None and predictor._cn_model is not None
    return jsonify({
        "status": "ok",
        "en_model_loaded": en_loaded,
        "cn_model_loaded": cn_loaded,
    })


# ── 单篇评分（升级版） ──────────────────────────────────────────

@app.route("/api/v1/score", methods=["POST"])
def score():
    init_predictor()
    start = time.time()

    if not request.is_json:
        return jsonify({"success": False, "error": "Content-Type must be application/json"}), 400

    data = request.get_json(silent=True)
    if not data or "text" not in data:
        return jsonify({"success": False, "error": "Missing 'text' field"}), 400

    text = data["text"]
    if not isinstance(text, str) or not text.strip():
        return jsonify({"success": False, "error": "Text must be a non-empty string"}), 400

    if len(text) > 10000:
        return jsonify({"success": False, "error": "Text exceeds maximum length (10000 chars)"}), 400

    language = data.get("language", "auto")
    if language not in ("auto", "en", "zh"):
        language = "auto"

    try:
        result = predictor.predict(text, language=language)
    except Exception:
        logger.exception("Prediction failed")
        return jsonify({"success": False, "error": "Prediction failed"}), 500

    if result.get("error"):
        return jsonify({"success": False, "error": result["error"]}), 500

    elapsed = time.time() - start
    logger.info(
        f"Scored [{result['language']}] essay ({len(text)} chars) "
        f"in {elapsed:.2f}s -> {result['score']:.4f}"
    )

    return jsonify({
        "success": True,
        "score": result["score"],
        "scores": result.get("scores", {}),
        "feedback": result.get("feedback", {}),
        "language": result["language"],
        "elapsed_ms": round(elapsed * 1000),
    })


# ── 批量评分 ────────────────────────────────────────────────────

@app.route("/api/v1/batch", methods=["POST"])
def batch_score():
    init_predictor()

    if "file" not in request.files:
        return jsonify({"success": False, "error": "Missing CSV file in 'file' field"}), 400

    file = request.files["file"]
    if not file.filename or not file.filename.endswith(".csv"):
        return jsonify({"success": False, "error": "File must be a CSV"}), 400

    try:
        content = file.read().decode("utf-8")
        reader = csv.DictReader(io.StringIO(content))

        items = []
        for row in reader:
            text = row.get("text", row.get("essay_text", ""))
            if not text or not text.strip():
                continue
            items.append({
                "id": row.get("id", row.get("essay_id", str(len(items)))),
                "text": text.strip(),
                "language": row.get("language", "auto"),
            })

        if not items:
            return jsonify({"success": False, "error": "No valid essays found in CSV"}), 400

        if len(items) > 100:
            return jsonify({"success": False, "error": "Batch limit is 100 essays"}), 400

    except Exception as e:
        return jsonify({"success": False, "error": f"Failed to parse CSV: {str(e)}"}), 400

    total_start = time.time()
    results = []

    for i, item in enumerate(items):
        try:
            result = predictor.predict(item["text"], language=item["language"])
            results.append({
                "id": item["id"],
                "score": result["score"],
                "scores": result.get("scores", {}),
                "language": result["language"],
                "error": result.get("error"),
            })
        except Exception:
            results.append({
                "id": item["id"],
                "score": None,
                "error": "Prediction failed",
            })
        logger.info(f"Batch progress: {i + 1}/{len(items)}")

    total_elapsed = time.time() - total_start
    return jsonify({
        "success": True,
        "total": len(items),
        "completed": len([r for r in results if r.get("error") is None]),
        "elapsed_ms": round(total_elapsed * 1000),
        "results": results,
    })


# ── 模型信息 ────────────────────────────────────────────────────

@app.route("/api/v1/models", methods=["GET"])
def models_info():
    init_predictor()
    info = {
        "en": {
            "name": "bert-base-uncased",
            "version": "v1.0",
            "language": "en",
            "loaded": predictor._en_model is not None if predictor else False,
        },
        "zh": {
            "name": "bert-base-chinese",
            "version": "v1.0",
            "language": "zh",
            "loaded": predictor._cn_model is not None if predictor else False,
        },
    }
    return jsonify({"success": True, "models": info})


# ── Main ────────────────────────────────────────────────────────

def main():
    init_predictor()
    app.run(host="0.0.0.0", port=5000, debug=False)


if __name__ == "__main__":
    main()
