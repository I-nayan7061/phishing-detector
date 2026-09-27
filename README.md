# Phishing Email Detector (Machine Learning)

A high-performance machine learning system for detecting phishing emails with **99.3%+ accuracy** and **0.999+ ROC-AUC**, trained on combined datasets (`CEAS_08` and `Phishing_Email`).

---

## 📊 Dataset & Model Overview

- **Datasets Used**:
  - `CEAS_08.csv`: 39,154 emails (`subject`, `body`, binary labels)
  - `Phishing_Email.csv`: 18,650 emails (`Email Text`, `Email Type`)
- **Total Deduplicated Samples**: **56,667 emails** (Balanced ~50% legitimate, ~50% phishing).
- **ML Architecture**:
  - **Text Preprocessing**: Tokenizes URLs (`URLTOKEN`), emails (`EMAILTOKEN`), IP addresses (`IPTOKEN`), and currency indicators (`MONEYTOKEN`), stripping noise.
  - **Feature Extractor**: `TfidfVectorizer` (sublinear term frequencies, unigrams & bigrams, max 30,000 features).
  - **Classifier**: `LinearSVC` with Platt probability calibration via `CalibratedClassifierCV`.
  - **Performance**:
    - **Accuracy**: `99.33%`
    - **ROC-AUC**: `0.9996`
    - **F1-Score**: `0.993` for both Safe and Phishing classes

---

## 🚀 Quick Start

### 1. Train the Model
To re-train or train the model from scratch on both datasets:
```bash
python phishing_svm_classifier.py
```
This saves `phishing_detector_model.joblib`.

### 2. Predict / Test Emails via CLI
Run prediction on any text:
```bash
python predict.py --text "Urgent: Your account is suspended. Click http://fake-login.com to verify."
```

Or test with an email text file:
```bash
python predict.py --file path/to/email.txt
```

Or start the interactive shell:
```bash
python predict.py --interactive
```

### 3. Launch the Production Web Interface (Custom HTML/CSS/JS + FastAPI)
To launch the full custom cybersecurity web application:
```bash
python server.py
```
Or with Uvicorn:
```bash
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```
Then visit **`http://localhost:8000`** in your browser.
Interactive OpenAPI / Swagger docs are available at **`http://localhost:8000/docs`**.

### 4. Legacy Streamlit Interface (Optional)
To launch the alternative Streamlit app:
```bash
streamlit run app.py
```
