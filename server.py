"""
Production-Ready FastAPI Server for Phishing Email Detection
=============================================================
Serves REST API endpoints for model inference and hosts the
HTML/CSS/JS frontend application.

Run with:
    python server.py
or
    uvicorn server:app --host 0.0.0.0 --port 8000 --reload
"""

import os
import re
import time
import logging
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional

import joblib
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

# Import clean_text from training module to preserve pipeline consistency
from phishing_svm_classifier import clean_text

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("phishing-detector-server")

MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "phishing_detector_model.joblib")
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

# Global state for loaded model pipeline
app_state: Dict[str, Any] = {
    "model": None,
    "model_loaded_at": None,
    "model_path": MODEL_PATH,
    "dataset_info": {
        "training_samples": "56,000+",
        "datasets": ["CEAS_08", "Phishing_Email"],
        "accuracy": "99.3%",
        "architecture": "TF-IDF (15,000 features, n-grams 1-2) + LinearSVC (CalibratedClassifierCV)"
    }
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager to load and warm up ML model on startup."""
    logger.info("Initializing Phishing Detector Server...")
    if not os.path.exists(MODEL_PATH):
        logger.error(f"Model file not found at: {MODEL_PATH}")
    else:
        try:
            logger.info(f"Loading ML pipeline from {MODEL_PATH}...")
            start_t = time.perf_counter()
            model = joblib.load(MODEL_PATH)
            # Warm up model with sample text
            _ = model.predict_proba([clean_text("Warm-up email verification")])
            load_duration = (time.perf_counter() - start_t) * 1000
            app_state["model"] = model
            app_state["model_loaded_at"] = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
            logger.info(f"Model successfully loaded and warmed up in {load_duration:.2f}ms.")
        except Exception as e:
            logger.exception(f"Failed to load ML model: {e}")

    yield

    logger.info("Shutting down Phishing Detector Server...")


# FastAPI Application instance
app = FastAPI(
    title="Phishing Email Sentinel API",
    description="High-performance ML API for detecting phishing emails and malicious intent.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for external frontend consumers / microservices
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
        max_length=200000,
        description="The full email text (subject, headers, and/or body) to analyze.",
        example="Subject: Urgent: Your account has been suspended! Verify your login immediately at http://secure-bank-login.xyz"
    )

class IndicatorSignal(BaseModel):
    category: str
    severity: str  # info, warning, danger
    title: str
    description: str

class PredictResponse(BaseModel):
    is_phishing: bool
    verdict: str
    risk_level: str  # SAFE, LOW, MEDIUM, HIGH, CRITICAL
    phishing_probability: float
    confidence: float
    extracted_urls: List[str]
    threat_signals: List[IndicatorSignal]
    clean_text_preview: str
    processing_time_ms: float


# Preset examples
PRESET_EXAMPLES = [
    {
        "id": "urgent_suspension",
        "title": "Urgent: Account Suspension",
        "category": "phishing",
        "tag": "Credential Theft",
        "subject": "Urgent: Your Bank Account Has Been Suspended!",
        "content": (
            "Subject: Urgent: Your Bank Account Has Been Suspended!\n\n"
            "Dear customer,\n\n"
            "We have observed unauthorized login attempts on your account from an unrecognized IP address. "
            "For your security, your account access has been temporarily restricted.\n\n"
            "To restore your account and verify your identity, visit our secure portal immediately:\n"
            "http://verify-secure-bank-login.xyz/auth/login\n\n"
            "Failure to verify within 24 hours will result in permanent account termination.\n\n"
            "Security Team, Customer Protection Dept."
        )
    },
    {
        "id": "lottery_crypto",
        "title": "Crypto / Prize Claim",
        "category": "phishing",
        "tag": "Financial Scam",
        "subject": "CONGRATULATIONS! You won $1,500,000 USD",
        "content": (
            "Subject: CONGRATULATIONS! You won $1,500,000 USD\n\n"
            "Dear Winner,\n\n"
            "You have been selected as the grand winner of the 2026 International Crypto & Grant Sweepstakes. "
            "Your prize fund of $1,500,000 USD has been deposited with our escrow agent.\n\n"
            "To claim your funds, reply with your full legal name, telephone number, and bank wire details to "
            "claim-dept@freemail-international-award.org.\n\n"
            "Do not disclose this notification to anyone for security reasons."
        )
    },
    {
        "id": "fake_doc_share",
        "title": "Shared Payroll Document",
        "category": "phishing",
        "tag": "Link Phishing",
        "subject": "Important: Updated Q3 Employee Bonus & Compensation Plan",
        "content": (
            "Subject: Important: Updated Q3 Employee Bonus & Compensation Plan\n\n"
            "Hello,\n\n"
            "Please review the attached confidential compensation and bonus schedule spreadsheet for this quarter. "
            "You must authenticate with your corporate Microsoft 365 login to access the file:\n\n"
            "http://sharepoint-secure-auth.top/payroll/bonus-review.xlsx\n\n"
            "Please complete this review by end of day.\n\n"
            "Human Resources Department"
        )
    },
    {
        "id": "safe_meeting",
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
    },
    {
        "id": "safe_shipping",
        "title": "Package Shipping Notice",
        "category": "legitimate",
        "tag": "Safe / Order",
        "subject": "Your Order #94821 has shipped",
        "content": (
            "Subject: Your Order #94821 has shipped\n\n"
            "Hello,\n\n"
            "Good news! Your package is on its way. Estimated delivery date is Thursday between 10:00 AM and 2:00 PM.\n\n"
            "You can track delivery progress and manage delivery preferences in your customer account order history.\n\n"
            "Thank you for shopping with us!"
        )
    }
]


# ============================================================================
# Deep Heuristic Analysis Helpers
# ============================================================================
URL_REGEX = re.compile(r"https?://[^\s<>\"']+|www\.[^\s<>\"']+", re.IGNORECASE)
SUSPICIOUS_TLDS = [".xyz", ".top", ".tk", ".ru", ".buzz", ".work", ".click", ".fit", ".ga", ".cf", ".ml"]

def extract_threat_signals(raw_text: str, urls: List[str]) -> List[IndicatorSignal]:
    """Inspects text and extracted URLs for common threat vectors and heuristics."""
    signals: List[IndicatorSignal] = []
    lower = raw_text.lower()

    # 1. URL Analysis
    if urls:
        suspicious_urls = [u for u in urls if any(tld in u.lower() for tld in SUSPICIOUS_TLDS) or "login" in u.lower() or "verify" in u.lower()]
        if suspicious_urls:
            signals.append(IndicatorSignal(
                category="suspicious_link",
                severity="danger",
                title="High-Risk URLs Detected",
                description=f"Found {len(suspicious_urls)} link(s) matching known phishing patterns or suspicious TLDs: {', '.join(suspicious_urls[:3])}"
            ))
        else:
            signals.append(IndicatorSignal(
                category="hyperlink",
                severity="warning",
                title="Hyperlinks Present",
                description=f"Contains {len(urls)} external hyperlink(s). Phishing campaigns frequently redirect users to spoofed web pages."
            ))

    # 2. Urgency & Coercion
    urgency_terms = ["urgent", "immediately", "account suspended", "suspended", "action required", "locked", "within 24 hours", "unauthorized access", "terminate"]
    detected_urgency = [w for w in urgency_terms if w in lower]
    if detected_urgency:
        signals.append(IndicatorSignal(
            category="urgency",
            severity="danger" if len(detected_urgency) >= 2 else "warning",
            title="Urgency / Fear Inducement",
            description=f"Pressure tactics detected ({', '.join(detected_urgency[:3])}). Attackers use artificial urgency to prevent critical evaluation."
        ))

    # 3. Credential Harvesting
    credential_terms = ["password", "credential", "ssn", "social security", "pin", "verify your identity", "login details", "authenticate", "microsoft 365"]
    detected_creds = [w for w in credential_terms if w in lower]
    if detected_creds:
        signals.append(IndicatorSignal(
            category="credential_theft",
            severity="danger",
            title="Credential Solicitation",
            description=f"Email prompts for sensitive credentials or authentication ({', '.join(detected_creds[:3])})."
        ))

    # 4. Financial & Monetary Lures
    financial_terms = ["$", "usd", "wire transfer", "bitcoin", "crypto", "won", "lottery", "prize", "million", "sweepstakes", "inheritance"]
    detected_finance = [w for w in financial_terms if w in lower]
    if detected_finance:
        signals.append(IndicatorSignal(
            category="financial_lure",
            severity="warning",
            title="Financial Incentive / Prize Claim",
            description=f"Monetary keywords identified ({', '.join(detected_finance[:3])}). Often used as social engineering bait."
        ))

    return signals


# ============================================================================
# API Endpoints
# ============================================================================
@app.get("/api/health")
async def health_check():
    """Health check endpoint reporting API and model readiness."""
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
    """Returns curated preset email examples for quick testing."""
    return {"examples": PRESET_EXAMPLES}


@app.post("/api/predict", response_model=PredictResponse)
async def predict_email(payload: PredictRequest):
    """
    Analyzes an email text using the trained SVM ML pipeline
    and deep heuristic security rules.
    """
    model = app_state["model"]
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Machine learning model is not loaded. Please ensure phishing_detector_model.joblib exists."
        )

    raw_text = payload.email_text.strip()
    if not raw_text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Email text cannot be empty."
        )

    start_time = time.perf_counter()

    # Preprocessing
    cleaned = clean_text(raw_text)

    # ML Inference
    try:
        pred = model.predict([cleaned])[0]
        prob_array = model.predict_proba([cleaned])[0]
        phishing_prob = float(prob_array[1])
    except Exception as e:
        logger.exception("Error during model inference")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference error: {str(e)}"
        )

    is_phishing = bool(pred == 1)

    # Extract URLs & heuristics
    urls = URL_REGEX.findall(raw_text)
    signals = extract_threat_signals(raw_text, urls)

    # Determine Risk Tier
    if phishing_prob >= 0.80:
        risk_level = "CRITICAL"
        verdict = "PHISHING DETECTED"
    elif phishing_prob >= 0.55:
        risk_level = "HIGH"
        verdict = "SUSPECTED PHISHING"
    elif phishing_prob >= 0.35:
        risk_level = "MEDIUM"
        verdict = "SUSPICIOUS / ELEVATED RISK"
    elif phishing_prob >= 0.15:
        risk_level = "LOW"
        verdict = "LIKELY LEGITIMATE"
    else:
        risk_level = "SAFE"
        verdict = "LEGITIMATE / SAFE"

    confidence = phishing_prob if is_phishing else (1.0 - phishing_prob)
    elapsed_ms = (time.perf_counter() - start_time) * 1000

    preview = cleaned[:160] + ("..." if len(cleaned) > 160 else "")

    return PredictResponse(
        is_phishing=is_phishing,
        verdict=verdict,
        risk_level=risk_level,
        phishing_probability=round(phishing_prob, 4),
        confidence=round(confidence, 4),
        extracted_urls=urls,
        threat_signals=signals,
        clean_text_preview=preview,
        processing_time_ms=round(elapsed_ms, 2)
    )


# ============================================================================
# Static Files & SPA Route
# ============================================================================
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
async def serve_index():
    """Serves the main frontend Single Page Application."""
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse(
        status_code=404,
        content={"error": "Frontend assets not found in static/ directory."}
    )


# ============================================================================
# Standalone execution
# ============================================================================
if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    logger.info(f"Starting server at http://{host}:{port}")
    uvicorn.run("server:app", host=host, port=port, reload=True)
