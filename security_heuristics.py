"""
Cyber Threat Heuristics and Anti-Evasion Engine
================================================
Comprehensive inspection modules for:
1. Zero-width character & hidden HTML de-obfuscation
2. Sender identity & header spoofing (Display Name, Reply-To, SPF/DKIM/DMARC)
3. Deep Masked Hyperlinks, Anchor Text & Domain Mismatches
4. IDN Homograph (Punycode xn--) & Brand Typosquatting
5. Attachment threat screening (double extensions, scripts, macros)
6. URL shorteners, raw IP hosts, suspicious TLDs, and domain entropy
"""

import re
import math
import html
import urllib.parse
from typing import List, Dict, Any, Tuple, Optional

# ============================================================================
# Constant Threat Dictionaries
# ============================================================================

ZERO_WIDTH_CHARS = ["\u200B", "\u200C", "\u200D", "\uFEFF", "\u00AD", "\u2060", "\u180E", "\u200E", "\u200F"]

SUSPICIOUS_TLDS = {
    ".xyz", ".top", ".ru", ".buzz", ".work", ".click", ".fit", ".ga",
    ".cf", ".ml", ".gq", ".tk", ".cn", ".icu", ".cam", ".monster",
    ".rest", ".live", ".support", ".accountant", ".download", ".racing"
}

URL_SHORTENERS = {
    "bit.ly", "tinyurl.com", "t.co", "cutt.ly", "is.gd", "rb.gy",
    "shorturl.at", "ow.ly", "buff.ly", "goo.gl", "trib.al", "rebrand.ly"
}

POPULAR_FREE_EMAIL_DOMAINS = {
    "gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "icloud.com",
    "aol.com", "mail.com", "proton.me", "protonmail.com", "zoho.com",
    "yandex.com", "gmx.com", "live.com"
}

HIGH_VALUE_TARGET_BRANDS = [
    "microsoft", "office365", "google", "apple", "amazon", "netflix",
    "paypal", "chase", "wellsfargo", "bankofamerica", "citibank",
    "facebook", "instagram", "twitter", "linkedin", "dropbox",
    "dhl", "fedex", "ups", "adobe", "docusign", "coinbase", "binance",
    "metamask", "steam", "walmart", "irs", "gov", "helpdesk", "support"
]

HIGH_RISK_EXTENSIONS = {
    ".exe", ".scr", ".bat", ".cmd", ".vbs", ".vbe", ".js", ".jse",
    ".hta", ".iso", ".img", ".wsf", ".ps1", ".pif", ".msi", ".jar"
}

MACRO_EXTENSIONS = {
    ".docm", ".xlsm", ".pptm", ".dotm", ".xltm"
}

ARCHIVE_EXTENSIONS = {
    ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"
}

GENERIC_CTA_PATTERNS = [
    r"click\s+(here|below|this\s+link)",
    r"press\s+(here|below)",
    r"follow\s+this\s+link",
    r"verify\s+(account|identity|now|login|email)",
    r"confirm\s+(account|identity|details|email|password)",
    r"update\s+(payment|billing|profile|security)",
    r"log\s*in\s+(here|now|to\s+verify)",
    r"download\s+(invoice|attachment|document|statement)",
    r"view\s+(invoice|document|file|report)",
    r"claim\s+(prize|funds|reward|payout|bonus)",
    r"restore\s+(access|account)",
    r"action\s+required",
]


# ============================================================================
# 1. Anti-Evasion & Zero-Width Sanitizer
# ============================================================================

def sanitize_evasions(raw_text: str) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Strips zero-width characters, unescapes HTML entities, and strips hidden HTML.
    Returns cleaned text and a list of threat signals if deliberate evasion was detected.
    """
    signals: List[Dict[str, Any]] = []
    if not raw_text:
        return "", signals

    has_zero_width = False
    cleaned = raw_text

    # Check for zero-width characters
    for zw in ZERO_WIDTH_CHARS:
        if zw in cleaned:
            has_zero_width = True
            cleaned = cleaned.replace(zw, "")

    if has_zero_width:
        signals.append({
            "category": "evasion",
            "severity": "danger",
            "title": "Zero-Width Character Evasion Detected",
            "description": "Invisible zero-width unicode characters were detected. Attackers inject these to split keywords and evade NLP machine learning filters."
        })

    # Unescape HTML entities (&amp;, &#x...;, &lt;)
    unescaped = html.unescape(cleaned)

    # Detect hidden HTML evasion: <span style="display:none">noise</span> or <font size="0">
    hidden_html_pattern = re.compile(
        r'<[^>]*(?:display\s*:\s*none|font-size\s*:\s*0|visibility\s*:\s*hidden)[^>]*>(.*?)</[^>]+>',
        re.IGNORECASE | re.DOTALL
    )
    if hidden_html_pattern.search(unescaped):
        signals.append({
            "category": "evasion",
            "severity": "danger",
            "title": "Hidden HTML Evasion Markup Detected",
            "description": "Email contains hidden text tags (display:none or font-size:0) designed to confuse spam filters while remaining invisible to the user."
        })
        unescaped = hidden_html_pattern.sub("", unescaped)

    return unescaped, signals


# ============================================================================
# 2. Shannon Entropy & String Utilities
# ============================================================================

def calculate_entropy(text: str) -> float:
    """Calculates Shannon entropy of a string (measures randomness)."""
    if not text:
        return 0.0
    text_clean = text.lower()
    freq = {}
    for c in text_clean:
        freq[c] = freq.get(c, 0) + 1
    entropy = 0.0
    for count in freq.values():
        p = count / len(text_clean)
        entropy -= p * math.log2(p)
    return round(entropy, 3)


def levenshtein_distance(s1: str, s2: str) -> int:
    """Computes Levenshtein edit distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]


# ============================================================================
# 3. URL, Domain & Homograph Intelligence
# ============================================================================

IP_HOST_REGEX = re.compile(r"^https?://(?:\d{1,3}\.){3}\d{1,3}(?::\d+)?(?:/|$)", re.IGNORECASE)
DOMAIN_EXTRACT_REGEX = re.compile(r"https?://([^/:\s?#]+)", re.IGNORECASE)

def inspect_url(url: str) -> Dict[str, Any]:
    """
    Performs deep inspection on a single URL:
    - Punycode / IDN Homograph detection
    - IP host detection
    - Suspicious TLD check
    - URL shortener identification
    - Brand typosquatting / lookalike
    - Entropy calculation
    """
    flags: List[str] = []
    is_suspicious = False
    domain = ""

    parsed = urllib.parse.urlparse(url if url.startswith(("http://", "https://")) else f"http://{url}")
    hostname = (parsed.hostname or "").lower()

    if hostname:
        domain = hostname
    else:
        m = DOMAIN_EXTRACT_REGEX.match(url)
        domain = m.group(1).lower() if m else url.lower()

    # 1. IP Hostname Check
    if IP_HOST_REGEX.match(url) or re.match(r"^(\d{1,3}\.){3}\d{1,3}$", domain):
        flags.append("Raw Numeric IP Hostname (Hides domain identity)")
        is_suspicious = True

    # 2. Punycode / IDN Homograph Check (Lookalike Cyrillic/Greek characters)
    if "xn--" in domain or any(ord(char) > 127 for char in domain):
        flags.append("IDN Homograph / Punycode Lookalike Domain (Phishing mimic)")
        is_suspicious = True

    # 3. Suspicious TLD Check
    for tld in SUSPICIOUS_TLDS:
        if domain.endswith(tld):
            flags.append(f"High-Risk / Abuse-Prone TLD ({tld})")
            is_suspicious = True
            break

    # 4. URL Shortener Check
    for shortener in URL_SHORTENERS:
        if domain == shortener or domain.endswith("." + shortener):
            flags.append(f"URL Shortener Redirection ({shortener})")
            is_suspicious = True
            break

    # 5. Brand Impersonation / Typosquatting Check
    domain_core = domain.split(".")[0] if "." in domain else domain
    for brand in HIGH_VALUE_TARGET_BRANDS:
        if brand in domain and domain != f"{brand}.com" and not domain.endswith(f".{brand}.com"):
            flags.append(f"Brand Keyword in Non-Official Domain ('{brand}' inside {domain})")
            is_suspicious = True
            break
        elif len(domain_core) >= 4 and len(brand) >= 4:
            dist = levenshtein_distance(domain_core, brand)
            if dist == 1 or (dist == 2 and len(brand) >= 6):
                flags.append(f"Brand Typosquatting Lookalike ('{domain_core}' closely mimics '{brand}')")
                is_suspicious = True
                break

    # 6. Domain Randomness / Shannon Entropy
    entropy = calculate_entropy(domain_core)
    if entropy >= 3.8 and len(domain_core) >= 8:
        flags.append(f"High Domain Entropy ({entropy} bits - possible DGA/algorithmic random string)")
        is_suspicious = True

    # 7. Credential / Phishing Keywords in URL Path
    path_lower = parsed.path.lower()
    for kw in ["login", "verify", "authenticate", "signin", "secure-auth", "update-billing", "password-reset"]:
        if kw in path_lower:
            flags.append(f"Credential Harvesting Keyword in URL Path ('{kw}')")
            is_suspicious = True
            break

    return {
        "url": url,
        "domain": domain,
        "flags": flags,
        "is_suspicious": is_suspicious,
        "entropy": entropy
    }


# ============================================================================
# 4. Masked Hyperlinks & Anchor Text Inspection
# ============================================================================

def inspect_hyperlinks(links: List[Dict[str, str]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Inspects extracted links with their visible anchor text:
    `links` = [{"anchor_text": "Click Here", "target_url": "http://evil.com"}]
    
    Returns:
    - Detailed list of inspected links with risk ratings
    - List of threat signals
    """
    inspected_links: List[Dict[str, Any]] = []
    signals: List[Dict[str, Any]] = []

    mismatches_found = []
    urgent_ctas_found = []

    for item in links:
        anchor = item.get("anchor_text", "").strip()
        target = item.get("target_url", "").strip()
        if not target:
            continue

        url_inspection = inspect_url(target)
        link_record = {
            "anchor_text": anchor or "(No visible text)",
            "target_url": target,
            "domain": url_inspection["domain"],
            "flags": list(url_inspection["flags"]),
            "is_mismatch": False,
            "risk_severity": "safe"
        }

        # Check for Mismatched Domain Deception:
        # e.g. Visible text is a URL / domain like "https://paypal.com" but target is "http://evil.xyz"
        anchor_domain_match = DOMAIN_EXTRACT_REGEX.search(anchor) or re.search(r"([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", anchor)
        if anchor_domain_match:
            anchor_domain = anchor_domain_match.group(1).lower().lstrip("www.")
            target_domain = url_inspection["domain"].lstrip("www.")
            if anchor_domain and target_domain and anchor_domain != target_domain:
                link_record["is_mismatch"] = True
                link_record["flags"].append(f"Deceptive Link Spoofing: Visible text displays '{anchor_domain}' but redirects to '{target_domain}'")
                link_record["risk_severity"] = "danger"
                mismatches_found.append((anchor_domain, target_domain))

        # Check for Generic Phishing Call-To-Action Anchors ("Click Here", "Press Here")
        for cta_regex in GENERIC_CTA_PATTERNS:
            if re.search(cta_regex, anchor, re.IGNORECASE):
                link_record["flags"].append(f"Generic Urgency Action Anchor ('{anchor}') masking external URL")
                if link_record["risk_severity"] != "danger":
                    link_record["risk_severity"] = "warning"
                urgent_ctas_found.append(anchor)
                break

        if url_inspection["is_suspicious"] and link_record["risk_severity"] == "safe":
            link_record["risk_severity"] = "warning"
        if url_inspection["flags"] and any("Domain" in f or "Punycode" in f or "IP" in f for f in url_inspection["flags"]):
            link_record["risk_severity"] = "danger"

        inspected_links.append(link_record)

    # Generate Aggregate Threat Signals
    if mismatches_found:
        signals.append({
            "category": "link_spoofing",
            "severity": "danger",
            "title": "Critical Deceptive Hyperlink Spoofing",
            "description": f"Detected {len(mismatches_found)} deceptive hyperlink(s) where the visible text displays a trusted domain but secretly redirects to an entirely different address (e.g. '{mismatches_found[0][0]}' -> '{mismatches_found[0][1]}')."
        })

    if urgent_ctas_found:
        signals.append({
            "category": "urgency_anchor",
            "severity": "warning",
            "title": "Masked Call-To-Action Hyperlinks",
            "description": f"Found {len(urgent_ctas_found)} link(s) concealed behind generic call-to-action buttons/anchors ('{urgent_ctas_found[0]}'). Phishers use masked buttons to disguise malicious destination URLs."
        })

    return inspected_links, signals


# ============================================================================
# 5. Sender Identity & Header Security
# ============================================================================

def analyze_headers(headers: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    Analyzes email headers for:
    - Display Name Spoofing ("CEO / IT Support" <attacker@gmail.com>)
    - Reply-To Mismatch (From != Reply-To)
    - Authentication status (SPF, DKIM, DMARC failures)
    """
    signals: List[Dict[str, Any]] = []
    if not headers:
        return signals

    from_header = headers.get("from", "") or headers.get("From", "")
    reply_to = headers.get("reply-to", "") or headers.get("Reply-To", "")
    auth_results = headers.get("authentication-results", "") or headers.get("Authentication-Results", "")

    # 1. Parse Display Name and Envelope Address
    display_name = ""
    envelope_address = ""
    m = re.match(r'^(?:"?([^"<]+)"?\s*)?<([^>]+)>$', from_header.strip())
    if m:
        display_name = (m.group(1) or "").strip()
        envelope_address = (m.group(2) or "").strip().lower()
    else:
        envelope_address = from_header.strip().lower()

    envelope_domain = envelope_address.split("@")[-1] if "@" in envelope_address else ""

    # Check Display Name Spoofing
    if display_name and envelope_domain:
        display_lower = display_name.lower()
        impersonated_brand = None
        for brand in HIGH_VALUE_TARGET_BRANDS:
            if brand in display_lower and brand not in envelope_domain:
                impersonated_brand = brand
                break

        if impersonated_brand:
            signals.append({
                "category": "sender_spoofing",
                "severity": "danger",
                "title": f"Display Name Brand Spoofing ('{display_name}')",
                "description": f"The sender display name claims to represent '{impersonated_brand.title()}', but the actual sender domain is '{envelope_domain}'."
            })
        elif envelope_domain in POPULAR_FREE_EMAIL_DOMAINS and any(term in display_lower for term in ["ceo", "it support", "admin", "security", "helpdesk", "billing"]):
            signals.append({
                "category": "sender_spoofing",
                "severity": "danger",
                "title": f"Executive / IT Impersonation from Free Mailbox",
                "description": f"Sender claims to be '{display_name}' but is sending from a public free email service ({envelope_domain}). Common vector for Business Email Compromise (BEC)."
            })

    # 2. Check Reply-To Mismatch
    if reply_to:
        reply_m = re.search(r'<([^>]+)>', reply_to)
        reply_addr = (reply_m.group(1) if reply_m else reply_to).strip().lower()
        reply_domain = reply_addr.split("@")[-1] if "@" in reply_addr else ""

        if envelope_domain and reply_domain and envelope_domain != reply_domain:
            signals.append({
                "category": "reply_to_mismatch",
                "severity": "danger",
                "title": "Reply-To Header Domain Mismatch",
                "description": f"Replies are routed to an entirely different domain ('{reply_domain}') than the sender ('{envelope_domain}'). Attackers use this to intercept responses."
            })

    # 3. Check SPF, DKIM, DMARC Authentication Failures
    if auth_results:
        auth_lower = auth_results.lower()
        auth_issues = []
        if "spf=fail" in auth_lower or "spf=softfail" in auth_lower:
            auth_issues.append("SPF validation failed")
        if "dkim=fail" in auth_lower:
            auth_issues.append("DKIM signature failed")
        if "dmarc=fail" in auth_lower:
            auth_issues.append("DMARC policy failed")

        if auth_issues:
            signals.append({
                "category": "auth_failure",
                "severity": "danger",
                "title": "Email Domain Authentication Failure",
                "description": f"Domain security checks failed: {', '.join(auth_issues)}. Indicates the sender IP was not authorized to send on behalf of this domain."
            })

    return signals


# ============================================================================
# 6. Attachment Threat Screening
# ============================================================================

def inspect_attachments(attachments: List[Dict[str, str]], body_text: str = "") -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Screens email attachments for:
    - Double extensions (.pdf.exe, .docx.vbs)
    - High-risk executables and scripts (.exe, .bat, .vbs, .iso, .hta)
    - Macro-enabled Office files (.docm, .xlsm)
    - Password-protected archives with passwords in email body
    """
    scanned_attachments: List[Dict[str, Any]] = []
    signals: List[Dict[str, Any]] = []

    body_lower = body_text.lower()
    body_mentions_pwd = any(k in body_lower for k in ["password:", "pass:", "pwd:", "password is", "zip password", "archive pass"])

    for att in attachments:
        filename = att.get("filename", "").strip()
        size_bytes = att.get("size_bytes", 0)
        mime_type = att.get("content_type", "")
        if not filename:
            continue

        lower_name = filename.lower()
        flags = []
        severity = "safe"

        # 1. Double extension detection (e.g. document.pdf.exe)
        double_ext_match = re.search(r'\.([a-zA-Z0-9]{2,4})\.([a-zA-Z0-9]{2,4})$', lower_name)
        if double_ext_match:
            first_ext = f".{double_ext_match.group(1)}"
            second_ext = f".{double_ext_match.group(2)}"
            if second_ext in HIGH_RISK_EXTENSIONS:
                flags.append(f"Deceptive Double Extension ('{first_ext}{second_ext}' masks executable payload)")
                severity = "danger"

        # 2. High-Risk Extension Check
        for ext in HIGH_RISK_EXTENSIONS:
            if lower_name.endswith(ext):
                flags.append(f"Direct Executable / Script Payload ({ext})")
                severity = "danger"
                break

        # 3. Macro-Enabled Document Check
        for ext in MACRO_EXTENSIONS:
            if lower_name.endswith(ext):
                flags.append(f"Macro-Enabled Office Document ({ext}) - Capable of executing malicious code")
                severity = "danger"
                break

        # 4. Password-protected Archive with Password in Body
        for ext in ARCHIVE_EXTENSIONS:
            if lower_name.endswith(ext) and body_mentions_pwd:
                flags.append("Archive Attachment with Password Disclosed in Email Body (Classic Gateway Evasion)")
                if severity != "danger":
                    severity = "warning"
                break

        scanned_attachments.append({
            "filename": filename,
            "size_bytes": size_bytes,
            "mime_type": mime_type,
            "flags": flags,
            "risk_severity": severity
        })

    # Summary Signals
    danger_attachments = [a["filename"] for a in scanned_attachments if a["risk_severity"] == "danger"]
    if danger_attachments:
        signals.append({
            "category": "malicious_attachment",
            "severity": "danger",
            "title": "High-Risk Attachment Payloads Detected",
            "description": f"Contains dangerous file attachment(s): {', '.join(danger_attachments)}. Executables, scripts, and macro documents can compromise workstations upon opening."
        })

    return scanned_attachments, signals
