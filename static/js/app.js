/**
 * Phishing Sentinel — Client-side Application Logic
 * Pure ES6+ Vanilla JavaScript for full design control & zero runtime bloat.
 */

// Application State
const state = {
  examples: [],
  history: [],
  currentResult: null,
};

// DOM Selectors
const DOM = {
  systemStatusBadge: document.getElementById('systemStatusBadge'),
  systemStatusText: document.getElementById('systemStatusText'),
  presetPillsContainer: document.getElementById('presetPillsContainer'),
  emailForm: document.getElementById('emailForm'),
  emailInput: document.getElementById('emailInput'),
  charCount: document.getElementById('charCount'),
  wordCount: document.getElementById('wordCount'),
  pasteBtn: document.getElementById('pasteBtn'),
  clearBtn: document.getElementById('clearBtn'),
  scanBtn: document.getElementById('scanBtn'),
  copyReportBtn: document.getElementById('copyReportBtn'),
  emptyState: document.getElementById('emptyState'),
  resultsContainer: document.getElementById('resultsContainer'),
  verdictCard: document.getElementById('verdictCard'),
  verdictIconWrap: document.getElementById('verdictIconWrap'),
  riskLevelTag: document.getElementById('riskLevelTag'),
  latencyTag: document.getElementById('latencyTag'),
  verdictTitle: document.getElementById('verdictTitle'),
  verdictDesc: document.getElementById('verdictDesc'),
  probPercentage: document.getElementById('probPercentage'),
  gaugeBarFill: document.getElementById('gaugeBarFill'),
  metricConfidence: document.getElementById('metricConfidence'),
  metricClassification: document.getElementById('metricClassification'),
  signalsList: document.getElementById('signalsList'),
  urlsSection: document.getElementById('urlsSection'),
  urlCount: document.getElementById('urlCount'),
  urlsList: document.getElementById('urlsList'),
  cleanTextPreview: document.getElementById('cleanTextPreview'),
  historyContainer: document.getElementById('historyContainer'),
  clearHistoryBtn: document.getElementById('clearHistoryBtn'),
  toast: document.getElementById('toast'),
  toastMessage: document.getElementById('toastMessage'),
};

// SVG Icon Templates
const ICONS = {
  safe: `
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
      <path d="m9 12 2 2 4-4"/>
    </svg>`,
  threat: `
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
      <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
      <line x1="12" y1="9" x2="12" y2="13"/>
      <line x1="12" y1="17" x2="12.01" y2="17"/>
    </svg>`,
  warning: `
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="12" cy="12" r="10"/>
      <line x1="12" y1="8" x2="12" y2="12"/>
      <line x1="12" y1="16" x2="12.01" y2="16"/>
    </svg>`,
  signalDanger: `
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <polygon points="7.86 2 16.14 2 22 7.86 22 16.14 16.14 22 7.86 22 2 16.14 2 7.86 7.86 2"/>
      <line x1="12" y1="8" x2="12" y2="12"/>
      <line x1="12" y1="16" x2="12.01" y2="16"/>
    </svg>`,
  signalWarning: `
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/>
      <line x1="12" y1="9" x2="12" y2="13"/>
      <line x1="12" y1="17" x2="12.01" y2="17"/>
    </svg>`,
};

/**
 * Toast notifications
 */
let toastTimeout = null;
function showToast(message, duration = 3000) {
  if (toastTimeout) clearTimeout(toastTimeout);
  DOM.toastMessage.textContent = message;
  DOM.toast.classList.remove('hidden');
  toastTimeout = setTimeout(() => {
    DOM.toast.classList.add('hidden');
  }, duration);
}

/**
 * Update character and word counters
 */
function updateTextCounters() {
  const text = DOM.emailInput.value;
  DOM.charCount.textContent = `${text.length.toLocaleString()} characters`;
  const words = text.trim() ? text.trim().split(/\s+/).length : 0;
  DOM.wordCount.textContent = `${words.toLocaleString()} words`;
}

/**
 * Check backend health & model readiness
 */
async function checkSystemHealth() {
  try {
    const res = await fetch('/api/health');
    if (!res.ok) throw new Error('Health check returned non-200');
    const data = await res.json();
    if (data.model_loaded) {
      DOM.systemStatusBadge.classList.add('live');
      DOM.systemStatusText.textContent = 'Engine Active';
    } else {
      DOM.systemStatusText.textContent = 'Model Missing';
    }
  } catch (err) {
    console.warn('System status check error:', err);
    DOM.systemStatusText.textContent = 'API Offline';
  }
}

/**
 * Fetch preset email examples from backend
 */
async function loadPresets() {
  try {
    const res = await fetch('/api/examples');
    if (!res.ok) return;
    const data = await res.json();
    state.examples = data.examples || [];

    if (state.examples.length > 0) {
      DOM.presetPillsContainer.innerHTML = '';
      state.examples.forEach((example) => {
        const pill = document.createElement('button');
        pill.type = 'button';
        pill.className = 'preset-pill';
        pill.textContent = example.title;
        pill.title = `${example.tag} (${example.category})`;
        pill.addEventListener('click', () => {
          DOM.emailInput.value = example.content;
          updateTextCounters();
          DOM.emailInput.focus();
          showToast(`Loaded preset: "${example.title}"`);
        });
        DOM.presetPillsContainer.appendChild(pill);
      });
    }
  } catch (err) {
    console.error('Error fetching presets:', err);
  }
}

/**
 * Send email text to inference API
 */
async function analyzeEmail(text) {
  const cleanInput = text.trim();
  if (!cleanInput) {
    showToast('Please paste or type email content first.');
    return;
  }

  // Set loading state
  const btnText = DOM.scanBtn.querySelector('.btn-text');
  const btnSpinner = DOM.scanBtn.querySelector('.btn-spinner');
  DOM.scanBtn.disabled = true;
  btnText.classList.add('hidden');
  btnSpinner.classList.remove('hidden');

  try {
    const response = await fetch('/api/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email_text: cleanInput }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Inference request failed');
    }

    const result = await response.json();
    state.currentResult = result;
    renderResults(result);
    saveToHistory(cleanInput, result);
    DOM.copyReportBtn.classList.remove('hidden');
  } catch (err) {
    console.error('Analysis error:', err);
    showToast(`Error: ${err.message}`);
  } finally {
    DOM.scanBtn.disabled = false;
    btnText.classList.remove('hidden');
    btnSpinner.classList.add('hidden');
  }
}

/**
 * Render analysis results and update UI telemetry
 */
function renderResults(res) {
  DOM.emptyState.classList.add('hidden');
  DOM.resultsContainer.classList.remove('hidden');

  const probPercent = (res.phishing_probability * 100).toFixed(1);
  const confPercent = (res.confidence * 100).toFixed(1);
  const isMalicious = res.is_phishing;

  // 1. Verdict Card
  DOM.verdictCard.className = 'verdict-card';
  if (res.risk_level === 'CRITICAL' || res.risk_level === 'HIGH') {
    DOM.verdictCard.classList.add('threat');
    DOM.verdictIconWrap.innerHTML = ICONS.threat;
    DOM.verdictTitle.textContent = res.verdict;
    DOM.verdictDesc.textContent =
      'High confidence indicators of malicious phishing or social engineering detected. Do not click links or respond.';
  } else if (res.risk_level === 'MEDIUM') {
    DOM.verdictCard.classList.add('suspicious');
    DOM.verdictIconWrap.innerHTML = ICONS.warning;
    DOM.verdictTitle.textContent = res.verdict;
    DOM.verdictDesc.textContent =
      'Elevated risk signals detected. Review sender headers and links carefully before proceeding.';
  } else {
    DOM.verdictCard.classList.add('safe');
    DOM.verdictIconWrap.innerHTML = ICONS.safe;
    DOM.verdictTitle.textContent = res.verdict;
    DOM.verdictDesc.textContent =
      'Linguistic patterns, vocabulary, and token distributions align with safe/legitimate communications.';
  }

  DOM.riskLevelTag.textContent = res.risk_level;
  DOM.latencyTag.textContent = `${res.processing_time_ms} ms`;

  // 2. Risk Meter Gauge
  DOM.probPercentage.textContent = `${probPercent}%`;
  DOM.gaugeBarFill.style.width = `${probPercent}%`;

  if (res.phishing_probability >= 0.6) {
    DOM.gaugeBarFill.style.backgroundColor = 'var(--danger)';
    DOM.probPercentage.style.color = 'var(--danger)';
  } else if (res.phishing_probability >= 0.35) {
    DOM.gaugeBarFill.style.backgroundColor = 'var(--warning)';
    DOM.probPercentage.style.color = 'var(--warning)';
  } else {
    DOM.gaugeBarFill.style.backgroundColor = 'var(--success)';
    DOM.probPercentage.style.color = 'var(--success)';
  }

  // 3. Metrics Grid
  DOM.metricConfidence.textContent = `${confPercent}%`;
  DOM.metricClassification.textContent = isMalicious ? 'Malicious (1)' : 'Benign (0)';

  // 4. Behavioral Threat Signals
  DOM.signalsList.innerHTML = '';
  if (res.threat_signals && res.threat_signals.length > 0) {
    res.threat_signals.forEach((signal) => {
      const item = document.createElement('div');
      item.className = `signal-item ${signal.severity}`;
      const icon = signal.severity === 'danger' ? ICONS.signalDanger : ICONS.signalWarning;
      item.innerHTML = `
        <div class="signal-icon">${icon}</div>
        <div>
          <div class="signal-title">${escapeHTML(signal.title)}</div>
          <div class="signal-desc">${escapeHTML(signal.description)}</div>
        </div>
      `;
      DOM.signalsList.appendChild(item);
    });
  } else {
    DOM.signalsList.innerHTML = `
      <div class="no-signals-msg">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="20 6 9 17 4 12"/>
        </svg>
        <span>No common social engineering triggers or suspicious domain patterns detected.</span>
      </div>
    `;
  }

  // 5. Extracted URLs
  if (res.extracted_urls && res.extracted_urls.length > 0) {
    DOM.urlsSection.classList.remove('hidden');
    DOM.urlCount.textContent = res.extracted_urls.length;
    DOM.urlsList.innerHTML = '';
    res.extracted_urls.forEach((url) => {
      const isSuspicious = /\.(xyz|top|tk|ru|buzz|click)|login|verify/i.test(url);
      const chip = document.createElement('div');
      chip.className = `url-chip ${isSuspicious ? 'suspicious' : ''}`;
      chip.innerHTML = `
        <span>${escapeHTML(url)}</span>
        <span style="font-size:0.7rem; font-weight:700;">${isSuspicious ? 'FLAGGED' : 'LINK'}</span>
      `;
      DOM.urlsList.appendChild(chip);
    });
  } else {
    DOM.urlsSection.classList.add('hidden');
  }

  // 6. Preprocessed Text Preview
  DOM.cleanTextPreview.textContent = res.clean_text_preview || '(None)';
}

/**
 * Copy formatted security summary to clipboard
 */
function copySecurityReport() {
  if (!state.currentResult) return;
  const res = state.currentResult;
  const prob = (res.phishing_probability * 100).toFixed(2);
  const conf = (res.confidence * 100).toFixed(2);
  const signals = res.threat_signals.map((s) => `  * [${s.severity.toUpperCase()}] ${s.title}: ${s.description}`).join('\n');

  const report = [
    `=== PHISHING SENTINEL THREAT REPORT ===`,
    `Verdict:              ${res.verdict}`,
    `Risk Tier:            ${res.risk_level}`,
    `Phishing Probability: ${prob}%`,
    `Model Confidence:     ${conf}%`,
    `Inference Time:       ${res.processing_time_ms} ms`,
    `Signals Detected:`,
    signals || `  * None detected`,
    res.extracted_urls.length ? `Extracted URLs:\n` + res.extracted_urls.map((u) => `  * ${u}`).join('\n') : '',
    `========================================`,
  ].filter(Boolean).join('\n');

  navigator.clipboard.writeText(report).then(() => {
    showToast('Analysis report copied to clipboard!');
  }).catch(() => {
    showToast('Failed to copy to clipboard.');
  });
}

/**
 * Session Scan History Management
 */
const HISTORY_KEY = 'sentinel_scan_history';

function loadHistory() {
  try {
    const raw = localStorage.getItem(HISTORY_KEY);
    state.history = raw ? JSON.parse(raw) : [];
    renderHistory();
  } catch (e) {
    state.history = [];
  }
}

function saveToHistory(text, result) {
  const item = {
    id: Date.now(),
    preview: text.replace(/\s+/g, ' ').slice(0, 100),
    fullText: text,
    verdict: result.verdict,
    risk_level: result.risk_level,
    probability: result.phishing_probability,
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
  };

  state.history.unshift(item);
  if (state.history.length > 8) state.history.pop();
  try {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(state.history));
  } catch (e) {}
  renderHistory();
}

function renderHistory() {
  if (!state.history.length) {
    DOM.historyContainer.innerHTML = '<p class="history-empty">No scans recorded in this session yet.</p>';
    return;
  }

  DOM.historyContainer.innerHTML = '';
  state.history.forEach((h) => {
    const row = document.createElement('div');
    row.className = 'history-item';
    const tagClass = (h.risk_level === 'CRITICAL' || h.risk_level === 'HIGH') ? 'threat' : (h.risk_level === 'MEDIUM' ? 'suspicious' : 'safe');
    row.innerHTML = `
      <div class="history-left">
        <span class="history-tag ${tagClass}">${h.risk_level}</span>
        <span class="history-preview">${escapeHTML(h.preview)}</span>
      </div>
      <div class="history-right">
        <span class="history-prob">${(h.probability * 100).toFixed(1)}%</span>
        <span class="history-time">${h.timestamp}</span>
      </div>
    `;
    row.addEventListener('click', () => {
      DOM.emailInput.value = h.fullText;
      updateTextCounters();
      analyzeEmail(h.fullText);
    });
    DOM.historyContainer.appendChild(row);
  });
}

function clearHistory() {
  state.history = [];
  try {
    localStorage.removeItem(HISTORY_KEY);
  } catch (e) {}
  renderHistory();
  showToast('Session scan history cleared.');
}

/**
 * Utility: HTML entity escaping
 */
function escapeHTML(str) {
  return str.replace(/[&<>'"]/g, (tag) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    "'": '&#39;',
    '"': '&quot;',
  }[tag] || tag));
}

/**
 * Event Listeners Registration
 */
function initEvents() {
  DOM.emailInput.addEventListener('input', updateTextCounters);

  DOM.emailForm.addEventListener('submit', (e) => {
    e.preventDefault();
    analyzeEmail(DOM.emailInput.value);
  });

  // Shortcut: Ctrl+Enter or Cmd+Enter
  DOM.emailInput.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      analyzeEmail(DOM.emailInput.value);
    }
  });

  DOM.clearBtn.addEventListener('click', () => {
    DOM.emailInput.value = '';
    updateTextCounters();
    DOM.emailInput.focus();
    showToast('Input cleared');
  });

  DOM.pasteBtn.addEventListener('click', async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text) {
        DOM.emailInput.value = text;
        updateTextCounters();
        showToast('Pasted from clipboard');
      }
    } catch (e) {
      showToast('Clipboard access denied. Use Ctrl+V instead.');
    }
  });

  DOM.copyReportBtn.addEventListener('click', copySecurityReport);
  DOM.clearHistoryBtn.addEventListener('click', clearHistory);
}

// Initialization on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  initEvents();
  updateTextCounters();
  checkSystemHealth();
  loadPresets();
  loadHistory();
});
