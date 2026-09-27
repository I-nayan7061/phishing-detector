"""
Phishing Email Predictor CLI
=============================
Run inference on single emails, files, or in interactive mode using the trained model.

Usage:
    python predict.py --text "Dear user, update your password at http://fake-login.com"
    python predict.py --file email_sample.txt
    python predict.py --interactive
"""

import argparse
import os
import sys
import joblib

# Import clean_text from training script to ensure identical feature preprocessing
from phishing_svm_classifier import clean_text


def load_model(model_path: str = "phishing_detector_model.joblib"):
    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"Trained model '{model_path}' not found! "
            f"Please run 'python phishing_svm_classifier.py' first to train and save the model."
        )
    return joblib.load(model_path)


def analyze_email(pipeline, text: str):
    cleaned = clean_text(text)
    pred = pipeline.predict([cleaned])[0]
    prob = pipeline.predict_proba([cleaned])[0][1]

    # Heuristic indicators for explanation
    indicators = []
    lower = text.lower()
    if any(k in lower for k in ["http://", "https://", "www.", ".ru", ".xyz", ".top", ".tk"]):
        indicators.append("Contains hyperlinks / URLs")
    if any(k in lower for k in ["urgent", "immediately", "account suspended", "suspended", "action required", "locked"]):
        indicators.append("High urgency / fear inducement language")
    if any(k in lower for k in ["password", "credential", "ssn", "social security", "pin", "verify your identity", "login"]):
        indicators.append("Requests sensitive credentials or verification")
    if any(k in lower for k in ["$", "usd", "wire transfer", "bitcoin", "crypto", "won", "lottery", "prize", "million"]):
        indicators.append("Financial / monetary lure detected")

    verdict = "PHISHING" if pred == 1 else "LEGITIMATE"
    confidence = prob if pred == 1 else (1.0 - prob)

    return {
        "verdict": verdict,
        "phishing_probability": prob,
        "confidence": confidence,
        "indicators": indicators,
    }


def print_result(result: dict, text_preview: str = ""):
    if text_preview:
        preview = text_preview.strip().replace("\n", " ")
        if len(preview) > 120:
            preview = preview[:117] + "..."
        print(f"\nEmail: \"{preview}\"")

    verdict = result["verdict"]
    prob = result["phishing_probability"]
    conf = result["confidence"]

    print("-" * 50)
    if verdict == "PHISHING":
        print(f"VERDICT      : [!] PHISHING DETECTED")
        print(f"RISK LEVEL   : CRITICAL ({prob*100:.2f}% Phishing Probability)")
    else:
        print(f"VERDICT      : [OK] LEGITIMATE / SAFE")
        print(f"RISK LEVEL   : LOW ({prob*100:.2f}% Phishing Probability)")

    print(f"CONFIDENCE   : {conf*100:.2f}%")

    if result["indicators"]:
        print("DETECTED SIGNALS:")
        for ind in result["indicators"]:
            print(f"  * {ind}")
    else:
        print("DETECTED SIGNALS: None of common suspicious keywords flagged")
    print("-" * 50)


def interactive_mode(pipeline):
    print("\n" + "=" * 55)
    print("      Phishing Email Detection - Interactive Shell")
    print("=" * 55)
    print("Type or paste email text. Press Enter, then type 'EOF' on a new line.")
    print("Type 'exit' or 'quit' to quit.\n")

    while True:
        try:
            line = input("Enter email (or 'quit' to exit): ")
            if line.strip().lower() in ["quit", "exit"]:
                print("Exiting...")
                break
            if not line.strip():
                continue

            # Check if multi-line input requested
            lines = [line]
            if not line.strip().endswith("."):
                print("Continue typing body (enter blank line or 'EOF' when done):")
                while True:
                    next_line = input()
                    if next_line.strip() == "EOF" or next_line == "":
                        break
                    lines.append(next_line)

            full_text = "\n".join(lines)
            res = analyze_email(pipeline, full_text)
            print_result(res, full_text)
            print()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            break


def main():
    parser = argparse.ArgumentParser(description="Predict if an email is Phishing or Legitimate")
    parser.add_argument("--model", default="phishing_detector_model.joblib", help="Path to trained model")
    parser.add_argument("--text", type=str, help="Raw email text to analyze")
    parser.add_argument("--file", type=str, help="Path to text file containing an email")
    parser.add_argument("--interactive", "-i", action="store_true", help="Launch interactive testing console")
    args = parser.parse_args()

    pipeline = load_model(args.model)

    if args.interactive:
        interactive_mode(pipeline)
    elif args.file:
        if not os.path.exists(args.file):
            print(f"Error: File '{args.file}' not found.")
            sys.exit(1)
        with open(args.file, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        res = analyze_email(pipeline, content)
        print_result(res, content)
    elif args.text:
        res = analyze_email(pipeline, args.text)
        print_result(res, args.text)
    else:
        # Default demo check if no arguments supplied
        demo_text = (
            "URGENT: Your bank account will be closed in 24 hours unless you verify your identity! "
            "Please click the link below immediately: http://update-secure-banking-support.com"
        )
        print("No input provided. Running demonstration on sample email:")
        res = analyze_email(pipeline, demo_text)
        print_result(res, demo_text)
        print("\nTip: Use --text \"<email content>\", --file <path>, or --interactive")


if __name__ == "__main__":
    main()
