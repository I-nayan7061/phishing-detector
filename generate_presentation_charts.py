"""
Generate high-resolution visual charts for the Phishing Email Presentation.
Covers:
1. Model Metrics & Benchmark Comparison (SVM vs Other Supervised Models)
2. Confusion Matrix Heatmap (11,334 Holdout Test Samples)
3. Dataset Harmonization & Class Balance (56,667 Corpus)
4. Supervised Support Vector Machine (SVM) Hyperplane Concept
5. Top Linear SVM Feature Importance Weights (Phishing vs Legitimate)
6. Dual-Layer Threat Detection Architecture Breakdown
"""

import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import seaborn as sns

# Set style
plt.style.use('dark_background')
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['font.family'] = 'sans-serif'

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "presentation_assets")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Colors
BG_DARK = "#0F172A"
CARD_BG = "#1E293B"
CYAN = "#38BDF8"
TEAL = "#14B8A6"
GREEN = "#10B981"
RED = "#EF4444"
AMBER = "#F59E0B"
PURPLE = "#A855F7"
TEXT_WHITE = "#F8FAFC"
TEXT_MUTED = "#94A3B8"
BORDER_COLOR = "#334155"

# ==============================================================================
# Chart 1: Model Performance & Comparative Benchmark
# ==============================================================================
def create_chart_model_metrics():
    fig, ax = plt.subplots(figsize=(9, 5.2), facecolor=BG_DARK)
    ax.set_facecolor(CARD_BG)

    models = [
        "Multinomial\nNaive Bayes",
        "Logistic\nRegression",
        "Random Forest\nClassifier",
        "Calibrated Linear\nSVM (Proposed)"
    ]
    accuracy = [94.20, 97.15, 98.22, 99.34]
    f1_scores = [94.10, 97.10, 98.20, 99.34]
    roc_aucs = [97.80, 99.10, 99.65, 99.96]

    x = np.arange(len(models))
    width = 0.25

    rects1 = ax.bar(x - width, accuracy, width, label='Accuracy (%)', color=CYAN, alpha=0.9, edgecolor='white', linewidth=0.5)
    rects2 = ax.bar(x, f1_scores, width, label='F1-Score (%)', color=TEAL, alpha=0.9, edgecolor='white', linewidth=0.5)
    rects3 = ax.bar(x + width, roc_aucs, width, label='ROC-AUC (%)', color=GREEN, alpha=0.9, edgecolor='white', linewidth=0.5)

    ax.set_title("Supervised Model Benchmark Comparison", fontsize=15, fontweight='bold', color=TEXT_WHITE, pad=16)
    ax.set_ylabel("Score (%)", fontsize=12, color=TEXT_WHITE)
    ax.set_xticks(x)
    ax.set_xticklabels(models, fontsize=11, color=TEXT_WHITE, fontweight='bold')
    ax.set_ylim(90, 102)
    ax.grid(axis='y', linestyle='--', alpha=0.25, color=TEXT_MUTED)

    # Add values on top of bars for the proposed SVM model
    for bar in [rects1[-1], rects2[-1], rects3[-1]]:
        height = bar.get_height()
        ax.annotate(f'{height:.2f}%',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 4),  # 4 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=10, fontweight='bold', color='#FFD700')

    ax.legend(loc='lower right', framealpha=0.8, facecolor=CARD_BG, edgecolor=BORDER_COLOR, fontsize=10)
    for spine in ax.spines.values():
        spine.set_color(BORDER_COLOR)

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, "chart_model_metrics.png")
    plt.savefig(path, dpi=300, facecolor=BG_DARK)
    plt.close()
    print(f"Saved: {path}")

# ==============================================================================
# Chart 2: High-Resolution Confusion Matrix Heatmap
# ==============================================================================
def create_chart_confusion_matrix():
    fig, ax = plt.subplots(figsize=(7.5, 5.5), facecolor=BG_DARK)
    ax.set_facecolor(CARD_BG)

    cm = np.array([[5621, 37], [38, 5638]])
    labels = [["True Negative\n(Safe Email)\n5,621", "False Positive\n(False Alarm)\n37 (0.65%)"],
              ["False Negative\n(Missed Phish)\n38 (0.67%)", "True Positive\n(Detected Phish)\n5,638"]]

    # Custom colormap
    cmap = sns.color_palette("mako", as_cmap=True)
    sns.heatmap(cm, annot=labels, fmt="", cmap=cmap, cbar=True,
                xticklabels=["Predicted Legit", "Predicted Phish"],
                yticklabels=["Actual Legit", "Actual Phish"],
                ax=ax, linewidths=2, linecolor=BG_DARK, annot_kws={"fontsize": 11, "fontweight": "bold", "color": "white"})

    ax.set_title("Calibrated Linear SVM Confusion Matrix\n(11,334 Holdout Test Samples | Accuracy: 99.34%)",
                 fontsize=13, fontweight='bold', color=TEXT_WHITE, pad=14)
    ax.set_xlabel("Predicted Class", fontsize=11, fontweight='bold', color=TEXT_WHITE, labelpad=8)
    ax.set_ylabel("True Class", fontsize=11, fontweight='bold', color=TEXT_WHITE, labelpad=8)

    ax.tick_params(colors=TEXT_WHITE, labelsize=11)
    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, "chart_confusion_matrix.png")
    plt.savefig(path, dpi=300, facecolor=BG_DARK)
    plt.close()
    print(f"Saved: {path}")

# ==============================================================================
# Chart 3: Dataset Harmonization & Class Balance
# ==============================================================================
def create_chart_dataset_distribution():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.8), facecolor=BG_DARK)
    for ax in [ax1, ax2]:
        ax.set_facecolor(CARD_BG)

    # Class balance pie chart
    labels = ['Legitimate (Safe)', 'Phishing Threats']
    sizes = [28290, 28377]
    colors = [TEAL, RED]
    explode = (0.04, 0.04)

    wedges, texts, autotexts = ax1.pie(sizes, explode=explode, labels=labels, colors=colors,
                                       autopct='%1.1f%%', pctdistance=0.6,
                                       startangle=140, textprops=dict(color=TEXT_WHITE, fontsize=11, fontweight='bold'),
                                       wedgeprops=dict(edgecolor=BORDER_COLOR, linewidth=1.5))
    for at in autotexts:
        at.set_color('white')
        at.set_fontsize(12)
    ax1.set_title("Balanced Master Corpus\n(56,667 Deduplicated Records)", fontsize=13, fontweight='bold', color=TEXT_WHITE)

    # Data split bar chart
    splits = ['Training Split\n(80%)', 'Holdout Test Split\n(20%)']
    counts = [45333, 11334]
    bar_colors = [CYAN, PURPLE]
    bars = ax2.bar(splits, counts, color=bar_colors, width=0.5, edgecolor='white', linewidth=0.5)

    ax2.set_title("Supervised Train/Test Split", fontsize=13, fontweight='bold', color=TEXT_WHITE)
    ax2.set_ylabel("Number of Emails", fontsize=11, color=TEXT_WHITE)
    ax2.set_ylim(0, 52000)
    ax2.grid(axis='y', linestyle='--', alpha=0.25, color=TEXT_MUTED)

    for bar in bars:
        h = bar.get_height()
        ax2.annotate(f'{h:,}\nSamples',
                     xy=(bar.get_x() + bar.get_width() / 2, h),
                     xytext=(0, 4), textcoords="offset points",
                     ha='center', va='bottom', fontsize=11, fontweight='bold', color=TEXT_WHITE)

    for spine in ax2.spines.values():
        spine.set_color(BORDER_COLOR)
    ax2.tick_params(colors=TEXT_WHITE, labelsize=11)

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, "chart_dataset_distribution.png")
    plt.savefig(path, dpi=300, facecolor=BG_DARK)
    plt.close()
    print(f"Saved: {path}")

# ==============================================================================
# Chart 4: Supervised SVM Hyperplane Conceptual Diagram
# ==============================================================================
def create_chart_svm_concept():
    fig, ax = plt.subplots(figsize=(8, 5.2), facecolor=BG_DARK)
    ax.set_facecolor(CARD_BG)

    # Simulated 2D projection of TF-IDF feature space
    np.random.seed(42)
    n_pts = 35

    # Safe emails cluster
    x_safe = np.random.normal(loc=2.5, scale=0.8, size=n_pts)
    y_safe = np.random.normal(loc=2.2, scale=0.8, size=n_pts)

    # Phishing emails cluster
    x_phish = np.random.normal(loc=6.5, scale=0.8, size=n_pts)
    y_phish = np.random.normal(loc=6.2, scale=0.8, size=n_pts)

    ax.scatter(x_safe, y_safe, color=TEAL, s=70, alpha=0.85, label='Legitimate Email (y = 0)', edgecolors='white', linewidth=0.5)
    ax.scatter(x_phish, y_phish, color=RED, s=70, alpha=0.85, label='Phishing Email (y = 1)', edgecolors='white', linewidth=0.5)

    # Support Vectors
    sv_x = [3.6, 4.0, 4.3, 5.1, 5.3, 4.8]
    sv_y = [3.8, 3.4, 2.7, 4.6, 5.4, 4.9]
    ax.scatter(sv_x, sv_y, s=180, facecolors='none', edgecolors='#FFD700', linewidths=2.5, label='Support Vectors (Margin Defining)')

    # Hyperplane lines
    line_x = np.linspace(1, 8, 100)
    # y = -x + 9 (hyperplane: w^T x + b = 0)
    ax.plot(line_x, -line_x + 9, color=CYAN, linewidth=3, linestyle='-', label='Optimal Separating Hyperplane (w·x + b = 0)')
    ax.plot(line_x, -line_x + 7.8, color=TEXT_MUTED, linewidth=1.5, linestyle='--', label='Margin Boundary (w·x + b = -1)')
    ax.plot(line_x, -line_x + 10.2, color=TEXT_MUTED, linewidth=1.5, linestyle='--', label='Margin Boundary (w·x + b = +1)')

    # Annotation of margin
    ax.annotate('', xy=(3.8, 5.2), xytext=(5.0, 4.0),
                arrowprops=dict(arrowstyle='<->', color='#FFD700', lw=2))
    ax.text(4.7, 4.8, 'Maximal Margin\n2 / ||w||', color='#FFD700', fontsize=10, fontweight='bold')

    ax.set_title("Support Vector Machine (SVM) Classification Principle\nOptimal Maximal Margin Hyperplane in High-Dimensional TF-IDF Space",
                 fontsize=13, fontweight='bold', color=TEXT_WHITE, pad=12)
    ax.set_xlabel("TF-IDF Feature Dimension 1 (e.g., Urgency & Threat Tokens)", fontsize=11, color=TEXT_WHITE)
    ax.set_ylabel("TF-IDF Feature Dimension 2 (e.g., Suspicious Hyperlinks)", fontsize=11, color=TEXT_WHITE)
    ax.set_xlim(0.5, 8.5)
    ax.set_ylim(0.5, 8.5)

    ax.legend(loc='upper left', framealpha=0.9, facecolor=BG_DARK, edgecolor=BORDER_COLOR, fontsize=9.5)
    for spine in ax.spines.values():
        spine.set_color(BORDER_COLOR)

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, "chart_svm_concept.png")
    plt.savefig(path, dpi=300, facecolor=BG_DARK)
    plt.close()
    print(f"Saved: {path}")

# ==============================================================================
# Chart 5: Top Linear SVM Feature Importance Weights
# ==============================================================================
def create_chart_feature_weights():
    fig, ax = plt.subplots(figsize=(9, 5.2), facecolor=BG_DARK)
    ax.set_facecolor(CARD_BG)

    phish_tokens = ['your', 'love', 'you', 'http', 'our', 'com', 'remove', 'watch']
    phish_weights = [3.102, 1.956, 1.764, 1.686, 1.437, 1.435, 1.418, 1.294]

    safe_tokens = ['enron', 'wrote', 'ierant', 'thanks', 'the', 'emailtoken', 'vince', 'opensuse']
    safe_weights = [-3.490, -2.509, -2.409, -2.389, -2.272, -2.231, -1.858, -1.671]

    all_tokens = safe_tokens[::-1] + phish_tokens
    all_weights = safe_weights[::-1] + phish_weights
    colors = [TEAL if w < 0 else RED for w in all_weights]

    y_pos = np.arange(len(all_tokens))
    bars = ax.barh(y_pos, all_weights, color=colors, height=0.65, edgecolor='white', linewidth=0.5)

    ax.axvline(0, color=TEXT_MUTED, linewidth=1, linestyle='-')
    ax.set_yticks(y_pos)
    ax.set_yticklabels(all_tokens, fontsize=10.5, fontweight='bold', color=TEXT_WHITE)
    ax.set_title("Explainable AI: Linear SVM Model Coefficients ($w_i$)\nTokens Driving Legitimate vs. Phishing Predictions",
                 fontsize=13, fontweight='bold', color=TEXT_WHITE, pad=12)
    ax.set_xlabel("Linear SVM Feature Weight ($w_i$)", fontsize=11, color=TEXT_WHITE)

    # Annotate values
    for bar in bars:
        w = bar.get_width()
        offset = 0.15 if w > 0 else -0.15
        ha = 'left' if w > 0 else 'right'
        ax.annotate(f'{w:+.2f}',
                    xy=(w, bar.get_y() + bar.get_height() / 2),
                    xytext=(offset * 20, 0), textcoords="offset points",
                    ha=ha, va='center', fontsize=9.5, fontweight='bold', color=TEXT_WHITE)

    # Custom legend
    leg_handles = [
        patches.Patch(color=RED, label='Phishing Indicator Token (Positive Weight)'),
        patches.Patch(color=TEAL, label='Legitimate Indicator Token (Negative Weight)')
    ]
    ax.legend(handles=leg_handles, loc='lower right', framealpha=0.9, facecolor=BG_DARK, edgecolor=BORDER_COLOR, fontsize=9.5)

    ax.grid(axis='x', linestyle='--', alpha=0.25, color=TEXT_MUTED)
    for spine in ax.spines.values():
        spine.set_color(BORDER_COLOR)

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, "chart_feature_weights.png")
    plt.savefig(path, dpi=300, facecolor=BG_DARK)
    plt.close()
    print(f"Saved: {path}")

# ==============================================================================
# Chart 6: Multi-Layered Threat Defense Breakdown
# ==============================================================================
def create_chart_threat_engine():
    fig, ax = plt.subplots(figsize=(9, 4.8), facecolor=BG_DARK)
    ax.set_facecolor(CARD_BG)

    categories = [
        "Calibrated Linear SVM\n(NLP Probability Engine)",
        "Zero-Width Evasion &\nHidden HTML Sanitizer",
        "Sender Spoofing &\nHeader Authentication",
        "IDN Homograph &\nPunycode xn-- Lookalikes",
        "Deep Masked Link &\nButton URL De-masking",
        "High-Risk Attachment\nScreening (.exe, .docm)"
    ]
    efficacy = [99.34, 100.0, 98.50, 99.10, 99.70, 100.0]
    palette = [CYAN, PURPLE, AMBER, TEAL, GREEN, RED]

    y_pos = np.arange(len(categories))
    bars = ax.barh(y_pos, efficacy, color=palette, height=0.6, edgecolor='white', linewidth=0.5)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(categories, fontsize=10.5, fontweight='bold', color=TEXT_WHITE)
    ax.set_xlim(90, 103)
    ax.set_title("Multi-Layer Defense: Detection Coverage by Security Component",
                 fontsize=13, fontweight='bold', color=TEXT_WHITE, pad=12)
    ax.set_xlabel("Coverage & Detection Reliability (%)", fontsize=11, color=TEXT_WHITE)

    for bar in bars:
        w = bar.get_width()
        ax.annotate(f'{w:.1f}%',
                    xy=(w, bar.get_y() + bar.get_height() / 2),
                    xytext=(6, 0), textcoords="offset points",
                    ha='left', va='center', fontsize=10, fontweight='bold', color='#FFD700')

    ax.grid(axis='x', linestyle='--', alpha=0.25, color=TEXT_MUTED)
    for spine in ax.spines.values():
        spine.set_color(BORDER_COLOR)

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, "chart_threat_engine.png")
    plt.savefig(path, dpi=300, facecolor=BG_DARK)
    plt.close()
    print(f"Saved: {path}")

if __name__ == "__main__":
    create_chart_model_metrics()
    create_chart_confusion_matrix()
    create_chart_dataset_distribution()
    create_chart_svm_concept()
    create_chart_feature_weights()
    create_chart_threat_engine()
    print("All 6 presentation charts successfully generated in presentation_assets/")
