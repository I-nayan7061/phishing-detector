# Phishing Sentinel — Enterprise AI Threat Detection & MLOps Platform

A high-performance cybersecurity platform for detecting phishing attacks across **emails, documents, and images**, powered by a **Calibrated Linear Support Vector Machine (`LinearSVC`)** with **99.33% accuracy** and **0.9996 ROC-AUC**, combined with a multi-layered cyber threat heuristic defense engine and an interactive **Data & Model Operations Hub (MLOps)**.

---

## 🌟 Key Features

### 1. 🗂️ Universal Multi-Modal Document Ingestion
Directly upload and scan any file format:
- **Email Files**: `.eml`, `.msg` (Microsoft Outlook), `.mbox`
- **PDF Documents**: `.pdf` (extracts text, embedded `/URI` button links, forms)
- **Office Documents**: `.docx`, `.doc`, `.rtf`, `.xlsx`, `.xls`, `.pptx`
- **Images & Screenshots**: `.png`, `.jpg`, `.jpeg`, `.webp`, `.bmp` (OCR extraction)
- **Web & Markup**: `.html`, `.htm`, `.txt`, `.json`

### 2. 🔗 Deep Masked Link & Button Unmasking
- Deconstructs HTML `<a>` tags, `<button>` redirects, Markdown links `[Click Here](url)`, PDF `/URI` annotations, and plaintext URLs.
- **De-masks Hidden Targets**: Unpacks what is actually behind *"Click Here"*, *"Press Here"*, *"Verify Account"*, or *"Download Invoice"*.
- **Domain Mismatch Spoofing**: Detects deceptive links where visible text claims to be a brand (e.g. `https://paypal.com`) while the target secretly redirects to `http://paypa1-update.xyz`.
- Injects unmasked URLs into the SVM pipeline (`URLTOKEN`) so the model evaluates the true destination payload.

### 3. 🛡️ Advanced Anti-Evasion & Security Heuristics
- **Anti-Evasion Sanitizer**: Neutralizes invisible zero-width spaces (`\u200B`, `\u200C`, etc.) and hidden HTML tags (`display:none`, `font-size:0`) used to evade NLP tokenizers, raising high-severity evasion alerts.
- **Sender Identity & Header Spoofing**: Detects Display Name brand impersonation, Reply-To mismatches, and SPF/DKIM/DMARC authentication failures.
- **IDN Homograph & Typosquatting**: Identifies Punycode lookalikes (`xn--`) using Cyrillic/Greek characters and typosquatting against top 20 brands.
- **Attachment Threat Screening**: Detects double extensions (`Invoice.pdf.exe`), scripts, macro documents (`.docm`), and password-protected archives.
- **URL Shortener & IP Redirection**: Flags URL shorteners (`bit.ly`, `tinyurl.com`) and raw numeric IP hostnames.

### 4. 🔍 Explainable AI (XAI) & Word Attribution Heatmap
- Computes exact linear SVM token weights ($w_i \cdot x_i$).
- Highlights words on the UI: **Red badges** for tokens pushing toward Phishing, **Green badges** for legitimate signals.
- Displays the **Top 5 Influential Features** swaying the decision.

### 5. 🎚️ Tunable Sensitivity & Presets
- Adjust detection threshold via live slider or quick-select presets:
  - **Strict / Zero-Trust (0.35)**: Maximum security for executive and finance inboxes.
  - **Balanced (0.50)**: Standard calibrated operating threshold.
  - **Relaxed (0.70)**: High-certainty alerting for noisy environments.

### 6. 📊 Data & Model Operations Hub (MLOps)
- **Live Dataset Telemetry**: Real-time stats on 56,667+ deduplicated emails and class balance.
- **Upload & Ingest New Data**: Drag-and-drop CSV or JSON files with automatic schema mapping (`text`, `label`) and deduplication.
- **One-Click In-Browser Retraining**: Retrains the full pipeline with live execution terminal output and Before vs. After metrics comparison.
- **Safe Rollback**: Revert to previous model backup with a single click.
- **Active Learning**: Human-in-the-loop review buttons for continuous improvement.

---

## 🚀 Quick Start

### 1. Launch the Production Web Application
```bash
python server.py
```
Open **`http://localhost:8000`** in your browser.
API Swagger documentation is available at **`http://localhost:8000/docs`**.

### 2. Run Predictions via CLI
```bash
python predict.py --text "Urgent: Your account is suspended. Click http://fake-login.com to verify."
```
Or run in interactive shell mode:
```bash
python predict.py --interactive
```

### 3. Run Automated Verification Tests
```bash
python test_sentinel_platform.py
```
Runs the 14-test automated verification suite covering parsers, anti-evasion, heuristics, explainability, and REST API endpoints.

---

## 🏗️ Project Architecture

```
phishing-email/
├── server.py                  # Production FastAPI application & REST endpoints
├── phishing_svm_classifier.py  # Model pipeline, TF-IDF, Calibrated LinearSVC & explainability
├── security_heuristics.py     # Anti-evasion, sender spoofing, link & attachment heuristics
├── document_parsers.py        # Universal parser for .eml, .msg, .pdf, .docx, .xlsx, OCR, etc.
├── dataset_manager.py         # MLOps engine: dataset stats, CSV ingestion, retrain & rollback
├── predict.py                 # Terminal command-line prediction tool
├── test_sentinel_platform.py  # Automated 14-point test suite
├── phishing_detector_model.joblib # Calibrated Linear SVM model artifact
├── dataset_master.csv         # Deduplicated master corpus (56,667 records)
├── requirements.txt           # Project dependencies
└── static/                    # Frontend Single Page Application
    ├── index.html             # Dual-tab dashboard (Scanner + Data Hub)
    ├── css/style.css          # Cybersecurity dark-mode styling
    └── js/app.js              # Client-side controller, heatmaps, file uploads
```
