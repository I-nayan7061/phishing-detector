"""
Production-Ready FastAPI Server for Phishing Email & Document Sentinel
======================================================================
Serves REST API endpoints for:
1. Multi-modal document & email file scanning (.eml, .msg, .pdf, .docx, .xlsx, images/OCR, .html, .txt)
2. Manual text/HTML threat prediction with token-level SVM explainability (heatmaps)
3. Deep masked link de-anonymization ("Click Here", buttons, domain mismatches)
4. Anti-evasion sanitization (zero-width characters & hidden HTML)
5. Dataset telemetry, CSV/JSON data ingestion, 1-click model retraining, and rollback
"""

import os
import re
import time
import logging
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional

import joblib
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

# Core classifier and explainability
from phishing_svm_classifier import clean_text, explain_prediction, get_model_coefficients
from security_heuristics import (
    sanitize_evasions,
    analyze_headers,
    inspect_hyperlinks,
    inspect_attachments,
    inspect_url
)
from document_parsers import UniversalDocumentParser, extract_masked_links_from_text_and_html
import dataset_manager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("phishing-sentinel-server")

MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "phishing_detector_model.joblib")
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

app_state: Dict[str, Any] = {
    "model": None,
    "model_loaded_at": None,
    "model_path": MODEL_PATH,
    "dataset_info": {
        "training_samples": "56,000+",
        "architecture": "Calibrated LinearSVC + Sublinear TF-IDF + Heuristic Defense Engine"
    }
}


def load_model_pipeline():
    """Loads and warms up the ML model."""
    if not os.path.exists(MODEL_PATH):
        logger.error(f"Model file not found at: {MODEL_PATH}")
        app_state["model"] = None
        return None

    try:
        logger.info(f"Loading ML pipeline from {MODEL_PATH}...")
        start_t = time.perf_counter()
        model = joblib.load(MODEL_PATH)
        # Warmup
        _ = model.predict_proba([clean_text("warm-up email check")])
        load_duration = (time.perf_counter() - start_t) * 1000
        app_state["model"] = model
        app_state["model_loaded_at"] = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
        logger.info(f"Model successfully loaded and warmed up in {load_duration:.2f}ms.")
        return model
    except Exception as e:
        logger.exception(f"Failed to load ML model: {e}")
        app_state["model"] = None
        return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Phishing Sentinel API...")
    load_model_pipeline()
    yield
    logger.info("Shutting down Phishing Sentinel API...")


app = FastAPI(
    title="Phishing Email & Document Sentinel API",
    description="Universal Multi-Modal Threat Detection & Model Operations Platform.",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Schemas
# ============================================================================

class PredictRequest(BaseModel):
    email_text: str = Field(
        ...,
        min_length=1,
        max_length=500000,
        description="The raw email text, HTML, or message body to analyze.",
        example="Subject: Urgent: Verify your PayPal account now at http://fake-login.xyz"
    )
    sensitivity: Optional[float] = Field(
        0.50,
        ge=0.10,
        le=0.90,
        description="Decision sensitivity threshold (0.35 Strict, 0.50 Balanced, 0.70 Relaxed)."
    )

class IndicatorSignal(BaseModel):
    category: str
    severity: str  # safe, info, warning, danger
    title: str
    description: str

class LinkItem(BaseModel):
    anchor_text: str
    target_url: str
    domain: str
    flags: List[str]
    is_mismatch: bool
    risk_severity: str

class AttachmentItem(BaseModel):
    filename: str
    size_bytes: int
    mime_type: str
    flags: List[str]
    risk_severity: str

class TokenAttribution(BaseModel):
    token: str
    score: float
    type: str

class TopFeature(BaseModel):
    feature: str
    weight: float
    contribution: float
    direction: str

class PredictResponse(BaseModel):
    is_phishing: bool
    verdict: str
    risk_level: str  # SAFE, LOW, MEDIUM, HIGH, CRITICAL
    phishing_probability: float
    confidence: float
    sensitivity_threshold: float
    extracted_urls: List[str]
    inspected_links: List[LinkItem]
    threat_signals: List[IndicatorSignal]
    scanned_attachments: List[AttachmentItem]
    headers_analysis: Optional[Dict[str, Any]] = None
    heatmap_tokens: List[TokenAttribution]
    top_features: List[TopFeature]
    clean_text_preview: str
    processing_time_ms: float
    file_metadata: Optional[Dict[str, Any]] = None


# Curated presets for interactive testing
PRESET_EXAMPLES = [
    {
        "id": "masked_click_here",
        "title": "Masked Link / 'Click Here' Deception",
        "category": "phishing",
        "tag": "Hidden URL",
        "subject": "Urgent: Unrecognized Login from Russia",
        "content": (
            "Subject: Urgent: Unrecognized Login from Russia\n\n"
            "Dear customer,\n\n"
            "We detected an unauthorized sign-in to your bank account from IP 185.220.101.5 (Moscow, Russia).\n\n"
            "If this was not you, please verify your credentials immediately:\n"
            "<a href=\"http://verify-bank-sec.xyz/auth/login\">Click Here to Verify Your Account</a>\n\n"
            "Failure to confirm your identity within 12 hours will lead to account suspension.\n\n"
            "Fraud Prevention Unit"
        )
    },
    {
        "id": "domain_spoof_mismatch",
        "title": "Visible Domain Mismatch Spoofing",
        "category": "phishing",
        "tag": "Spoofed Domain",
        "subject": "Important Security Update for PayPal Users",
        "content": (
            "Subject: Important Security Update for PayPal Users\n\n"
            "Hello,\n\n"
            "To keep your account active, please review our new terms of service:\n"
            "<a href=\"http://paypa1-update.top/security\">https://www.paypal.com/security-update</a>\n\n"
            "Please complete this review today.\n\n"
            "PayPal Security Department"
        )
    },
    {
        "id": "zero_width_evasion",
        "title": "Zero-Width Evasion Technique",
        "category": "phishing",
        "tag": "NLP Evasion",
        "subject": "A​c​c​o​u​n​t S​u​s​p​e​n​d​e​d",
        "content": (
            "Subject: A\u200Bc\u200Bc\u200Bo\u200Bu\u200Bn\u200Bt S\u200Bu\u200Bs\u200Bp\u200Be\u200Bn\u200Bd\u200Be\u200Bd\n\n"
            "Your P\u200Ba\u200Bs\u200Bs\u200Bw\u200Bo\u200Br\u200Bd has expired. Visit http://portal-auth-365.buzz to reset."
        )
    },
    {
        "id": "safe_sprint_retro",
        "title": "Sprint Retrospective Notes",
        "category": "legitimate",
        "tag": "Safe / Work",
        "subject": "Meeting Notes: Sprint 14 Retrospective",
        "content": (
            "Subject: Meeting Notes: Sprint 14 Retrospective\n\n"
            "Hi Team,\n\n"
            "Thanks for attending today's retrospective. Here are the key action items we agreed upon:\n"
            "1. Finish code review for the authentication module by Wednesday.\n"
            "2. Update the staging deployment documentation in the internal wiki.\n"
            "3. Schedule design sync with frontend engineering for next Tuesday.\n\n"
            "Let me know if I missed anything in the summary.\n\n"
            "Best regards,\nSarah Jenkins\nEngineering Team Lead"
        )
    }
]


# ============================================================================
# Core Pipeline Processing Logic
# ============================================================================

def process_threat_scan(
    raw_text: str,
    extracted_links: List[Dict[str, str]] = None,
    headers: Dict[str, str] = None,
    attachments: List[Dict[str, Any]] = None,
    file_metadata: Dict[str, Any] = None,
    sensitivity: float = 0.50
) -> PredictResponse:
    """
    Unified evaluation engine combining:
    1. Anti-evasion sanitization
    2. Deep masked link inspection & domain mismatch checks
    3. Sender identity & header checks (SPF/DKIM/DMARC)
    4. Attachment screening (double extensions, scripts, macros)
    5. Calibrated SVM machine learning inference
    6. Native token-level explainability (heatmaps & top features)
    7. Tunable sensitivity risk scoring
    """
    model = app_state["model"]
    if model is None:
        model = load_model_pipeline()
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Machine learning model is not loaded. Please ensure phishing_detector_model.joblib exists."
        )

    start_t = time.perf_counter()

    # 1. Anti-Evasion Sanitization (Zero-Width & Hidden HTML)
    sanitized_text, evasion_signals = sanitize_evasions(raw_text)

    # 2. Extract and Unmask Hyperlinks
    if extracted_links is None:
        extracted_links = extract_masked_links_from_text_and_html(raw_text)

    inspected_links, link_signals = inspect_hyperlinks(extracted_links)
    all_target_urls = [link["target_url"] for link in inspected_links]

    # 3. Header & Sender Analysis
    header_signals = analyze_headers(headers or {})

    # 4. Attachment Screening
    scanned_attachments, attachment_signals = inspect_attachments(attachments or [], body_text=sanitized_text)

    # Combine all threat heuristic signals
    all_signals = evasion_signals + link_signals + header_signals + attachment_signals

    # 5. Additional Heuristic keyword checks on sanitized text
    lower = sanitized_text.lower()
    urgency_terms = ["urgent", "immediately", "account suspended", "suspended", "action required", "locked", "within 24 hours", "unauthorized access", "terminate"]
    detected_urgency = [w for w in urgency_terms if w in lower]
    if detected_urgency:
        all_signals.append({
            "category": "urgency",
            "severity": "danger" if len(detected_urgency) >= 2 else "warning",
            "title": "Urgency & Coercion Phrasing",
            "description": f"Pressure tactics detected ({', '.join(detected_urgency[:3])}). Attackers use artificial urgency to prevent critical evaluation."
        })

    cred_terms = ["password", "credential", "ssn", "social security", "pin", "verify your identity", "login details", "authenticate"]
    detected_creds = [w for w in cred_terms if w in lower]
    if detected_creds:
        all_signals.append({
            "category": "credential_theft",
            "severity": "danger",
            "title": "Credential Solicitation",
            "description": f"Prompts for sensitive credentials or authentication details ({', '.join(detected_creds[:3])})."
        })

    finance_terms = ["wire transfer", "bitcoin", "crypto", "won", "lottery", "prize", "sweepstakes", "inheritance", "million usd"]
    detected_finance = [w for w in finance_terms if w in lower]
    if detected_finance:
        all_signals.append({
            "category": "financial_lure",
            "severity": "warning",
            "title": "Financial Scam Lure",
            "description": f"High-yield monetary bait identified ({', '.join(detected_finance[:3])})."
        })

    # 6. SVM Inference & Native Explainability
    explanation = explain_prediction(model, sanitized_text, top_k=10, unmasked_urls=all_target_urls)
    ml_prob = explanation["phishing_prob"]

    # 7. Tunable Sensitivity Threshold Evaluation
    is_phishing = bool(ml_prob >= sensitivity)

    # Escalate risk if critical threat signals were detected
    has_critical_danger = any(s["severity"] == "danger" for s in all_signals)
    if has_critical_danger and ml_prob < sensitivity and ml_prob > 0.30:
        is_phishing = True

    # Multi-tier Risk Assessment
    if ml_prob >= 0.80 or (has_critical_danger and ml_prob >= 0.50):
        risk_level = "CRITICAL"
        verdict = "PHISHING DETECTED"
    elif ml_prob >= sensitivity:
        risk_level = "HIGH"
        verdict = "SUSPECTED PHISHING"
    elif ml_prob >= 0.35 or has_critical_danger:
        risk_level = "MEDIUM"
        verdict = "SUSPICIOUS / ELEVATED RISK"
    elif ml_prob >= 0.15:
        risk_level = "LOW"
        verdict = "LIKELY LEGITIMATE"
    else:
        risk_level = "SAFE"
        verdict = "LEGITIMATE / SAFE"

    confidence = ml_prob if is_phishing else (1.0 - ml_prob)
    elapsed_ms = (time.perf_counter() - start_t) * 1000

    clean_preview = clean_text(sanitized_text, unmasked_urls=all_target_urls)
    clean_preview = clean_preview[:160] + ("..." if len(clean_preview) > 160 else "")

    return PredictResponse(
        is_phishing=is_phishing,
        verdict=verdict,
        risk_level=risk_level,
        phishing_probability=round(ml_prob, 4),
        confidence=round(confidence, 4),
        sensitivity_threshold=round(sensitivity, 2),
        extracted_urls=all_target_urls,
        inspected_links=[LinkItem(**l) for l in inspected_links],
        threat_signals=[IndicatorSignal(**s) for s in all_signals],
        scanned_attachments=[AttachmentItem(**a) for a in scanned_attachments],
        headers_analysis=headers if headers else None,
        heatmap_tokens=[TokenAttribution(**t) for t in explanation["heatmap_tokens"]],
        top_features=[TopFeature(**f) for f in explanation["top_features"]],
        clean_text_preview=clean_preview,
        processing_time_ms=round(elapsed_ms, 2),
        file_metadata=file_metadata
    )


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/api/health")
async def health_check():
    """Health check reporting model state and dataset size."""
    if app_state["model"] is None:
        load_model_pipeline()
    is_ready = app_state["model"] is not None
    return {
        "status": "healthy" if is_ready else "degraded",
        "model_loaded": is_ready,
        "model_path": app_state["model_path"],
        "loaded_at": app_state["model_loaded_at"],
        "dataset_info": app_state["dataset_info"],
    }



@app.get("/api/examples")
async def get_examples():
    """Returns preset curated test samples."""
    return {"examples": PRESET_EXAMPLES}


@app.post("/api/predict", response_model=PredictResponse)
async def predict_text(payload: PredictRequest):
    """Analyzes raw email or HTML text."""
    raw = payload.email_text.strip()
    if not raw:
        raise HTTPException(status_code=422, detail="Text cannot be empty.")
    return process_threat_scan(raw, sensitivity=payload.sensitivity or 0.50)


@app.post("/api/scan-file", response_model=PredictResponse)
async def scan_file(
    file: UploadFile = File(...),
    sensitivity: float = Form(0.50)
):
    """
    Universal multi-modal file ingestion endpoint.
    Accepts .eml, .msg, .pdf, .docx, .xlsx, images/OCR, .html, .txt, etc.
    """
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=422, detail="Uploaded file is empty.")

    try:
        parsed = UniversalDocumentParser.parse_file(file_bytes, file.filename)
    except Exception as e:
        logger.exception("Failed parsing document")
        raise HTTPException(status_code=500, detail=f"Document parsing error: {str(e)}")

    content = f"Subject: {parsed.get('subject', '')}\n\n{parsed.get('text', '')}"
    if parsed.get("html"):
        content += "\n\n" + parsed["html"]

    file_meta = {
        "filename": parsed.get("filename"),
        "extension": parsed.get("extension"),
        **parsed.get("metadata", {})
    }

    return process_threat_scan(
        raw_text=content,
        extracted_links=parsed.get("links", []),
        headers=parsed.get("headers", {}),
        attachments=parsed.get("attachments", []),
        file_metadata=file_meta,
        sensitivity=sensitivity
    )


# ============================================================================
# Dataset & Model Operations (MLOps) Endpoints
# ============================================================================

@app.get("/api/dataset/stats")
async def dataset_stats():
    """Live telemetry for Dataset & Model Operations Hub."""
    try:
        stats = dataset_manager.get_dataset_statistics()
        return JSONResponse(content=stats, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})
    except Exception as e:
        logger.exception("Error reading dataset stats")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/dataset/upload")
async def upload_dataset_file(file: UploadFile = File(...)):
    """Uploads and merges new CSV or JSON training data."""
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=422, detail="Empty upload.")

    try:
        result = dataset_manager.ingest_uploaded_data(file_bytes, file.filename)
        return result
    except Exception as e:
        logger.exception("Error ingesting dataset")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/dataset/retrain")
async def retrain_model(max_features: int = 30000):
    """Triggers 1-click model retraining on the current master dataset."""
    try:
        result = dataset_manager.retrain_model_pipeline(max_features=max_features)
        # Reload active model into memory
        load_model_pipeline()
        return result
    except Exception as e:
        logger.exception("Error retraining model")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/dataset/rollback")
async def rollback_model():
    """Restores the previous model version from backup."""
    try:
        result = dataset_manager.rollback_model()
        # Reload active model into memory
        load_model_pipeline()
        return result
    except Exception as e:
        logger.exception("Error rolling back model")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/feedback")
async def submit_feedback(payload: Dict[str, Any]):
    """Receives active learning human-labeled feedback."""
    text = payload.get("text", "").strip()
    label = payload.get("label")
    if not text or label not in [0, 1]:
        raise HTTPException(status_code=422, detail="Invalid feedback payload.")

    try:
        # Append single row to master dataset
        df = dataset_manager.ensure_master_dataset()
        new_row = pd.DataFrame([{
            "text": text,
            "label": int(label),
            "clean_text": clean_text(text)
        }])
        df = pd.concat([df, new_row], ignore_index=True).drop_duplicates(subset=["text"])
        df.to_csv(dataset_manager.MASTER_DATASET_PATH, index=False)
        return {"status": "success", "message": "Feedback recorded in training pool."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Static Files & SPA Route
# ============================================================================

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
async def serve_index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse(status_code=404, content={"error": "Frontend not found in static/"})


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    logger.info(f"Starting server at http://{host}:{port}")
    uvicorn.run("server:app", host=host, port=port, reload=True)

