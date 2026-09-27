"""
Universal Multi-Modal Document Parser
======================================
Ingests and extracts text, headers, masked hyperlinks, and attachment metadata
from all document formats used in email and phishing communication:
- Email formats: .eml, .msg (Outlook), .mbox
- Document formats: .pdf, .docx, .doc, .rtf
- Spreadsheets: .xlsx, .xls, .csv
- Presentations: .pptx
- Web & text: .html, .htm, .txt, .json
- Images: .png, .jpg, .jpeg, .webp, .bmp, .tiff (OCR)
"""

import io
import re
import os
import email
import email.policy
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup
from PIL import Image

# Import extract_msg if available for Outlook .msg support
try:
    import extract_msg
    HAS_EXTRACT_MSG = True
except ImportError:
    HAS_EXTRACT_MSG = False

# Import pypdf for PDF support
try:
    import pypdf
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False

# Import docx for Word document support
try:
    import docx
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

# Import openpyxl for Excel spreadsheet support
try:
    import openpyxl
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

# Import pytesseract for OCR
try:
    import pytesseract
    HAS_PYTESSERACT = True
except ImportError:
    HAS_PYTESSERACT = False


URL_REGEX = re.compile(r"https?://[^\s<>\"']+|www\.[^\s<>\"']+", re.IGNORECASE)
MARKDOWN_LINK_REGEX = re.compile(r'\[([^\]]+)\]\((https?://[^\s\)]+)\)', re.IGNORECASE)


def extract_masked_links_from_text_and_html(content: str) -> List[Dict[str, str]]:
    """
    Extracts all links and their visible anchor text from HTML tags,
    Markdown syntax, and raw plaintext.
    """
    links: List[Dict[str, str]] = []
    seen_urls = set()

    if not content:
        return links

    # 1. HTML Anchor Extraction: <a href="url">Anchor Text</a>
    if "<a " in content.lower() or "<button" in content.lower():
        try:
            soup = BeautifulSoup(content, "html.parser")
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"].strip()
                anchor = a_tag.get_text(strip=True)
                if href and href not in seen_urls:
                    seen_urls.add(href)
                    links.append({"anchor_text": anchor or href, "target_url": href})

            for btn in soup.find_all("button"):
                onclick = btn.get("onclick", "")
                btn_url_match = URL_REGEX.search(onclick)
                if btn_url_match:
                    url = btn_url_match.group(0).strip()
                    btn_text = btn.get_text(strip=True) or "Button Action"
                    if url not in seen_urls:
                        seen_urls.add(url)
                        links.append({"anchor_text": btn_text, "target_url": url})
        except Exception:
            pass

    # 2. Markdown Link Extraction: [Click Here](http://...)
    for match in MARKDOWN_LINK_REGEX.finditer(content):
        anchor = match.group(1).strip()
        url = match.group(2).strip()
        if url and url not in seen_urls:
            seen_urls.add(url)
            links.append({"anchor_text": anchor, "target_url": url})

    # 3. Raw URLs in plaintext
    for url in URL_REGEX.findall(content):
        url = url.strip()
        if url not in seen_urls:
            seen_urls.add(url)
            links.append({"anchor_text": url, "target_url": url})

    return links


class UniversalDocumentParser:
    """
    Unified dispatcher to parse any file type into normalized email/threat data.
    """

    @classmethod
    def parse_file(cls, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        Main entry point: Inspects file extension and routes to appropriate parser.
        """
        ext = os.path.splitext(filename)[1].lower()

        result: Dict[str, Any] = {
            "filename": filename,
            "extension": ext,
            "subject": "",
            "text": "",
            "html": "",
            "headers": {},
            "links": [],
            "attachments": [],
            "metadata": {}
        }

        try:
            if ext in [".eml", ".mbox"]:
                result = cls.parse_eml(file_bytes, filename)
            elif ext == ".msg":
                result = cls.parse_msg(file_bytes, filename)
            elif ext == ".pdf":
                result = cls.parse_pdf(file_bytes, filename)
            elif ext in [".docx", ".doc"]:
                result = cls.parse_docx(file_bytes, filename)
            elif ext in [".xlsx", ".xls", ".csv"]:
                result = cls.parse_spreadsheet(file_bytes, filename)
            elif ext in [".html", ".htm"]:
                result = cls.parse_html(file_bytes, filename)
            elif ext in [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"]:
                result = cls.parse_image(file_bytes, filename)
            else:
                # Default plaintext fallback (.txt, .json, .log, etc.)
                result = cls.parse_plaintext(file_bytes, filename)
        except Exception as e:
            # Safe degradation fallback
            raw_text = file_bytes.decode("utf-8", errors="ignore")
            result["text"] = raw_text
            result["links"] = extract_masked_links_from_text_and_html(raw_text)
            result["metadata"]["parse_warning"] = f"Processed with fallback extractor: {str(e)}"

        # Ensure links are populated if none were collected by specific parser
        if not result["links"]:
            combined_text = f"{result['subject']} {result['text']} {result.get('html', '')}"
            result["links"] = extract_masked_links_from_text_and_html(combined_text)

        return result

    @classmethod
    def parse_eml(cls, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Parses RFC 822 .eml or .mbox email files."""
        msg = email.message_from_bytes(file_bytes, policy=email.policy.default)

        subject = msg.get("Subject", "") or ""
        from_hdr = msg.get("From", "") or ""
        to_hdr = msg.get("To", "") or ""
        reply_to = msg.get("Reply-To", "") or ""
        date_hdr = msg.get("Date", "") or ""
        auth_results = msg.get("Authentication-Results", "") or ""

        headers = {
            "from": str(from_hdr),
            "to": str(to_hdr),
            "subject": str(subject),
            "reply-to": str(reply_to),
            "date": str(date_hdr),
            "authentication-results": str(auth_results)
        }

        body_plain_parts = []
        body_html_parts = []
        attachments = []

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))

                if "attachment" in content_disposition:
                    att_filename = part.get_filename() or "unnamed_attachment"
                    payload = part.get_payload(decode=True) or b""
                    attachments.append({
                        "filename": att_filename,
                        "size_bytes": len(payload),
                        "content_type": content_type
                    })
                elif content_type == "text/plain":
                    try:
                        body_plain_parts.append(part.get_content())
                    except Exception:
                        pass
                elif content_type == "text/html":
                    try:
                        body_html_parts.append(part.get_content())
                    except Exception:
                        pass
        else:
            if msg.get_content_type() == "text/html":
                body_html_parts.append(msg.get_content())
            else:
                body_plain_parts.append(msg.get_content())

        html_text = "\n".join(body_html_parts)
        plain_text = "\n".join(body_plain_parts)

        # If plain text is empty, convert HTML to readable plain text
        if not plain_text and html_text:
            soup = BeautifulSoup(html_text, "html.parser")
            plain_text = soup.get_text(separator="\n", strip=True)

        full_content = f"Subject: {subject}\nFrom: {from_hdr}\n\n{plain_text}"
        links = extract_masked_links_from_text_and_html(html_text or plain_text)

        return {
            "filename": filename,
            "extension": ".eml",
            "subject": str(subject),
            "text": full_content,
            "html": html_text,
            "headers": headers,
            "links": links,
            "attachments": attachments,
            "metadata": {"multipart": msg.is_multipart()}
        }

    @classmethod
    def parse_msg(cls, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Parses Microsoft Outlook .msg files."""
        if not HAS_EXTRACT_MSG:
            return cls.parse_plaintext(file_bytes, filename)

        msg_obj = extract_msg.Message(io.BytesIO(file_bytes))
        subject = msg_obj.subject or ""
        sender = msg_obj.sender or ""
        to_hdr = msg_obj.to or ""
        body = msg_obj.body or ""
        html_body = msg_obj.htmlBody or ""

        if isinstance(html_body, bytes):
            html_body = html_body.decode("utf-8", errors="ignore")

        headers = {
            "from": sender,
            "to": to_hdr,
            "subject": subject,
            "date": str(msg_obj.date or "")
        }

        attachments = []
        for att in msg_obj.attachments:
            att_name = att.longFilename or att.shortFilename or "attachment"
            att_size = len(att.data) if hasattr(att, "data") and att.data else 0
            attachments.append({
                "filename": att_name,
                "size_bytes": att_size,
                "content_type": getattr(att, "mimetype", "application/octet-stream")
            })

        full_content = f"Subject: {subject}\nFrom: {sender}\n\n{body}"
        links = extract_masked_links_from_text_and_html(html_body or body)

        return {
            "filename": filename,
            "extension": ".msg",
            "subject": subject,
            "text": full_content,
            "html": html_body,
            "headers": headers,
            "links": links,
            "attachments": attachments,
            "metadata": {"client": "Microsoft Outlook"}
        }

    @classmethod
    def parse_pdf(cls, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Parses PDF documents, extracting text and embedded /URI links from buttons/annotations."""
        if not HAS_PYPDF:
            return cls.parse_plaintext(file_bytes, filename)

        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        page_texts = []
        links: List[Dict[str, str]] = []
        seen_urls = set()

        for page_idx, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            page_texts.append(page_text)

            # Extract Annotations (/Annots) looking for clickable /URI links
            if "/Annots" in page:
                annots = page["/Annots"]
                if annots:
                    for annot_ref in annots:
                        try:
                            annot = annot_ref.get_object()
                            if annot.get("/Subtype") == "/Link":
                                action = annot.get("/A")
                                if action and action.get("/S") == "/URI":
                                    uri = str(action.get("/URI", "")).strip()
                                    if uri and uri not in seen_urls:
                                        seen_urls.add(uri)
                                        # Use page context or link label as anchor
                                        links.append({
                                            "anchor_text": f"PDF Page {page_idx + 1} Action Button",
                                            "target_url": uri
                                        })
                        except Exception:
                            pass

        full_text = "\n\n".join(page_texts)
        # Also extract any plaintext URLs in the PDF content
        more_links = extract_masked_links_from_text_and_html(full_text)
        for ml in more_links:
            if ml["target_url"] not in seen_urls:
                seen_urls.add(ml["target_url"])
                links.append(ml)

        meta = {}
        if reader.metadata:
            meta = {
                "author": str(reader.metadata.author or ""),
                "creator": str(reader.metadata.creator or ""),
                "title": str(reader.metadata.title or ""),
                "pages": len(reader.pages)
            }

        return {
            "filename": filename,
            "extension": ".pdf",
            "subject": meta.get("title", filename),
            "text": full_text,
            "html": "",
            "headers": {},
            "links": links,
            "attachments": [],
            "metadata": meta
        }

    @classmethod
    def parse_docx(cls, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Parses Microsoft Word (.docx) documents."""
        if not HAS_DOCX:
            return cls.parse_plaintext(file_bytes, filename)

        doc = docx.Document(io.BytesIO(file_bytes))
        paragraphs = [p.text for p in doc.paragraphs if p.text]
        table_texts = []
        for table in doc.tables:
            for row in table.rows:
                row_str = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                if row_str:
                    table_texts.append(row_str)

        full_text = "\n".join(paragraphs + table_texts)

        # Extract Hyperlinks from DOCX relationships
        links: List[Dict[str, str]] = []
        seen_urls = set()
        for rel in doc.part.rels.values():
            if "hyperlink" in rel.reltype:
                url = rel.target_ref
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    links.append({"anchor_text": "Embedded Word Hyperlink", "target_url": url})

        # Plaintext URLs
        for ml in extract_masked_links_from_text_and_html(full_text):
            if ml["target_url"] not in seen_urls:
                seen_urls.add(ml["target_url"])
                links.append(ml)

        return {
            "filename": filename,
            "extension": ".docx",
            "subject": filename,
            "text": full_text,
            "html": "",
            "headers": {},
            "links": links,
            "attachments": [],
            "metadata": {"paragraph_count": len(paragraphs)}
        }

    @classmethod
    def parse_spreadsheet(cls, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Parses Excel (.xlsx) and CSV spreadsheets."""
        ext = os.path.splitext(filename)[1].lower()
        if ext == ".csv":
            text = file_bytes.decode("utf-8", errors="ignore")
            links = extract_masked_links_from_text_and_html(text)
            return {
                "filename": filename,
                "extension": ".csv",
                "subject": filename,
                "text": text,
                "html": "",
                "headers": {},
                "links": links,
                "attachments": [],
                "metadata": {}
            }

        if not HAS_OPENPYXL:
            return cls.parse_plaintext(file_bytes, filename)

        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
        cells_text = []
        links: List[Dict[str, str]] = []
        seen_urls = set()

        for sheet in wb.sheetnames:
            ws = wb[sheet]
            for row in ws.iter_rows(values_only=False):
                for cell in row:
                    val = str(cell.value) if cell.value is not None else ""
                    if val:
                        cells_text.append(val)
                    if cell.hyperlink and cell.hyperlink.target:
                        target = str(cell.hyperlink.target).strip()
                        if target and target not in seen_urls:
                            seen_urls.add(target)
                            links.append({"anchor_text": val or "Spreadsheet Link", "target_url": target})

        full_text = " ".join(cells_text)
        for ml in extract_masked_links_from_text_and_html(full_text):
            if ml["target_url"] not in seen_urls:
                seen_urls.add(ml["target_url"])
                links.append(ml)

        return {
            "filename": filename,
            "extension": ext,
            "subject": filename,
            "text": full_text,
            "html": "",
            "headers": {},
            "links": links,
            "attachments": [],
            "metadata": {"sheets": wb.sheetnames}
        }

    @classmethod
    def parse_html(cls, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Parses HTML web pages and email exports."""
        html_content = file_bytes.decode("utf-8", errors="ignore")
        soup = BeautifulSoup(html_content, "html.parser")
        title = soup.title.string if soup.title else filename
        text = soup.get_text(separator="\n", strip=True)
        links = extract_masked_links_from_text_and_html(html_content)

        return {
            "filename": filename,
            "extension": ".html",
            "subject": title,
            "text": text,
            "html": html_content,
            "headers": {},
            "links": links,
            "attachments": [],
            "metadata": {"title": title}
        }

    @classmethod
    def parse_image(cls, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Parses images and screenshots via OCR."""
        image = Image.open(io.BytesIO(file_bytes))
        ocr_text = ""
        warning_msg = None

        if HAS_PYTESSERACT:
            try:
                ocr_text = pytesseract.image_to_string(image)
            except Exception as e:
                warning_msg = f"OCR binary notice: {str(e)}. Ensure Tesseract is installed for character extraction."
        else:
            warning_msg = "pytesseract not installed; using image metadata."

        if not ocr_text:
            ocr_text = f"[Image scanned: {filename}, dimensions: {image.width}x{image.height}, format: {image.format}]"

        links = extract_masked_links_from_text_and_html(ocr_text)

        metadata = {
            "image_size": f"{image.width}x{image.height}",
            "image_format": image.format,
            "ocr_extracted": bool(ocr_text and not warning_msg)
        }
        if warning_msg:
            metadata["ocr_note"] = warning_msg

        return {
            "filename": filename,
            "extension": os.path.splitext(filename)[1].lower(),
            "subject": f"Image Scan: {filename}",
            "text": ocr_text,
            "html": "",
            "headers": {},
            "links": links,
            "attachments": [],
            "metadata": metadata
        }

    @classmethod
    def parse_plaintext(cls, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Fallback for plaintext documents (.txt, .json, etc.)."""
        text = file_bytes.decode("utf-8", errors="ignore")
        links = extract_masked_links_from_text_and_html(text)

        return {
            "filename": filename,
            "extension": os.path.splitext(filename)[1].lower(),
            "subject": filename,
            "text": text,
            "html": "",
            "headers": {},
            "links": links,
            "attachments": [],
            "metadata": {}
        }
