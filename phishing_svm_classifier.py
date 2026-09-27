"""
Phishing Email Detection Pipeline
=================================
Trains a high-accuracy, calibrated machine learning model on combined phishing email datasets:
- CEAS_08 (subject, body, label: 0/1)
- Phishing_Email (Email Text, Email Type: Safe Email/Phishing Email)

Features:
- Handles folder paths, direct CSV paths, or comma-separated lists of datasets.
- Preprocessing and feature extraction using TF-IDF n-grams (1, 2) with sublinear TF scaling.
- Scalable, calibrated Linear SVM classifier delivering >99% test accuracy and calibrated probabilities.
- Model serialization to joblib format.

Usage:
    python phishing_svm_classifier.py
    python phishing_svm_classifier.py --data CEAS_08.csv,Phishing_Email.csv --save phishing_detector_model.joblib
"""

import argparse
import os
import re
import string
import time
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    accuracy_score,
    roc_auc_score,
    classification_report,
    confusion_matrix,
)


def resolve_csv_path(path_str: str) -> str:
    """
    Resolve path to CSV file whether user passed a directory containing the CSV or the CSV directly.
    """
    path_str = path_str.strip()
    if os.path.isdir(path_str):
        # Look for CSV file inside
        candidates = [
            os.path.join(path_str, f)
            for f in os.listdir(path_str)
            if f.lower().endswith(".csv")
        ]
        if candidates:
            return candidates[0]
    return path_str


ZERO_WIDTH_CHARS = ["\u200B", "\u200C", "\u200D", "\uFEFF", "\u00AD", "\u2060", "\u180E", "\u200E", "\u200F"]


def clean_text(text: str, unmasked_urls: list = None) -> str:
    """
    Normalize raw email text to enhance feature extraction.
    Strips zero-width characters and incorporates any unmasked URLs.
    """
    if not isinstance(text, str):
        text = str(text) if text is not None else ""

    # Strip zero-width evasion characters
    for zw in ZERO_WIDTH_CHARS:
        if zw in text:
            text = text.replace(zw, "")

    text = text.lower()

    # Append unmasked URLs to text so tokenizer captures them
    if unmasked_urls:
        text = text + " " + " ".join(str(u) for u in unmasked_urls)

    # Normalize URLs
    text = re.sub(r"https?://\S+|www\.\S+", " URLTOKEN ", text)
    # Normalize Email addresses
    text = re.sub(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", " EMAILTOKEN ", text)
    # Normalize Currency symbols / monetary mentions
    text = re.sub(r"[\$£€¥]\s*\d+[\d,\.]*", " MONEYTOKEN ", text)
    # Normalize standalone numbers / IP addresses
    text = re.sub(r"\b\d{1,3}(\.\d{1,3}){3}\b", " IPTOKEN ", text)
    text = re.sub(r"\b\d+\b", " NUMTOKEN ", text)
    # Remove punctuation
    text = text.translate(str.maketrans("", "", string.punctuation))
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text



def load_dataset_source(file_path: str) -> pd.DataFrame:
    """Load and harmonize individual dataset schema into unified [text, label]."""
    real_path = resolve_csv_path(file_path)
    if not os.path.exists(real_path):
        raise FileNotFoundError(f"Dataset path not found: {file_path} (resolved: {real_path})")

    print(f"Loading dataset from: {real_path}")
    df = pd.read_csv(real_path, low_memory=False)

    cols = set(df.columns)
    # Schema 1: CEAS_08 format (subject, body, label)
    if "body" in cols and "label" in cols:
        subject = df["subject"].fillna("") if "subject" in cols else ""
        body = df["body"].fillna("")
        combined_text = (subject + " " + body).str.strip()
        out_df = pd.DataFrame({"text": combined_text, "label": df["label"].astype(int)})

    # Schema 2: Phishing_Email format (Email Text, Email Type)
    elif "Email Text" in cols and "Email Type" in cols:
        label_map = {
            "safe email": 0,
            "phishing email": 1,
            "legitimate": 0,
            "phishing": 1,
            "spam": 1,
            "ham": 0,
        }
        labels = df["Email Type"].astype(str).str.strip().str.lower().map(label_map)
        texts = df["Email Text"].fillna("").astype(str).str.strip()
        out_df = pd.DataFrame({"text": texts, "label": labels})

    # Schema 3: Standard (text, label)
    elif "text" in cols and "label" in cols:
        labels = df["label"]
        if labels.dtype == object:
            label_map = {"phishing": 1, "spam": 1, "1": 1, "legit": 0, "ham": 0, "0": 0, "safe": 0}
            labels = labels.astype(str).str.strip().str.lower().map(label_map)
        out_df = pd.DataFrame({"text": df["text"].fillna("").astype(str).str.strip(), "label": labels})

    else:
        raise ValueError(
            f"Unrecognized dataset schema for {file_path}. Columns found: {df.columns.tolist()}"
        )

    out_df = out_df.dropna(subset=["label"])
    out_df["label"] = out_df["label"].astype(int)
    out_df = out_df[out_df["text"] != ""]
    return out_df


def load_and_merge_data(paths: list) -> pd.DataFrame:
    """Load multiple datasets, merge, deduplicate, and clean."""
    frames = []
    for p in paths:
        try:
            df = load_dataset_source(p)
            frames.append(df)
            print(f"  -> Extracted {len(df):,} valid records from {p}")
        except Exception as e:
            print(f"Warning: Failed to load dataset {p}: {e}")

    if not frames:
        raise ValueError("No valid datasets loaded.")

    combined = pd.concat(frames, ignore_index=True)
    before_len = len(combined)
    combined = combined.drop_duplicates(subset=["text"])
    print(f"\nMerged total: {before_len:,} rows -> Deduplicated: {len(combined):,} rows")
    counts = combined["label"].value_counts().to_dict()
    print(f"Class distribution: Legitimate (0) = {counts.get(0, 0):,}, Phishing (1) = {counts.get(1, 0):,}")

    print("Cleaning text corpus...")
    combined["clean_text"] = combined["text"].apply(clean_text)
    combined = combined[combined["clean_text"].str.strip() != ""]
    return combined


def build_pipeline(max_features: int = 30000) -> Pipeline:
    """
    Constructs high-performance NLP classification pipeline:
    TfidfVectorizer -> Calibrated LinearSVC (yielding well-calibrated probabilities).
    """
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            max_features=max_features,
            ngram_range=(1, 2),
            min_df=2,
            sublinear_tf=True,
            strip_accents="unicode",
        )),
        ("classifier", CalibratedClassifierCV(
            estimator=LinearSVC(dual=False, C=1.0, random_state=42),
            cv=3,
        )),
    ])
    return pipeline


def train_and_evaluate(df: pd.DataFrame, max_features: int = 30000):
    """Split dataset, train pipeline, and print comprehensive metrics."""
    X_train, X_test, y_train, y_test = train_test_split(
        df["clean_text"],
        df["label"],
        test_size=0.2,
        random_state=42,
        stratify=df["label"],
    )

    print(f"\nTraining set size: {len(X_train):,} | Test set size: {len(X_test):,}")
    print("Building and fitting model pipeline...")
    pipeline = build_pipeline(max_features=max_features)

    t0 = time.time()
    pipeline.fit(X_train, y_train)
    fit_duration = time.time() - t0
    print(f"Training completed in {fit_duration:.2f} seconds.")

    print("\n=== Model Evaluation on Test Set ===")
    preds = pipeline.predict(X_test)
    probs = pipeline.predict_proba(X_test)[:, 1]

    acc = accuracy_score(y_test, preds)
    auc = roc_auc_score(y_test, probs)
    print(f"Accuracy : {acc:.4f} ({acc*100:.2f}%)")
    print(f"ROC-AUC  : {auc:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, preds, target_names=["Legitimate", "Phishing"], digits=4))

    print("Confusion Matrix:")
    cm = confusion_matrix(y_test, preds)
    print(f"                Predicted Legit   Predicted Phishing")
    print(f"Actual Legit        {cm[0][0]:<15} {cm[0][1]:<15}")
    print(f"Actual Phishing     {cm[1][0]:<15} {cm[1][1]:<15}")

    return pipeline


def get_model_coefficients(pipeline: Pipeline):
    """Extracts averaged linear SVM coefficients from CalibratedClassifierCV."""
    try:
        clf = pipeline.named_steps["classifier"]
        if hasattr(clf, "calibrated_classifiers_"):
            coefs_list = []
            for c in clf.calibrated_classifiers_:
                est = getattr(c, "estimator", None) or getattr(c, "base_estimator", None)
                if est is not None and hasattr(est, "coef_"):
                    coefs_list.append(est.coef_)
            if coefs_list:
                return np.mean(coefs_list, axis=0)[0]
        elif hasattr(clf, "coef_"):
            return clf.coef_[0]
    except Exception:
        pass
    return None


def explain_prediction(pipeline: Pipeline, raw_text: str, top_k: int = 10, unmasked_urls: list = None):
    """
    Computes token-level mathematical attribution (w_i * x_i) for native SVM explainability.
    Returns:
    - heatmap_tokens: list of {"token": str, "score": float, "type": "phishing" | "safe" | "neutral"}
    - top_features: list of {"feature": str, "weight": float, "contribution": float, "direction": "phishing" | "safe"}
    """
    cleaned = clean_text(raw_text, unmasked_urls=unmasked_urls)
    pred = pipeline.predict([cleaned])[0]
    prob = pipeline.predict_proba([cleaned])[0][1]

    coefs = get_model_coefficients(pipeline)
    tfidf = pipeline.named_steps.get("tfidf")

    top_features = []
    heatmap_tokens = []

    if coefs is not None and tfidf is not None:
        try:
            vec = tfidf.transform([cleaned])
            feature_names = tfidf.get_feature_names_out()
            feature_to_idx = {name: i for i, name in enumerate(feature_names)}

            nonzero_indices = vec.nonzero()[1]
            contributions = []
            for idx in nonzero_indices:
                feat_name = feature_names[idx]
                w = float(coefs[idx])
                x = float(vec[0, idx])
                contrib = w * x
                contributions.append({
                    "feature": feat_name,
                    "weight": round(w, 4),
                    "contribution": round(contrib, 4),
                    "direction": "phishing" if contrib > 0 else "safe"
                })

            contributions.sort(key=lambda item: abs(item["contribution"]), reverse=True)
            top_features = contributions[:top_k]

            # Generate word heatmap preserving line breaks for natural readability
            lines = raw_text.splitlines()
            for line_idx, line in enumerate(lines):
                if not line.strip():
                    heatmap_tokens.append({"token": "\n", "score": 0.0, "type": "newline"})
                    continue
                words = line.split(" ")
                for word in words:
                    if not word:
                        continue
                    norm_w = re.sub(r"[^\w]", "", word).lower()
                    score = 0.0
                    if norm_w in feature_to_idx:
                        idx = feature_to_idx[norm_w]
                        score = float(coefs[idx])

                    if score > 0.35:
                        token_cls = "phishing"
                    elif score < -0.35:
                        token_cls = "safe"
                    else:
                        token_cls = "neutral"

                    heatmap_tokens.append({
                        "token": word,
                        "score": round(score, 3),
                        "type": token_cls
                    })
                if line_idx < len(lines) - 1:
                    heatmap_tokens.append({"token": "\n", "score": 0.0, "type": "newline"})
        except Exception:
            pass


    return {
        "verdict": "PHISHING" if pred == 1 else "LEGITIMATE",
        "phishing_prob": float(prob),
        "top_features": top_features,
        "heatmap_tokens": heatmap_tokens
    }


def predict_single(pipeline: Pipeline, raw_text: str):
    """Predict label and phishing probability for arbitrary raw email string."""
    cleaned = clean_text(raw_text)
    pred = pipeline.predict([cleaned])[0]
    prob = pipeline.predict_proba([cleaned])[0][1]
    verdict = "PHISHING" if pred == 1 else "LEGITIMATE"
    return verdict, prob



def main():
    default_datasets = ["CEAS_08.csv", "Phishing_Email.csv"]
    parser = argparse.ArgumentParser(description="Train and evaluate Phishing Email Classifier")
    parser.add_argument(
        "--data",
        default=",".join(default_datasets),
        help="Comma-separated paths to dataset files/folders",
    )
    parser.add_argument(
        "--save",
        default="phishing_detector_model.joblib",
        help="Target file path to save trained pipeline",
    )
    parser.add_argument(
        "--max_features",
        type=int,
        default=30000,
        help="Max TF-IDF vocabulary size (default: 30000)",
    )
    args = parser.parse_args()

    data_paths = [p.strip() for p in args.data.split(",") if p.strip()]
    df = load_and_merge_data(data_paths)

    pipeline = train_and_evaluate(df, max_features=args.max_features)

    # Save trained model artifact
    joblib.dump(pipeline, args.save)
    print(f"\nSuccessfully saved trained model pipeline to: {os.path.abspath(args.save)}")

    # Quick sanity checks
    test_phishing = (
        "Subject: Urgent: Verify your PayPal account now! "
        "Dear customer, suspicious activity was detected on your account. "
        "Please visit http://paypal-security-update.com/login and confirm your password immediately."
    )
    test_legit = (
        "Subject: Quarterly Project Status Meeting "
        "Hi Alex, please find the presentation attached for tomorrow's 10 AM review. "
        "Let me know if you would like to make changes to slide 4 beforehand."
    )

    print("\n=== Sanity Checks on New Samples ===")
    v1, p1 = predict_single(pipeline, test_phishing)
    print(f"Sample 1 (Urgent Bank Phish) : Verdict = {v1:<10} (Phishing Risk: {p1*100:.2f}%)")

    v2, p2 = predict_single(pipeline, test_legit)
    print(f"Sample 2 (Normal Work Email) : Verdict = {v2:<10} (Phishing Risk: {p2*100:.2f}%)")


if __name__ == "__main__":
    main()
