"""
Streamlit Web Application: Phishing Email Detector
===================================================
Run with:
    streamlit run app.py
"""

import os
import joblib
import streamlit as st
from phishing_svm_classifier import clean_text

st.set_page_config(
    page_title="Phishing Email Detector",
    page_icon="🛡️",
    layout="centered",
)

MODEL_PATH = "phishing_detector_model.joblib"


@st.cache_resource
def get_model():
    if not os.path.exists(MODEL_PATH):
        return None
    return joblib.load(MODEL_PATH)


def analyze_text(pipeline, text: str):
    cleaned = clean_text(text)
    pred = pipeline.predict([cleaned])[0]
    prob = pipeline.predict_proba([cleaned])[0][1]

    indicators = []
    lower = text.lower()
    if any(k in lower for k in ["http://", "https://", "www.", ".ru", ".xyz", ".top", ".tk"]):
        indicators.append("Contains URLs / hyperlinks")
    if any(k in lower for k in ["urgent", "immediately", "account suspended", "suspended", "action required", "locked"]):
        indicators.append("Urgency or fear-inducing phrasing")
    if any(k in lower for k in ["password", "credential", "ssn", "social security", "pin", "verify your identity", "login"]):
        indicators.append("Requests sensitive credentials / verification")
    if any(k in lower for k in ["$", "usd", "wire transfer", "bitcoin", "crypto", "won", "lottery", "prize", "million"]):
        indicators.append("Financial incentive / prize claims")

    return {
        "is_phishing": bool(pred == 1),
        "phishing_prob": float(prob),
        "indicators": indicators,
    }


# UI Header
st.title("🛡️ Phishing Email Detector")
st.markdown(
    "Trained on **56,000+ emails** from the **CEAS_08** & **Phishing_Email** datasets with **99.3% accuracy**."
)

model = get_model()

if model is None:
    st.error(
        f"⚠️ Model file `{MODEL_PATH}` not found! Please run the training script first: `python phishing_svm_classifier.py`"
    )
    st.stop()

# Preset examples for convenience
EXAMPLES = {
    "Select an example...": "",
    "🚨 Phishing: Urgent Account Suspension": (
        "Subject: Urgent: Your Bank Account Has Been Suspended!\n\n"
        "Dear customer, we observed suspicious transactions on your account. "
        "Your access is temporarily restricted. Please visit http://verify-secure-bank-login.com "
        "immediately and enter your login details to restore access, otherwise your account will be deleted within 24 hours."
    ),
    "🚨 Phishing: Lottery / Crypto Prize": (
        "Subject: CONGRATULATIONS! You won $1,500,000 USD\n\n"
        "You have been selected as the lucky winner of our international lottery. "
        "To claim your funds, send your full name, phone number, and bank account details to claim-dept@freemail-winner.org."
    ),
    "✅ Legitimate: Team Meeting Follow-up": (
        "Subject: Meeting Notes: Sprint 14 Retrospective\n\n"
        "Hi Team,\n\n"
        "Thanks for attending today's retrospective. Here are the key action items:\n"
        "1. Finish code review for authentication module.\n"
        "2. Update deployment documentation.\n\n"
        "Let me know if I missed anything.\nBest regards,\nSarah"
    ),
    "✅ Legitimate: Shipping Notification": (
        "Subject: Your Order #94821 has shipped\n\n"
        "Hello,\nYour package is on its way! You can track the delivery progress in your order history.\n"
        "Estimated delivery date is Thursday. Thank you for shopping with us."
    ),
}

selected_example = st.selectbox("Quick-fill with an example email:", list(EXAMPLES.keys()))
default_text = EXAMPLES[selected_example]

email_input = st.text_area(
    "Email Content (Subject & Body):",
    value=default_text,
    height=200,
    placeholder="Paste subject and body of the email here...",
)

col1, col2 = st.columns([1, 4])
with col1:
    analyze_btn = st.button("🔍 Analyze Email", type="primary")

if analyze_btn or (email_input and email_input != ""):
    if not email_input.strip():
        st.warning("Please paste or type email content to analyze.")
    else:
        result = analyze_text(model, email_input)
        prob = result["phishing_prob"]
        is_phishing = result["is_phishing"]

        st.markdown("---")
        st.subheader("Analysis Results")

        if is_phishing:
            st.error(f"### 🚨 Warning: High Phishing Risk ({prob*100:.1f}%)")
            st.progress(prob)
            st.markdown(
                "This email exhibits strong characteristics of a malicious phishing attack. **Do not click links or provide credentials.**"
            )
        else:
            st.success(f"### ✅ Looks Safe / Legitimate ({100 - prob*100:.1f}% Safe)")
            st.progress(prob)
            st.markdown(
                "This email appears legitimate based on linguistic patterns and sender structure."
            )

        # Risk breakdown metrics
        m1, m2, m3 = st.columns(3)
        m1.metric("Phishing Probability", f"{prob*100:.2f}%")
        m2.metric("Verdict", "PHISHING" if is_phishing else "LEGITIMATE")
        m3.metric("Confidence", f"{(prob if is_phishing else 1 - prob)*100:.2f}%")

        # Heuristic triggers
        if result["indicators"]:
            st.markdown("#### Detected Risk Factors:")
            for ind in result["indicators"]:
                st.markdown(f"- ⚠️ {ind}")
        else:
            st.markdown("#### Detected Risk Factors:\n- No common high-risk triggers detected.")
