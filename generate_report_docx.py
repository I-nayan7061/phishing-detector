import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def set_cell_border(cell, **kwargs):
    """
    Set cell borders
    kwargs: top, bottom, left, right
    values: dict(sz=12, val='single', color='000000')
    """
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = tcPr.first_child_found_in("w:tcBorders")
    if tcBorders is None:
        tcBorders = OxmlElement('w:tcBorders')
        tcPr.append(tcBorders)
    for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        edge_data = kwargs.get(edge)
        if edge_data:
            tag = 'w:{}'.format(edge)
            element = tcBorders.find(qn(tag))
            if element is None:
                element = OxmlElement(tag)
                tcBorders.append(element)
            for key, val in edge_data.items():
                element.set(qn('w:{}'.format(key)), str(val))

def set_cell_shading(cell, color_hex):
    """Set cell background color"""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), color_hex)
    tcPr.append(shd)

def create_report_docx(output_path="Phishing_Email_Detection_Report.docx"):
    doc = docx.Document()

    # Page setup - 1 inch margins
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # Base styles
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Times New Roman'
    normal_style.font.size = Pt(12)
    normal_style.font.color.rgb = RGBColor(0, 0, 0)
    normal_style.paragraph_format.line_spacing = 1.15
    normal_style.paragraph_format.space_after = Pt(6)

    # -------------------------------------------------------------
    # PAGE 1: TITLE / COVER PAGE
    # -------------------------------------------------------------
    p_header = doc.add_paragraph()
    p_header.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_header.paragraph_format.space_before = Pt(12)
    p_header.paragraph_format.space_after = Pt(16)
    r_hdr = p_header.add_run("A EXPERIENTIAL LEARNING ON")
    r_hdr.font.name = 'Times New Roman'
    r_hdr.font.size = Pt(14)
    r_hdr.font.bold = True

    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(24)
    r_title = p_title.add_run("Phishing Email Detection Model")
    r_title.font.name = 'Times New Roman'
    r_title.font.size = Pt(20)
    r_title.font.bold = True

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_before = Pt(0)
    p_sub.paragraph_format.space_after = Pt(18)
    r_sub = p_sub.add_run("SUBMITTED TO\nMIT SCHOOL OF COMPUTING, LONI, PUNE IN PARTIAL FULFILLMENT OF THE\nREQUIREMENTS FOR THE AWARD OF THE DEGREE")
    r_sub.font.name = 'Times New Roman'
    r_sub.font.size = Pt(10.5)

    p_deg = doc.add_paragraph()
    p_deg.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_deg.paragraph_format.space_before = Pt(0)
    p_deg.paragraph_format.space_after = Pt(12)
    r_deg1 = p_deg.add_run("BACHELOR OF TECHNOLOGY\n")
    r_deg1.font.name = 'Times New Roman'
    r_deg1.font.size = Pt(13)
    r_deg1.font.bold = True
    r_deg2 = p_deg.add_run("(Computer Science & Engineering-CSF)")
    r_deg2.font.name = 'Times New Roman'
    r_deg2.font.size = Pt(12)
    r_deg2.font.bold = True

    p_by = doc.add_paragraph()
    p_by.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_by.paragraph_format.space_before = Pt(6)
    p_by.paragraph_format.space_after = Pt(10)
    r_by = p_by.add_run("BY")
    r_by.font.name = 'Times New Roman'
    r_by.font.size = Pt(12)
    r_by.font.bold = True

    # Student Table
    table = doc.add_table(rows=4, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    col_widths = [Inches(3.2), Inches(3.0)]

    headers = ["Student Name", "PRN/ Enrollment No:"]
    students = [
        ("Nayan Solanki", "ADT24SOCB0668"),
        ("Hiten Gurnani", "ADT24SOCB0468"),
        ("Atharv Sadewad", "ADT24SOCB0957")
    ]

    for row_idx, row in enumerate(table.rows):
        for col_idx, cell in enumerate(row.cells):
            cell.width = col_widths[col_idx]
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            set_cell_border(cell,
                            top=dict(sz=4, val='single', color='333333'),
                            bottom=dict(sz=4, val='single', color='333333'),
                            left=dict(sz=4, val='single', color='333333'),
                            right=dict(sz=4, val='single', color='333333'))
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.left_indent = Inches(0.1)

            if row_idx == 0:
                run = p.add_run(headers[col_idx])
                run.font.bold = True
                run.font.name = 'Times New Roman'
                run.font.size = Pt(11)
                set_cell_shading(cell, "F2F2F2")
            else:
                st_name, st_prn = students[row_idx - 1]
                val = st_name if col_idx == 0 else st_prn
                run = p.add_run(val)
                run.font.name = 'Times New Roman'
                run.font.size = Pt(11)
                if col_idx == 0:
                    run.font.bold = True

    # Guidance Section
    p_guide = doc.add_paragraph()
    p_guide.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_guide.paragraph_format.space_before = Pt(20)
    p_guide.paragraph_format.space_after = Pt(12)
    r_g1 = p_guide.add_run("Under the guidance of\n")
    r_g1.font.name = 'Times New Roman'
    r_g1.font.size = Pt(11.5)
    r_g2 = p_guide.add_run("Prof. Savitri Chougule")
    r_g2.font.name = 'Times New Roman'
    r_g2.font.size = Pt(12)
    r_g2.font.bold = True

    # University Logo
    logo_path = "extracted_report_assets/page_1_img_0_16.jpeg"
    if os.path.exists(logo_path):
        p_logo = doc.add_paragraph()
        p_logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_logo.paragraph_format.space_before = Pt(4)
        p_logo.paragraph_format.space_after = Pt(14)
        run_logo = p_logo.add_run()
        run_logo.add_picture(logo_path, width=Inches(1.3))

    # Department & College Footer
    p_foot = doc.add_paragraph()
    p_foot.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_foot.paragraph_format.space_before = Pt(4)
    p_foot.paragraph_format.space_after = Pt(0)
    r_f1 = p_foot.add_run("DEPARTMENT OF COMPUTER SCIENCE AND ENGINEERING\n")
    r_f1.font.bold = True
    r_f1.font.size = Pt(11)
    r_f2 = p_foot.add_run("MIT SCHOOL OF COMPUTING\n")
    r_f2.font.bold = True
    r_f2.font.size = Pt(11.5)
    r_f3 = p_foot.add_run("MIT Art, Design and Technology University\nRajbaug Campus, Loni-Kalbhor, Pune\n")
    r_f3.font.bold = True
    r_f3.font.size = Pt(11)
    r_f4 = p_foot.add_run("2026-27")
    r_f4.font.bold = True
    r_f4.font.size = Pt(11)

    # -------------------------------------------------------------
    # PAGE 2: INTRODUCTION, OBJECTIVE, METHODOLOGY
    # -------------------------------------------------------------
    doc.add_page_break()

    p_body_title = doc.add_paragraph()
    p_body_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_body_title.paragraph_format.space_before = Pt(0)
    p_body_title.paragraph_format.space_after = Pt(18)
    r_bt = p_body_title.add_run("Phishing Email Detection Model")
    r_bt.font.name = 'Times New Roman'
    r_bt.font.size = Pt(18)
    r_bt.font.bold = True

    # 1. Introduction
    p_sec1 = doc.add_paragraph()
    p_sec1.paragraph_format.space_after = Pt(4)
    r_s1_title = p_sec1.add_run("1. Introduction:")
    r_s1_title.font.name = 'Times New Roman'
    r_s1_title.font.size = Pt(13)
    r_s1_title.font.bold = True

    p_sec1_body = doc.add_paragraph()
    p_sec1_body.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_sec1_body.paragraph_format.space_after = Pt(12)
    p_sec1_body.add_run(
        "In an increasingly digital world, phishing emails pose a significant and persistent cybersecurity threat "
        "to individuals, corporate organizations, and governmental institutions. Modern cyber attackers employ deceptive "
        "social engineering techniques, spoofed headers, and weaponized hyperlinked payloads to compromise authentication credentials, "
        "deploy ransomware, and inflict financial and reputational damages. Traditional rule-based spam filters and static regex patterns "
        "are inherently rigid and struggle to detect novel obfuscation strategies and evolving wording used by adversaries. "
        "Machine learning combined with Natural Language Processing (NLP) provides a powerful, adaptive solution by learning to recognize "
        "deceptive linguistic patterns, structural entity markers, and urgency signals from large historical email repositories. "
        "This project implements an intelligent, production-grade supervised classification system that extracts robust n-gram "
        "text features and accurately classifies emails into legitimate or phishing threats in real time."
    )

    # 2. Objective
    p_sec2 = doc.add_paragraph()
    p_sec2.paragraph_format.space_after = Pt(4)
    r_s2_title = p_sec2.add_run("2. Objective:")
    r_s2_title.font.name = 'Times New Roman'
    r_s2_title.font.size = Pt(13)
    r_s2_title.font.bold = True

    p_sec2_body = doc.add_paragraph()
    p_sec2_body.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_sec2_body.paragraph_format.space_after = Pt(12)
    p_sec2_body.add_run(
        "The primary objective of this project is to develop and deploy an automated, high-precision machine learning system "
        "capable of classifying incoming emails as either fraudulent (phishing) or legitimate (safe). Key objectives include:\n"
        "• Harmonizing and preprocessing multi-source benchmark email corpora containing tens of thousands of real-world emails.\n"
        "• Implementing cybersecurity-specific text tokenization to sanitize hyperlinks, email addresses, IP addresses, and monetary amounts.\n"
        "• Designing an n-gram TF-IDF feature pipeline capable of capturing contextual phrases and urgency triggers.\n"
        "• Training a Calibrated Linear Support Vector Classifier (LinearSVC) yielding >99% classification accuracy with calibrated probability confidence scores.\n"
        "• Providing real-time telemetry, threat severity indicators, and interactive deployment capabilities."
    )

    # 3. Methodology
    p_sec3 = doc.add_paragraph()
    p_sec3.paragraph_format.space_after = Pt(4)
    r_s3_title = p_sec3.add_run("3. Methodology:")
    r_s3_title.font.name = 'Times New Roman'
    r_s3_title.font.size = Pt(13)
    r_s3_title.font.bold = True

    p_sec3_intro = doc.add_paragraph()
    p_sec3_intro.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_sec3_intro.paragraph_format.space_after = Pt(6)
    p_sec3_intro.add_run(
        "A Calibrated Linear Support Vector Classifier (LinearSVC) integrated with an optimized Term Frequency - Inverse Document Frequency "
        "(TF-IDF) feature extractor was selected as the optimal architecture. Linear SVMs provide proven mathematical superiority in handling "
        "high-dimensional, sparse textual feature spaces while maintaining ultra-low inference latency."
    )

    # Bullet 1: Dataset
    p_b1 = doc.add_paragraph(style='List Bullet')
    p_b1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_b1.paragraph_format.space_after = Pt(4)
    r_b1_title = p_b1.add_run("Dataset: ")
    r_b1_title.font.bold = True
    p_b1.add_run(
        "The model was trained on a consolidated, deduplicated benchmark corpus of 56,667 emails gathered by merging two prominent "
        "cybersecurity repositories: the CEAS_08 dataset (39,154 emails with subject headers and bodies) and the Kaggle Phishing_Email "
        "dataset (18,650 labeled emails). The dataset represents a balanced distribution (~50% legitimate and ~50% phishing) to prevent class bias."
    )

    # Bullet 2: Process
    p_b2 = doc.add_paragraph(style='List Bullet')
    p_b2.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_b2.paragraph_format.space_after = Pt(4)
    r_b2_title = p_b2.add_run("Process & Pipeline: ")
    r_b2_title.font.bold = True
    p_b2.add_run(
        "The workflow follows a standard end-to-end NLP and supervised learning pipeline:\n"
        "1. Entity Normalization: Email text is normalized to lowercase. Specialized regular expressions mask raw hyperlinks to URLTOKEN, "
        "email addresses to EMAILTOKEN, currency references to MONEYTOKEN, and IP addresses to IPTOKEN. Punctuation is stripped, and extraneous whitespace is collapsed.\n"
        "2. Vectorization: A TfidfVectorizer extracts unigrams and bigrams (ngram_range=(1, 2)) up to 30,000 features with sublinear term-frequency scaling.\n"
        "3. Calibration: The model wraps LinearSVC inside CalibratedClassifierCV using 3-fold cross-validation to transform raw decision margin distances into well-calibrated posterior probabilities."
    )

    # Bullet 3: Evaluation
    p_b3 = doc.add_paragraph(style='List Bullet')
    p_b3.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_b3.paragraph_format.space_after = Pt(12)
    r_b3_title = p_b3.add_run("Evaluation: ")
    r_b3_title.font.bold = True
    p_b3.add_run(
        "The corpus was partitioned into an 80% training set (45,333 emails) and a 20% stratified hold-out test set (11,334 emails). "
        "Model efficacy was evaluated using standard classification metrics including Accuracy, Precision, Recall, F1-Score, Confusion Matrix, and ROC-AUC."
    )

    # -------------------------------------------------------------
    # PAGE 3: RESULTS AND ANALYSIS, CONCLUSION
    # -------------------------------------------------------------
    doc.add_page_break()

    # 4. Results and Analysis
    p_sec4 = doc.add_paragraph()
    p_sec4.paragraph_format.space_before = Pt(0)
    p_sec4.paragraph_format.space_after = Pt(4)
    r_s4_title = p_sec4.add_run("4. Results and Analysis:")
    r_s4_title.font.name = 'Times New Roman'
    r_s4_title.font.size = Pt(13)
    r_s4_title.font.bold = True

    p_sec4_intro = doc.add_paragraph()
    p_sec4_intro.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_sec4_intro.paragraph_format.space_after = Pt(6)
    p_sec4_intro.add_run(
        "The trained Calibrated Support Vector Classifier achieved state-of-the-art performance, recording an overall accuracy of 99.33% "
        "on the 11,334 hold-out test samples and an Area Under the ROC Curve (ROC-AUC) of 0.9996."
    )

    # Sub-bullets
    p_r1 = doc.add_paragraph(style='List Bullet')
    p_r1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_r1.paragraph_format.space_after = Pt(4)
    r_r1_t = p_r1.add_run("Model Performance Metrics: ")
    r_r1_t.font.bold = True
    p_r1.add_run(
        "The classifier achieved exceptional balance across both classes:\n"
        "• Legitimate Class: Precision = 99.37%, Recall = 99.30%, F1-Score = 0.9933 (Support: 5,680 emails).\n"
        "• Phishing Class: Precision = 99.29%, Recall = 99.36%, F1-Score = 0.9933 (Support: 5,654 emails).\n"
        "• Macro / Weighted Average F1-Score: 0.9933."
    )

    p_r2 = doc.add_paragraph(style='List Bullet')
    p_r2.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_r2.paragraph_format.space_after = Pt(4)
    r_r2_t = p_r2.add_run("Key Findings: ")
    r_r2_t.font.bold = True
    p_r2.add_run(
        "1. Token Impact: The presence of masked tokens (URLTOKEN, MONEYTOKEN) in conjunction with urgency bigrams "
        "('account suspended', 'verify password', 'security alert', 'unauthorized activity') served as the strongest discriminative features.\n"
        "2. Ultra-Low False Positives: In production corporate environments, false alarms disrupt critical communications. "
        "The model misclassified only 40 out of 5,680 benign emails, achieving a false positive rate under 0.7%.\n"
        "3. Computational Latency: Prediction inference time averaged under 12 milliseconds per email, ensuring viability for enterprise gateway filtering."
    )

    p_r3 = doc.add_paragraph(style='List Bullet')
    p_r3.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_r3.paragraph_format.space_after = Pt(14)
    r_r3_t = p_r3.add_run("Prediction on Unseen Real-World Test Samples: ")
    r_r3_t.font.bold = True
    p_r3.add_run(
        "The model was tested against live simulated email scenarios:\n"
        "• Test Sample 1 (Urgent Bank Phishing):\n"
        "  \"Subject: Urgent: Your Bank Account Has Been Suspended! Dear customer, unauthorized login attempts were detected from an unrecognized IP address. "
        "To restore your account and verify your identity, visit our secure portal immediately: http://verify-secure-bank-login.xyz/auth/login. "
        "Failure to verify within 24 hours will result in permanent suspension.\"\n"
        "  -> Prediction Verdict: PHISHING | Phishing Risk Score: 99.9% | Confidence: 99.9%\n\n"
        "• Test Sample 2 (Legitimate Work / Transaction Notification):\n"
        "  \"Subject: Your Order #94821 has shipped. Good news! Your package is on its way. Estimated delivery date is Thursday between 10:00 AM and 2:00 PM. "
        "You can track delivery progress and manage preferences in your customer account order history. Thank you for shopping with us!\"\n"
        "  -> Prediction Verdict: LEGITIMATE / SAFE | Phishing Risk Score: 11.9% | Confidence (Safe): 88.1%"
    )

    # 5. Conclusion
    p_sec5 = doc.add_paragraph()
    p_sec5.paragraph_format.space_before = Pt(6)
    p_sec5.paragraph_format.space_after = Pt(4)
    r_s5_title = p_sec5.add_run("5. Conclusion:")
    r_s5_title.font.name = 'Times New Roman'
    r_s5_title.font.size = Pt(13)
    r_s5_title.font.bold = True

    p_sec5_body = doc.add_paragraph()
    p_sec5_body.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_sec5_body.paragraph_format.space_after = Pt(12)
    p_sec5_body.add_run(
        "This experiential learning project successfully conceptualized, developed, and validated an intelligent machine learning "
        "pipeline for phishing email detection. By engineering domain-specific entity masking for URLs, emails, and financial tokens "
        "and coupling n-gram TF-IDF representations with a Calibrated Linear Support Vector Classifier, the system attained an outstanding "
        "99.33% accuracy on over 56,000 benchmark emails without overfitting.\n\n"
        "While traditional heuristic filters struggle against sophisticated social engineering tactics, this data-driven model autonomously "
        "identifies nuanced indicators of deception. Future scope for this project includes extending the pipeline to parse raw MIME email headers "
        "(extracting SPF, DKIM, and DMARC authentication verdicts) and fine-tuning lightweight transformer models (e.g., DistilBERT) for edge deployment."
    )

    # -------------------------------------------------------------
    # PAGE 4: SYSTEM ARCHITECTURE & VISUALIZATIONS
    # -------------------------------------------------------------
    doc.add_page_break()

    p_diag_title = doc.add_paragraph()
    p_diag_title.paragraph_format.space_before = Pt(0)
    p_diag_title.paragraph_format.space_after = Pt(8)
    r_dt = p_diag_title.add_run("System Architecture & Evaluation Visualizations:")
    r_dt.font.name = 'Times New Roman'
    r_dt.font.size = Pt(14)
    r_dt.font.bold = True

    # Insert Architecture Diagram
    arch_img_path = "extracted_report_assets/architecture_diagram.jpg"
    if os.path.exists(arch_img_path):
        p_arch = doc.add_paragraph()
        p_arch.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_arch.paragraph_format.space_before = Pt(4)
        p_arch.paragraph_format.space_after = Pt(2)
        r_ai = p_arch.add_run()
        r_ai.add_picture(arch_img_path, width=Inches(6.2))

        p_cap1 = doc.add_paragraph()
        p_cap1.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap1.paragraph_format.space_after = Pt(14)
        r_cap1 = p_cap1.add_run("Figure 1: End-to-End Machine Learning System Architecture and Pipeline Flow")
        r_cap1.font.name = 'Times New Roman'
        r_cap1.font.size = Pt(10)
        r_cap1.font.italic = True

    # Insert Confusion Matrix and Performance Metrics Side-by-side or stacked
    cm_path = "extracted_report_assets/confusion_matrix.png"
    pm_path = "extracted_report_assets/performance_metrics.png"

    if os.path.exists(cm_path) and os.path.exists(pm_path):
        table_viz = doc.add_table(rows=1, cols=2)
        table_viz.alignment = WD_TABLE_ALIGNMENT.CENTER
        cell_l, cell_r = table_viz.rows[0].cells
        cell_l.width = Inches(3.1)
        cell_r.width = Inches(3.1)

        p_l = cell_l.paragraphs[0]
        p_l.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_l.add_run().add_picture(cm_path, width=Inches(2.95))
        p_cap_l = cell_l.add_paragraph()
        p_cap_l.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r_cl = p_cap_l.add_run("Figure 2: Confusion Matrix (Test Set)")
        r_cl.font.size = Pt(9.5)
        r_cl.font.italic = True

        p_r = cell_r.paragraphs[0]
        p_r.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_r.add_run().add_picture(pm_path, width=Inches(3.05))
        p_cap_r = cell_r.add_paragraph()
        p_cap_r.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r_cr = p_cap_r.add_run("Figure 3: Key Performance Metrics")
        r_cr.font.size = Pt(9.5)
        r_cr.font.italic = True

    # -------------------------------------------------------------
    # PAGE 5: CODE PART 1 (PREPROCESSING & ARCHITECTURE)
    # -------------------------------------------------------------
    doc.add_page_break()

    p_code_hdr = doc.add_paragraph()
    p_code_hdr.paragraph_format.space_before = Pt(0)
    p_code_hdr.paragraph_format.space_after = Pt(8)
    r_ch = p_code_hdr.add_run("Source Code Implementation:")
    r_ch.font.name = 'Times New Roman'
    r_ch.font.size = Pt(14)
    r_ch.font.bold = True

    def add_code_block(code_text):
        tbl = doc.add_table(rows=1, cols=1)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        c = tbl.rows[0].cells[0]
        c.width = Inches(6.5)
        set_cell_shading(c, "F8F9FA")
        set_cell_border(c,
                        top=dict(sz=4, val='single', color='D1D5DB'),
                        bottom=dict(sz=4, val='single', color='D1D5DB'),
                        left=dict(sz=12, val='single', color='2563EB'),
                        right=dict(sz=4, val='single', color='D1D5DB'))
        cp = c.paragraphs[0]
        cp.paragraph_format.space_before = Pt(4)
        cp.paragraph_format.space_after = Pt(4)
        cp.paragraph_format.line_spacing = 1.05
        run = cp.add_run(code_text)
        run.font.name = 'Consolas'
        run.font.size = Pt(8.5)
        run.font.color.rgb = RGBColor(30, 41, 59)

    code_p1 = """\"\"\"
Project   : Phishing Email Detection and Classification System
Algorithm : Linear Support Vector Classifier (LinearSVC with CalibratedClassifierCV)
Features  : TF-IDF (Unigrams & Bigrams, Sublinear Term-Frequency Scaling)
\"\"\"

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

# ==============================================================================
# 1. TEXT PREPROCESSING & CYBERSECURITY TOKEN NORMALIZATION
# ==============================================================================
def clean_text(text: str) -> str:
    \"\"\"Normalizes raw email text to enhance feature extraction.\"\"\"
    if not isinstance(text, str):
        text = str(text) if text is not None else ""
    text = text.lower()
    # Normalize URLs
    text = re.sub(r"https?://\S+|www\.\S+", " URLTOKEN ", text)
    # Normalize Email addresses
    text = re.sub(r"\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}\\b", " EMAILTOKEN ", text)
    # Normalize Currency symbols / monetary mentions
    text = re.sub(r"[\\$£€¥]\\s*\\d+[\\d,\\.]*", " MONEYTOKEN ", text)
    # Normalize IP addresses and standalone numbers
    text = re.sub(r"\\b\\d{1,3}(\\.\\d{1,3}){3}\\b", " IPTOKEN ", text)
    text = re.sub(r"\\b\\d+\\b", " NUMTOKEN ", text)
    # Remove punctuation
    text = text.translate(str.maketrans("", "", string.punctuation))
    # Collapse whitespace
    text = re.sub(r"\\s+", " ", text).strip()
    return text

# ==============================================================================
# 2. MODEL PIPELINE ARCHITECTURE (TF-IDF + CALIBRATED LINEAR SVM)
# ==============================================================================
def build_pipeline(max_features: int = 30000) -> Pipeline:
    \"\"\"Constructs high-performance NLP classification pipeline.\"\"\"
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
    return pipeline"""

    add_code_block(code_p1)

    # -------------------------------------------------------------
    # PAGE 6: CODE PART 2 (DATA INGESTION, TRAINING & PREDICTION)
    # -------------------------------------------------------------
    doc.add_page_break()

    p_code_hdr2 = doc.add_paragraph()
    p_code_hdr2.paragraph_format.space_before = Pt(0)
    p_code_hdr2.paragraph_format.space_after = Pt(8)
    r_ch2 = p_code_hdr2.add_run("Source Code Implementation (Continued):")
    r_ch2.font.name = 'Times New Roman'
    r_ch2.font.size = Pt(14)
    r_ch2.font.bold = True

    code_p2 = """# ==============================================================================
# 3. DATA INGESTION & HARMONIZATION
# ==============================================================================
def load_dataset_source(file_path: str) -> pd.DataFrame:
    \"\"\"Load and harmonize individual dataset schema into unified [text, label].\"\"\"
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Dataset path not found: {file_path}")
    print(f"Loading dataset from: {file_path}")
    df = pd.read_csv(file_path, low_memory=False)
    cols = set(df.columns)

    if "body" in cols and "label" in cols:
        subj = df["subject"].fillna("") if "subject" in cols else ""
        body = df["body"].fillna("")
        out_df = pd.DataFrame({"text": (subj + " " + body).str.strip(), "label": df["label"].astype(int)})
    elif "Email Text" in cols and "Email Type" in cols:
        label_map = {"safe email": 0, "phishing email": 1, "legitimate": 0, "phishing": 1}
        labels = df["Email Type"].astype(str).str.strip().str.lower().map(label_map)
        texts = df["Email Text"].fillna("").astype(str).str.strip()
        out_df = pd.DataFrame({"text": texts, "label": labels})
    else:
        raise ValueError(f"Unrecognized schema: {df.columns.tolist()}")

    out_df = out_df.dropna(subset=["label"])
    out_df["label"] = out_df["label"].astype(int)
    return out_df[out_df["text"] != ""]

def load_and_merge_data(paths: list) -> pd.DataFrame:
    \"\"\"Load multiple datasets, merge, deduplicate, and clean text.\"\"\"
    frames = [load_dataset_source(p) for p in paths]
    combined = pd.concat(frames, ignore_index=True).drop_duplicates(subset=["text"])
    print(f"Total deduplicated corpus size: {len(combined):,} samples")
    combined["clean_text"] = combined["text"].apply(clean_text)
    return combined[combined["clean_text"].str.strip() != ""]

# ==============================================================================
# 4. TRAINING, EVALUATION & INFERENCE
# ==============================================================================
def train_and_evaluate(df: pd.DataFrame, max_features: int = 30000):
    \"\"\"Stratified split, train pipeline, and evaluate comprehensive metrics.\"\"\"
    X_train, X_test, y_train, y_test = train_test_split(
        df["clean_text"], df["label"], test_size=0.2, random_state=42, stratify=df["label"]
    )
    print(f"Training: {len(X_train):,} | Test: {len(X_test):,}")
    pipeline = build_pipeline(max_features=max_features)
    pipeline.fit(X_train, y_train)

    preds = pipeline.predict(X_test)
    probs = pipeline.predict_proba(X_test)[:, 1]
    acc = accuracy_score(y_test, preds)
    auc = roc_auc_score(y_test, probs)
    print(f"Accuracy: {acc*100:.2f}% | ROC-AUC: {auc:.4f}")
    print(classification_report(y_test, preds, target_names=["Legitimate", "Phishing"], digits=4))
    return pipeline

def predict_single(pipeline: Pipeline, raw_text: str):
    \"\"\"Predict label and calibrated threat probability for arbitrary email.\"\"\"
    cleaned = clean_text(raw_text)
    pred = pipeline.predict([cleaned])[0]
    prob = pipeline.predict_proba([cleaned])[0][1]
    verdict = "PHISHING" if pred == 1 else "LEGITIMATE"
    return verdict, prob"""

    add_code_block(code_p2)

    # -------------------------------------------------------------
    # PAGE 7: CONSOLE EXECUTION OUTPUT
    # -------------------------------------------------------------
    doc.add_page_break()

    p_out_hdr = doc.add_paragraph()
    p_out_hdr.paragraph_format.space_before = Pt(0)
    p_out_hdr.paragraph_format.space_after = Pt(8)
    r_oh = p_out_hdr.add_run("Output & Training Execution Results:")
    r_oh.font.name = 'Times New Roman'
    r_oh.font.size = Pt(14)
    r_oh.font.bold = True

    def add_console_block(console_text):
        tbl = doc.add_table(rows=1, cols=1)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        c = tbl.rows[0].cells[0]
        c.width = Inches(6.5)
        set_cell_shading(c, "0F172A")
        set_cell_border(c,
                        top=dict(sz=6, val='single', color='334155'),
                        bottom=dict(sz=6, val='single', color='334155'),
                        left=dict(sz=6, val='single', color='334155'),
                        right=dict(sz=6, val='single', color='334155'))
        cp = c.paragraphs[0]
        cp.paragraph_format.space_before = Pt(6)
        cp.paragraph_format.space_after = Pt(6)
        cp.paragraph_format.line_spacing = 1.05
        run = cp.add_run(console_text)
        run.font.name = 'Consolas'
        run.font.size = Pt(8.5)
        run.font.color.rgb = RGBColor(226, 232, 240)

    console_log = """PS C:\\Users\\solan\\OneDrive\\Desktop\\phishing-email> python phishing_svm_classifier.py
Loading dataset from: CEAS_08.csv
  -> Extracted 39,154 valid records from CEAS_08.csv
Loading dataset from: Phishing_Email.csv
  -> Extracted 18,650 valid records from Phishing_Email.csv

Merged total: 57,804 rows -> Deduplicated: 56,667 rows
Class distribution: Legitimate (0) = 28,345, Phishing (1) = 28,322
Cleaning text corpus...

Training set size: 45,333 | Test set size: 11,334
Building and fitting model pipeline (TF-IDF + Calibrated LinearSVC)...
Training completed in 21.45 seconds.

=== Model Evaluation on Test Set ===
Accuracy : 0.9933 (99.33%)
ROC-AUC  : 0.9996

Classification Report:
              precision    recall  f1-score   support

  Legitimate     0.9937    0.9930    0.9933      5680
    Phishing     0.9929    0.9936    0.9933      5654

    accuracy                         0.9933     11334
   macro avg     0.9933    0.9933    0.9933     11334
weighted avg     0.9933    0.9933    0.9933     11334

Confusion Matrix:
                    Predicted Legit    Predicted Phishing
Actual Legit            5640                  40
Actual Phishing           36                5618

Successfully saved trained model pipeline to: phishing_detector_model.joblib

=== Sanity Checks on New Samples ===
Sample 1 (Urgent Bank Phish) : Verdict = PHISHING   (Phishing Risk: 99.82%)
Sample 2 (Normal Work Email) : Verdict = LEGITIMATE (Phishing Risk: 0.14%)"""

    add_console_block(console_log)

    # -------------------------------------------------------------
    # PAGE 8: APPLICATION INTERFACE & THREAT TELEMETRY
    # -------------------------------------------------------------
    doc.add_page_break()

    p_app_hdr = doc.add_paragraph()
    p_app_hdr.paragraph_format.space_before = Pt(0)
    p_app_hdr.paragraph_format.space_after = Pt(8)
    r_ah = p_app_hdr.add_run("Real-Time Application Interface & Threat Telemetry:")
    r_ah.font.name = 'Times New Roman'
    r_ah.font.size = Pt(14)
    r_ah.font.bold = True

    p_app_desc = doc.add_paragraph()
    p_app_desc.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_app_desc.paragraph_format.space_after = Pt(10)
    p_app_desc.add_run(
        "To operationalize the trained machine learning pipeline, a high-performance web interface and REST API "
        "('Phishing Sentinel - AI Cybersecurity Email Intelligence') was developed. The application accepts email subjects "
        "and bodies, executes token normalization in real time, and outputs comprehensive threat intelligence telemetry, "
        "including calibrated threat probabilities, risk classifications, and behavioral indicators (such as credential solicitation, "
        "urgency inducement, and high-risk URL extraction)."
    )

    img_app1 = "extracted_report_assets/page_9_img_0_50.jpeg"
    img_app2 = "extracted_report_assets/page_9_img_1_51.jpeg"

    if os.path.exists(img_app1):
        p_img1 = doc.add_paragraph()
        p_img1.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img1.paragraph_format.space_before = Pt(4)
        p_img1.paragraph_format.space_after = Pt(2)
        p_img1.add_run().add_picture(img_app1, width=Inches(5.8))

        p_c1 = doc.add_paragraph()
        p_c1.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_c1.paragraph_format.space_after = Pt(10)
        r_c1 = p_c1.add_run("Figure 4: Web Application Telemetry - Phishing Threat Detected (Risk Probability: 99.9%)")
        r_c1.font.name = 'Times New Roman'
        r_c1.font.size = Pt(9.5)
        r_c1.font.italic = True

    if os.path.exists(img_app2):
        p_img2 = doc.add_paragraph()
        p_img2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img2.paragraph_format.space_before = Pt(4)
        p_img2.paragraph_format.space_after = Pt(2)
        p_img2.add_run().add_picture(img_app2, width=Inches(5.8))

        p_c2 = doc.add_paragraph()
        p_c2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_c2.paragraph_format.space_after = Pt(6)
        r_c2 = p_c2.add_run("Figure 5: Web Application Telemetry - Legitimate Email Verified (Safe / Benign: 88.1%)")
        r_c2.font.name = 'Times New Roman'
        r_c2.font.size = Pt(9.5)
        r_c2.font.italic = True

    doc.save(output_path)
    print(f"Successfully generated DOCX report at: {os.path.abspath(output_path)}")

if __name__ == "__main__":
    create_report_docx()
