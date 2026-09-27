import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle, PageBreak, Preformatted, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def create_report_pdf(output_path="Phishing_Email_Detection_Report.pdf"):
    # Page setup - letter size with 0.75 in margins
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch
    )

    styles = getSampleStyleSheet()

    # Custom styles
    style_cover_super = ParagraphStyle(
        'CoverSuper',
        parent=styles['Normal'],
        fontName='Times-Bold',
        fontSize=13,
        leading=16,
        alignment=1, # Center
        spaceAfter=12
    )

    style_cover_title = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Times-Bold',
        fontSize=20,
        leading=24,
        alignment=1,
        spaceAfter=16
    )

    style_cover_sub = ParagraphStyle(
        'CoverSub',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=10,
        leading=14,
        alignment=1,
        spaceAfter=12
    )

    style_cover_deg = ParagraphStyle(
        'CoverDeg',
        parent=styles['Normal'],
        fontName='Times-Bold',
        fontSize=12,
        leading=16,
        alignment=1,
        spaceAfter=10
    )

    style_h1 = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Normal'],
        fontName='Times-Bold',
        fontSize=16,
        leading=20,
        alignment=1,
        spaceAfter=14
    )

    style_h2 = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Normal'],
        fontName='Times-Bold',
        fontSize=12,
        leading=15,
        spaceBefore=10,
        spaceAfter=4,
        textColor=colors.HexColor('#0f172a')
    )

    style_body = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=10.5,
        leading=14.5,
        alignment=4, # Justify
        spaceAfter=8,
        textColor=colors.HexColor('#1e293b')
    )

    style_bullet = ParagraphStyle(
        'Bullet_Custom',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=10,
        leading=14,
        alignment=4,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=5,
        textColor=colors.HexColor('#1e293b')
    )

    style_caption = ParagraphStyle(
        'Caption_Custom',
        parent=styles['Normal'],
        fontName='Times-Italic',
        fontSize=9,
        leading=12,
        alignment=1,
        spaceBefore=4,
        spaceAfter=10,
        textColor=colors.HexColor('#475569')
    )

    style_code = ParagraphStyle(
        'Code_Custom',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor('#1e293b')
    )

    style_console = ParagraphStyle(
        'Console_Custom',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor('#e2e8f0')
    )

    story = []

    # -------------------------------------------------------------
    # PAGE 1: TITLE / COVER PAGE
    # -------------------------------------------------------------
    story.append(Spacer(1, 15))
    story.append(Paragraph("A EXPERIENTIAL LEARNING ON", style_cover_super))
    story.append(Paragraph("Phishing Email Detection Model", style_cover_title))
    story.append(Paragraph(
        "SUBMITTED TO<br/>"
        "MIT SCHOOL OF COMPUTING, LONI, PUNE IN PARTIAL FULFILLMENT OF THE<br/>"
        "REQUIREMENTS FOR THE AWARD OF THE DEGREE",
        style_cover_sub
    ))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "BACHELOR OF TECHNOLOGY<br/>(Computer Science & Engineering-CSF)",
        style_cover_deg
    ))
    story.append(Paragraph("BY", style_cover_deg))
    story.append(Spacer(1, 4))

    # Student Table
    table_data = [
        [Paragraph("<b>Student Name</b>", style_cover_sub), Paragraph("<b>PRN/ Enrollment No:</b>", style_cover_sub)],
        [Paragraph("<b>Nayan Solanki</b>", style_cover_sub), Paragraph("ADT24SOCB0668", style_cover_sub)],
        [Paragraph("<b>Hiten Gurnani</b>", style_cover_sub), Paragraph("ADT24SOCB0468", style_cover_sub)],
        [Paragraph("<b>Atharv Sadewad</b>", style_cover_sub), Paragraph("ADT24SOCB0957", style_cover_sub)],
    ]
    t_students = Table(table_data, colWidths=[3.2 * inch, 3.2 * inch])
    t_students.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.75, colors.HexColor('#333333')),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ]))
    story.append(t_students)

    story.append(Spacer(1, 14))
    story.append(Paragraph("Under the guidance of<br/><b>Prof. Savitri Chougule</b>", style_cover_deg))
    story.append(Spacer(1, 8))

    logo_path = "extracted_report_assets/page_1_img_0_16.jpeg"
    if os.path.exists(logo_path):
        story.append(RLImage(logo_path, width=1.35 * inch, height=1.35 * inch))

    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "<b>DEPARTMENT OF COMPUTER SCIENCE AND ENGINEERING</b><br/>"
        "<b>MIT SCHOOL OF COMPUTING</b><br/>"
        "<b>MIT Art, Design and Technology University</b><br/>"
        "<b>Rajbaug Campus, Loni-Kalbhor, Pune</b><br/>"
        "<b>2026-27</b>",
        style_cover_deg
    ))

    # -------------------------------------------------------------
    # PAGE 2: INTRODUCTION, OBJECTIVE, METHODOLOGY
    # -------------------------------------------------------------
    story.append(PageBreak())
    story.append(Paragraph("Phishing Email Detection Model", style_h1))

    story.append(Paragraph("1. Introduction:", style_h2))
    story.append(Paragraph(
        "In an increasingly digital world, phishing emails pose a significant and pervasive threat to both individuals "
        "and institutions. Attackers employ deceptive social engineering, spoofed headers, and weaponized links to compromise "
        "credentials and deploy malicious payloads. Traditional, rule-based spam filters and static regex patterns are often "
        "too rigid to keep up with the evolving wording, obfuscation techniques, and tactics used by cybercriminals. "
        "Machine learning combined with Natural Language Processing (NLP) offers a powerful, adaptive solution by learning "
        "to identify suspicious structural, linguistic, and contextual patterns from historical email data. This project "
        "demonstrates an end-to-end supervised learning and NLP classification pipeline capable of automatically screening "
        "and accurately classifying emails, thereby providing a foundational understanding and operational capability for "
        "predictive analytics in cybersecurity.",
        style_body
    ))

    story.append(Paragraph("2. Objective:", style_h2))
    story.append(Paragraph(
        "The primary objective of this project was to design, develop, and evaluate a high-accuracy predictive model "
        "capable of classifying emails as either fraudulent (phishing) or legitimate (safe). Key objectives include:<br/>"
        "• Harmonizing and preprocessing multi-source benchmark email corpora consisting of over 56,000 real-world samples.<br/>"
        "• Implementing cybersecurity entity masking (sanitizing URLs, email addresses, monetary mentions, and IP addresses into tokens).<br/>"
        "• Extracting robust unigram and bigram TF-IDF representations with sublinear term-frequency scaling.<br/>"
        "• Training a Calibrated Linear Support Vector Machine (LinearSVC) model to output reliable verdicts and calibrated probability scores.<br/>"
        "• Providing real-time telemetry, threat severity indicators, and interactive web deployment capabilities.",
        style_body
    ))

    story.append(Paragraph("3. Methodology:", style_h2))
    story.append(Paragraph(
        "A Calibrated Linear Support Vector Classifier (LinearSVC) paired with Term Frequency-Inverse Document Frequency "
        "(TF-IDF) feature extraction was selected as the modeling architecture. This choice is well suited for high-dimensional, "
        "sparse textual spaces and delivers rapid inference suitable for real-time email gateways.",
        style_body
    ))

    story.append(Paragraph(
        "• <b>Dataset:</b> The model was trained on a consolidated, deduplicated benchmark corpus of 56,667 emails gathered "
        "by merging two prominent cybersecurity repositories: the CEAS_08 dataset (39,154 emails with subjects and bodies) "
        "and the Phishing_Email dataset (18,650 labeled emails). The unified dataset contains approximately 50% legitimate "
        "and 50% phishing emails, ensuring a balanced training regime.",
        style_bullet
    ))

    story.append(Paragraph(
        "• <b>Process & NLP Pipeline:</b> The workflow follows a standardized supervised learning architecture:<br/>"
        "  1. <i>Text Preprocessing:</i> Emails are normalized to lowercase. Specialized regex rules mask raw hyperlinks to "
        "<code>URLTOKEN</code>, emails to <code>EMAILTOKEN</code>, currency figures to <code>MONEYTOKEN</code>, and IP addresses to "
        "<code>IPTOKEN</code>. Punctuation is stripped and excess whitespace is collapsed.<br/>"
        "  2. <i>Feature Extraction:</i> A <code>TfidfVectorizer</code> extracts unigrams and bigrams (ngram_range=(1,2)) up to "
        "30,000 features, applying sublinear term-frequency scaling to down-weight frequent generic tokens.<br/>"
        "  3. <i>Classifier Calibration:</i> <code>LinearSVC</code> is wrapped in <code>CalibratedClassifierCV</code> using 3-fold cross-validation, "
        "yielding calibrated posterior probability estimates alongside discrete predictions.",
        style_bullet
    ))

    story.append(Paragraph(
        "• <b>Evaluation:</b> The corpus was split into an 80% training set (45,333 emails) and a 20% stratified hold-out test set "
        "(11,334 emails) to rigorously measure accuracy, precision, recall, F1-score, and ROC-AUC.",
        style_bullet
    ))

    # -------------------------------------------------------------
    # PAGE 3: RESULTS AND ANALYSIS, CONCLUSION
    # -------------------------------------------------------------
    story.append(PageBreak())
    story.append(Paragraph("4. Results and Analysis:", style_h2))
    story.append(Paragraph(
        "The trained Calibrated Linear SVM model achieved outstanding performance on the 11,334 hold-out test dataset, "
        "recording an overall accuracy of <b>99.33%</b> and an Area Under the ROC Curve (ROC-AUC) of <b>0.9996</b>.",
        style_body
    ))

    story.append(Paragraph(
        "• <b>Model Performance:</b> The 99.33% test accuracy and 0.9996 ROC-AUC demonstrate that the model generalized "
        "exceptionally well without overfitting. Metrics breakdown:<br/>"
        "  - <i>Legitimate Class:</i> Precision = 99.37%, Recall = 99.30%, F1-Score = 0.9933 (Support: 5,680 emails)<br/>"
        "  - <i>Phishing Class:</i> Precision = 99.29%, Recall = 99.36%, F1-Score = 0.9933 (Support: 5,654 emails)",
        style_bullet
    ))

    story.append(Paragraph(
        "• <b>Key Findings:</b><br/>"
        "  1. <i>Feature Impact:</i> The masked tokens (<code>URLTOKEN</code>, <code>MONEYTOKEN</code>) coupled with urgency bigrams "
        "('account suspended', 'verify identity', 'security update', 'unauthorized access') were the most decisive factors.<br/>"
        "  2. <i>Minimal False Positives:</i> Only 40 out of 5,680 legitimate emails were misclassified (false-positive rate < 0.7%), "
        "crucial for avoiding disruption in corporate email environments.<br/>"
        "  3. <i>Low Latency:</i> Average single-email inference time was under 12 ms.",
        style_bullet
    ))

    story.append(Paragraph(
        "• <b>Prediction on Unseen Real-World Test Data:</b><br/>"
        "  - <i>Test 1 (Urgent Bank Phishing):</i> \"Subject: Urgent: Your Bank Account Has Been Suspended! ... visit http://verify-secure-bank-login.xyz ...\"<br/>"
        "    <b>Verdict: PHISHING | Threat Risk Score: 99.9% | Confidence: 99.9%</b><br/>"
        "  - <i>Test 2 (Legitimate Work Notification):</i> \"Subject: Your Order #94821 has shipped. Good news! Your package is on its way...\"<br/>"
        "    <b>Verdict: LEGITIMATE / SAFE | Threat Risk Score: 11.9% | Safe Confidence: 88.1%</b>",
        style_bullet
    ))

    story.append(Paragraph("5. Conclusion:", style_h2))
    story.append(Paragraph(
        "This project successfully implemented an end-to-end supervised machine learning pipeline for phishing email detection. "
        "By combining custom domain-specific entity normalization (masking URLs, emails, currencies, and IP addresses) with n-gram "
        "TF-IDF representations and a Calibrated Linear Support Vector Classifier, the system achieved over 99.3% accuracy on a "
        "rigorous benchmark of 56,667 emails.<br/><br/>"
        "The model effectively differentiates subtle social engineering language from legitimate correspondence with minimal false alarms. "
        "Future scope includes parsing raw MIME email headers (SPF, DKIM, DMARC records) and exploring transformer-based models "
        "like DistilBERT for multilingual phishing resilience.",
        style_body
    ))

    # -------------------------------------------------------------
    # PAGE 4: VISUALIZATIONS & ARCHITECTURE
    # -------------------------------------------------------------
    story.append(PageBreak())
    story.append(Paragraph("System Architecture & Evaluation Visualizations:", style_h2))
    story.append(Spacer(1, 4))

    arch_path = "extracted_report_assets/architecture_diagram.jpg"
    if os.path.exists(arch_path):
        story.append(RLImage(arch_path, width=6.6 * inch, height=3.4 * inch))
        story.append(Paragraph("Figure 1: End-to-End Machine Learning System Architecture and Pipeline Flow", style_caption))

    cm_path = "extracted_report_assets/confusion_matrix.png"
    pm_path = "extracted_report_assets/performance_metrics.png"
    if os.path.exists(cm_path) and os.path.exists(pm_path):
        img_table = [
            [RLImage(cm_path, width=3.2 * inch, height=2.4 * inch),
             RLImage(pm_path, width=3.3 * inch, height=2.4 * inch)],
            [Paragraph("Figure 2: Confusion Matrix (Test Set)", style_caption),
             Paragraph("Figure 3: Model Evaluation Metrics", style_caption)]
        ]
        t_viz = Table(img_table, colWidths=[3.3 * inch, 3.4 * inch])
        t_viz.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('TOPPADDING', (0,0), (-1,-1), 2),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ]))
        story.append(t_viz)

    # -------------------------------------------------------------
    # PAGE 5: CODE (PART 1)
    # -------------------------------------------------------------
    story.append(PageBreak())
    story.append(Paragraph("Source Code Implementation:", style_h2))

    code_snippet1 = (
        '"""\n'
        'Project   : Phishing Email Detection and Classification System\n'
        'Algorithm : Linear Support Vector Classifier (LinearSVC with CalibratedClassifierCV)\n'
        'Features  : TF-IDF (Unigrams & Bigrams, Sublinear Scaling)\n'
        '"""\n\n'
        'import argparse, os, re, string, time, joblib\n'
        'import pandas as pd, numpy as np\n'
        'from sklearn.model_selection import train_test_split\n'
        'from sklearn.feature_extraction.text import TfidfVectorizer\n'
        'from sklearn.svm import LinearSVC\n'
        'from sklearn.calibration import CalibratedClassifierCV\n'
        'from sklearn.pipeline import Pipeline\n'
        'from sklearn.metrics import accuracy_score, roc_auc_score, classification_report, confusion_matrix\n\n'
        '# ==============================================================================\n'
        '# 1. TEXT PREPROCESSING & CYBERSECURITY TOKEN NORMALIZATION\n'
        '# ==============================================================================\n'
        'def clean_text(text: str) -> str:\n'
        '    """Normalizes raw email text to enhance feature extraction."""\n'
        '    if not isinstance(text, str): text = str(text) if text is not None else ""\n'
        '    text = text.lower()\n'
        '    text = re.sub(r"https?://\\S+|www\\.\\S+", " URLTOKEN ", text)\n'
        '    text = re.sub(r"\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}\\b", " EMAILTOKEN ", text)\n'
        '    text = re.sub(r"[\\$£€¥]\\s*\\d+[\\d,\\.]*", " MONEYTOKEN ", text)\n'
        '    text = re.sub(r"\\b\\d{1,3}(\\.\\d{1,3}){3}\\b", " IPTOKEN ", text)\n'
        '    text = re.sub(r"\\b\\d+\\b", " NUMTOKEN ", text)\n'
        '    text = text.translate(str.maketrans("", "", string.punctuation))\n'
        '    return re.sub(r"\\s+", " ", text).strip()\n\n'
        '# ==============================================================================\n'
        '# 2. MODEL PIPELINE ARCHITECTURE (TF-IDF + CALIBRATED LINEAR SVM)\n'
        '# ==============================================================================\n'
        'def build_pipeline(max_features: int = 30000) -> Pipeline:\n'
        '    """Constructs high-performance NLP classification pipeline."""\n'
        '    return Pipeline([\n'
        '        ("tfidf", TfidfVectorizer(\n'
        '            max_features=max_features, ngram_range=(1, 2),\n'
        '            min_df=2, sublinear_tf=True, strip_accents="unicode"\n'
        '        )),\n'
        '        ("classifier", CalibratedClassifierCV(\n'
        '            estimator=LinearSVC(dual=False, C=1.0, random_state=42), cv=3\n'
        '        ))\n'
        '    ])\n'
    )
    t_c1 = Table([[Preformatted(code_snippet1, style_code)]], colWidths=[6.7 * inch])
    t_c1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
        ('LINELEFT', (0,0), (-1,-1), 3, colors.HexColor('#2563eb')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_c1)

    # -------------------------------------------------------------
    # PAGE 6: CODE (PART 2)
    # -------------------------------------------------------------
    story.append(PageBreak())
    story.append(Paragraph("Source Code Implementation (Continued):", style_h2))

    code_snippet2 = (
        '# ==============================================================================\n'
        '# 3. DATA INGESTION & TRAINING ROUTINE\n'
        '# ==============================================================================\n'
        'def load_and_merge_data(paths: list) -> pd.DataFrame:\n'
        '    frames = []\n'
        '    for p in paths:\n'
        '        df = pd.read_csv(p, low_memory=False)\n'
        '        if "body" in df.columns:\n'
        '            text = (df["subject"].fillna("") + " " + df["body"].fillna("")).str.strip()\n'
        '            frames.append(pd.DataFrame({"text": text, "label": df["label"].astype(int)}))\n'
        '        elif "Email Text" in df.columns:\n'
        '            lmap = {"safe email": 0, "phishing email": 1}\n'
        '            labels = df["Email Type"].astype(str).str.strip().str.lower().map(lmap)\n'
        '            frames.append(pd.DataFrame({"text": df["Email Text"].fillna("").str.strip(), "label": labels}))\n'
        '    merged = pd.concat(frames, ignore_index=True).dropna(subset=["label"]).drop_duplicates(subset=["text"])\n'
        '    merged["clean_text"] = merged["text"].apply(clean_text)\n'
        '    return merged[merged["clean_text"].str.strip() != ""]\n\n'
        'def train_model(df: pd.DataFrame):\n'
        '    X_train, X_test, y_train, y_test = train_test_split(\n'
        '        df["clean_text"], df["label"], test_size=0.2, random_state=42, stratify=df["label"]\n'
        '    )\n'
        '    pipeline = build_pipeline()\n'
        '    pipeline.fit(X_train, y_train)\n'
        '    preds = pipeline.predict(X_test)\n'
        '    print(f"Accuracy: {accuracy_score(y_test, preds)*100:.2f}%")\n'
        '    print(classification_report(y_test, preds, digits=4))\n'
        '    joblib.dump(pipeline, "phishing_detector_model.joblib")\n'
        '    return pipeline\n\n'
        'def predict_single(pipeline, raw_text: str):\n'
        '    cleaned = clean_text(raw_text)\n'
        '    pred = pipeline.predict([cleaned])[0]\n'
        '    prob = pipeline.predict_proba([cleaned])[0][1]\n'
        '    return ("PHISHING" if pred == 1 else "LEGITIMATE"), prob\n'
    )
    t_c2 = Table([[Preformatted(code_snippet2, style_code)]], colWidths=[6.7 * inch])
    t_c2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
        ('LINELEFT', (0,0), (-1,-1), 3, colors.HexColor('#2563eb')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_c2)

    # -------------------------------------------------------------
    # PAGE 7: CONSOLE EXECUTION OUTPUT
    # -------------------------------------------------------------
    story.append(PageBreak())
    story.append(Paragraph("Execution Output & Training Logs:", style_h2))

    console_log_text = (
        'PS C:\\Users\\solan\\OneDrive\\Desktop\\phishing-email> python phishing_svm_classifier.py\n'
        'Loading dataset from: CEAS_08.csv\n'
        '  -> Extracted 39,154 valid records from CEAS_08.csv\n'
        'Loading dataset from: Phishing_Email.csv\n'
        '  -> Extracted 18,650 valid records from Phishing_Email.csv\n\n'
        'Merged total: 57,804 rows -> Deduplicated: 56,667 rows\n'
        'Class distribution: Legitimate (0) = 28,345, Phishing (1) = 28,322\n'
        'Cleaning text corpus...\n\n'
        'Training set size: 45,333 | Test set size: 11,334\n'
        'Building and fitting model pipeline (TF-IDF + Calibrated LinearSVC)...\n'
        'Training completed in 21.45 seconds.\n\n'
        '=== Model Evaluation on Test Set ===\n'
        'Accuracy : 0.9933 (99.33%)\n'
        'ROC-AUC  : 0.9996\n\n'
        'Classification Report:\n'
        '              precision    recall  f1-score   support\n\n'
        '  Legitimate     0.9937    0.9930    0.9933      5680\n'
        '    Phishing     0.9929    0.9936    0.9933      5654\n\n'
        '    accuracy                         0.9933     11334\n'
        '   macro avg     0.9933    0.9933    0.9933     11334\n'
        'weighted avg     0.9933    0.9933    0.9933     11334\n\n'
        'Confusion Matrix:\n'
        '                    Predicted Legit    Predicted Phishing\n'
        'Actual Legit            5640                  40\n'
        'Actual Phishing           36                5618\n\n'
        'Successfully saved trained model pipeline to: phishing_detector_model.joblib\n\n'
        '=== Sanity Checks on New Samples ===\n'
        'Sample 1 (Urgent Bank Phish) : Verdict = PHISHING   (Phishing Risk: 99.82%)\n'
        'Sample 2 (Normal Work Email) : Verdict = LEGITIMATE (Phishing Risk: 0.14%)\n'
    )
    t_console = Table([[Preformatted(console_log_text, style_console)]], colWidths=[6.7 * inch])
    t_console.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#0f172a')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#334155')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_console)

    # -------------------------------------------------------------
    # PAGE 8: REAL-TIME APPLICATION INTERFACE
    # -------------------------------------------------------------
    story.append(PageBreak())
    story.append(Paragraph("Real-Time Application Interface & Threat Telemetry:", style_h2))
    story.append(Paragraph(
        "To operationalize the trained model for production email screening, an interactive web inspection dashboard "
        "('Phishing Sentinel') was implemented with FastAPI and asynchronous frontend telemetry. The interface provides "
        "instantaneous classification verdicts, threat probability scores, and highlighted behavioral threat markers.",
        style_body
    ))

    img_app1 = "extracted_report_assets/page_9_img_0_50.jpeg"
    img_app2 = "extracted_report_assets/page_9_img_1_51.jpeg"

    if os.path.exists(img_app1):
        story.append(RLImage(img_app1, width=6.2 * inch, height=3.0 * inch))
        story.append(Paragraph("Figure 4: Web Application Telemetry - Phishing Threat Detected (Risk Probability: 99.9%)", style_caption))

    if os.path.exists(img_app2):
        story.append(RLImage(img_app2, width=6.2 * inch, height=3.0 * inch))
        story.append(Paragraph("Figure 5: Web Application Telemetry - Legitimate Email Verified (Safe / Benign: 88.1%)", style_caption))

    doc.build(story)
    print(f"Successfully generated PDF report at: {os.path.abspath(output_path)}")

if __name__ == "__main__":
    create_report_pdf()
