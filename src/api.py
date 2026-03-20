# -*- coding: ascii -*-
from __future__ import annotations

import hmac
import os
from flask import Flask, jsonify, request
from threading import Lock

from .ocr.engine import init_ocr
from .pipeline import run_pipeline

app = Flask(__name__)

_OCR = init_ocr()
_OCR_LOCK = Lock()
_API_TOKEN = os.getenv("API_TOKEN", "").strip()


def _run_pipeline(pdf_bytes: bytes):
    with _OCR_LOCK:
        return run_pipeline(pdf_bytes, _OCR)


def _is_authorized() -> bool:
    if not _API_TOKEN:
        return True

    authorization = request.headers.get("Authorization", "").strip()
    scheme, _, token = authorization.partition(" ")

    if scheme.lower() != "bearer" or not token:
        return False

    return hmac.compare_digest(token.strip(), _API_TOKEN)


@app.post("/enel")
def invoice():
    if not _is_authorized():
        return jsonify({"error": "unauthorized"}), 401

    content_type = (request.content_type or "").lower()
    if "application/pdf" not in content_type:
        return jsonify({"error": "only application/pdf is accepted"}), 400
    pdf_bytes = request.get_data()
    if not pdf_bytes:
        return jsonify({"error": "empty body"}), 400
    if not pdf_bytes.startswith(b"%PDF"):
        return jsonify({"error": "invalid pdf"}), 400

    invoice_obj = _run_pipeline(pdf_bytes)
    return jsonify(invoice_obj.to_dict())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
