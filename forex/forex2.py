# -*- coding: utf-8 -*-
import os
import re
import sys
import html
import time
import threading
import webbrowser
from pathlib import Path
from urllib.parse import urljoin, urlparse, urldefrag

import requests
from bs4 import BeautifulSoup

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText


# =========================
# AYARLAR
# =========================
REQUEST_TIMEOUT = 20
MAX_EXTRA_PAGES = 8

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

CONTACT_KEYWORDS = [
    "contact", "contact-us", "contactus", "contacts",
    "iletisim", "iletişim", "bize-ulasin", "bize-ulaşın",
    "support", "help", "yardim", "yardım", "customer-service",
    "customer-support", "reach-us", "about", "hakkimizda", "hakkımızda"
]

AUTH_KEYWORDS = [
    "register", "signup", "sign-up", "sign_up", "create-account",
    "createaccount", "my-account", "account", "login", "log-in",
    "signin", "sign-in", "member", "membership", "customer-portal",
    "portal", "uye", "üye", "uye-ol", "üye-ol", "kayit", "kayıt",
    "hesap", "hesap-olustur", "hesap-oluştur", "giris", "giriş",
    "oturum", "b2b", "dealer-login", "bayi", "musteri", "müşteri"
]

LANG_KEYWORDS = [
    "turkce", "türkçe", "turkish", "language", "lang", "locale"
]

TR_PHONE_HINT_PREFIXES = ("2", "3", "4", "5", "8", "9")


# =========================
# YARDIMCI FONKSİYONLAR
# =========================
def normalize_url(url: str) -> str:
    url = (url or "").strip()
    if not url:
        return ""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


def strip_www(host: str) -> str:
    host = (host or "").lower().strip()
    if host.startswith("www."):
        host = host[4:]
    return host


def same_domain(url1: str, url2: str) -> bool:
    try:
        h1 = strip_www(urlparse(url1).netloc)
        h2 = strip_www(urlparse(url2).netloc)
        return h1 == h2 or h1.endswith("." + h2) or h2.endswith("." + h1)
    except Exception:
        return False


def dedupe_keep_order(items):
    seen = set()
    out = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out


def clean_text(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def get_soup(html_text: str):
    try:
        return BeautifulSoup(html_text, "html.parser")
    except Exception:
        return BeautifulSoup("", "html.parser")


def extract_page_text(soup: BeautifulSoup) -> str:
    return clean_text(soup.get_text(" ", strip=True))


def absolutize(base_url: str, href: str) -> str:
    if not href:
        return ""
    href = href.strip()
    href, _ = urldefrag(href)
    return urljoin(base_url, href)


def looks_like_turkish_text(text: str) -> bool:
    if not text:
        return False

    txt = " " + text.lower() + " "
    common_words = [
        " için ", " ürün ", " iletişim ", " kampanya ", " sepet ",
        " giriş ", " üye ", " üyelik ", " hesabım ", " hakkımızda ",
        " destek ", " teslimat ", " ödeme ", " sipariş ", " müşteri "
    ]
    score = sum(1 for w in common_words if w in txt)
    tr_chars = sum(txt.count(c) for c in "çğıöşü")

    return score >= 3 or tr_chars >= 15


def fetch_url(url: str):
    session = requests.Session()
    session.headers.update(HEADERS)

    result = {
        "requested_url": url,
        "final_url": url,
        "status_code": None,
        "html": "",
        "error": "",
        "content_type": "",
    }

    try:
        resp = session.get(url, timeout=REQUEST_TIMEOUT, allow_redirects=True)
        result["final_url"] = resp.url
        result["status_code"] = resp.status_code
        result["content_type"] = resp.headers.get("Content-Type", "")
        if "text/html" in result["content_type"].lower() or "<html" in resp.text.lower():
            resp.encoding = resp.encoding or resp.apparent_encoding or "utf-8"
            result["html"] = resp.text
        else:
            result["error"] = f"HTML olmayan içerik: {result['content_type']}"
    except requests.exceptions.SSLError as e:
        result["error"] = f"SSL hatası: {e}"
    except requests.exceptions.Timeout:
        result["error"] = "Zaman aşımı"
    except requests.exceptions.RequestException as e:
        result["error"] = f"İstek hatası: {e}"
    except Exception as e:
        result["error"] = f"Beklenmeyen hata: {e}"

    return result


def collect_relevant_links(base_url: str, soup: BeautifulSoup):
    contact_links = []
    auth_links = []
    lang_links = []

    for a in soup.find_all("a", href=True):
        href = a.get("href", "").strip()
        abs_url = absolutize(base_url, href)
        if not abs_url.startswith(("http://", "https://")):
            continue
        if not same_domain(base_url, abs_url):
            continue

        text = " ".join([
            a.get_text(" ", strip=True) or "",
            a.get("title", "") or "",
            a.get("aria-label", "") or "",
            href
        ]).lower()

        if any(k in text for k in CONTACT_KEYWORDS):
            contact_links.append(abs_url)

        if any(k in text for k in AUTH_KEYWORDS):
            auth_links.append(abs_url)

        if any(k in text for k in LANG_KEYWORDS):
            lang_links.append(abs_url)

        if re.search(r'([/?=&]|^)(lang|locale|language)=tr([&#/]|$)', abs_url.lower()):
            lang_links.append(abs_url)
        if re.search(r'/(tr|tr-tr|tr_tr)(/|$|\?)', abs_url.lower()):
            lang_links.append(abs_url)

    return {
        "contact_links": dedupe_keep_order(contact_links),
        "auth_links": dedupe_keep_order(auth_links),
        "lang_links": dedupe_keep_order(lang_links),
    }


def detect_turkish_support(pages):
    signals = []

    for page in pages:
        html_text = page.get("html", "")
        if not html_text:
            continue

        soup = get_soup(html_text)
        page_text = extract_page_text(soup)

        html_tag = soup.find("html")
        if html_tag:
            lang_attr = (html_tag.get("lang") or "").lower().strip()
            if lang_attr.startswith("tr"):
                signals.append(f"HTML lang='{lang_attr}'")

        for tag in soup.find_all(attrs={"hreflang": True}):
            hreflang = (tag.get("hreflang") or "").lower().strip()
            if hreflang.startswith("tr"):
                signals.append(f"hreflang='{hreflang}'")

        for tag in soup.find_all(["a", "button", "option"]):
            txt = clean_text(tag.get_text(" ", strip=True)).lower()
            href = (tag.get("href") or "").lower()
            combined = f"{txt} {href}"
            if "türkçe" in combined or "turkce" in combined:
                signals.append("Dil seçicide Türkçe ifadesi bulundu")
            if re.search(r'([/?=&]|^)(lang|locale|language)=tr([&#/]|$)', combined):
                signals.append("URL parametresinde lang=tr bulundu")
            if re.search(r'/(tr|tr-tr|tr_tr)(/|$|\?)', combined):
                signals.append("TR dil yolu bulundu")

        current_url = (page.get("final_url") or "").lower()
        if re.search(r'([/?=&]|^)(lang|locale|language)=tr([&#/]|$)', current_url):
            signals.append("Sayfa URL'sinde lang=tr bulundu")
        if re.search(r'/(tr|tr-tr|tr_tr)(/|$|\?)', current_url):
            signals.append("Sayfa URL'sinde /tr bulundu")

        if looks_like_turkish_text(page_text):
            signals.append("Sayfa metni Türkçe görünüyor")

    signals = dedupe_keep_order(signals)
    return (len(signals) > 0), signals


def normalize_digits(raw: str) -> str:
    d = re.sub(r"\D", "", raw or "")
    if d.startswith("0090"):
        d = d[2:]
    return d


def is_turkish_phone_strong(digits: str) -> bool:
    if digits.startswith("90") and len(digits) == 12 and digits[2] in TR_PHONE_HINT_PREFIXES:
        return True
    if digits.startswith("0") and len(digits) == 11 and digits[1] in TR_PHONE_HINT_PREFIXES:
        return True
    return False


def format_tr_phone(digits: str) -> str:
    if digits.startswith("90") and len(digits) == 12:
        x = digits[2:]
        return f"+90 {x[0:3]} {x[3:6]} {x[6:8]} {x[8:10]}"
    if digits.startswith("0") and len(digits) == 11:
        x = digits[1:]
        return f"0{x[0:3]} {x[3:6]} {x[6:8]} {x[8:10]}"
    return digits


def extract_turkish_phones_from_html(html_text: str):
    soup = get_soup(html_text)
    found = []

    for a in soup.find_all("a", href=True):
        href = a.get("href", "").strip()
        if href.lower().startswith("tel:"):
            d = normalize_digits(href)
            if is_turkish_phone_strong(d):
                found.append(format_tr_phone(d))

    text = extract_page_text(soup)
    candidates = re.findall(r'(?:\+|00)?90[\d\s\-\(\)]{8,25}|0[\d\s\-\(\)]{9,25}', text)
    for c in candidates:
        d = normalize_digits(c)
        if is_turkish_phone_strong(d):
            found.append(format_tr_phone(d))

    return dedupe_keep_order(found)


def detect_membership(pages, auth_links):
    signals = []

    if auth_links:
        signals.append("Üyelik / hesap bağlantıları bulundu")

    for page in pages:
        html_text = page.get("html", "")
        if not html_text:
            continue

        soup = get_soup(html_text)
        text = extract_page_text(soup).lower()

        if soup.find("input", attrs={"type": re.compile(r"password", re.I)}):
            signals.append("Şifre alanı bulundu")

        for form in soup.find_all("form"):
            form_html = str(form).lower()
            has_password = 'type="password"' in form_html or "password" in form_html
            has_email = ('type="email"' in form_html) or ('name="email"' in form_html) or ("email" in form_html)
            action = (form.get("action") or "").lower()

            if has_password and has_email:
                signals.append("Email + şifre formu bulundu")
            elif has_password and any(
                k in action for k in [
                    "login", "signin", "account", "register",
                    "signup", "uye", "üye", "kayit", "kayıt"
                ]
            ):
                signals.append("Giriş / hesap formu bulundu")

        phrases = [
            "sign up", "signup", "register", "create account", "my account", "customer login",
            "member", "membership", "portal", "online account",
            "üye ol", "üyelik", "kayıt ol", "hesap oluştur", "giriş yap",
            "müşteri girişi", "bayi girişi", "oturum aç", "hesabım"
        ]
        for phrase in phrases:
            if phrase in text:
                signals.append(f"'{phrase}' ifadesi bulundu")

    signals = dedupe_keep_order(signals)
    return (len(signals) > 0), signals


def analyze_site(url: str):
    result = {
        "site": url,
        "final_url": "",
        "status_code": "",
        "turkish_support": False,
        "turkish_support_evidence": [],
        "turkey_phone": False,
        "turkey_phone_numbers": [],
        "membership": False,
        "membership_evidence": [],
        "contact_links": [],
        "auth_links": [],
        "lang_links": [],
        "scanned_pages": [],
        "error": "",
    }

    base = normalize_url(url)
    result["site"] = base

    main = fetch_url(base)
    result["final_url"] = main.get("final_url") or base
    result["status_code"] = main.get("status_code") or ""
    result["error"] = main.get("error", "")

    if not main.get("html"):
        return result

    main_soup = get_soup(main["html"])
    link_groups = collect_relevant_links(result["final_url"], main_soup)

    contact_links = link_groups["contact_links"][:4]
    auth_links = link_groups["auth_links"][:4]
    lang_links = link_groups["lang_links"][:3]

    result["contact_links"] = contact_links
    result["auth_links"] = auth_links
    result["lang_links"] = lang_links

    extra_links = dedupe_keep_order(contact_links + auth_links + lang_links)[:MAX_EXTRA_PAGES]

    pages = [main]
    result["scanned_pages"].append(result["final_url"])

    for link in extra_links:
        page = fetch_url(link)
        pages.append(page)
        result["scanned_pages"].append(page.get("final_url") or link)

    tr_support, tr_evidence = detect_turkish_support(pages)
    result["turkish_support"] = tr_support
    result["turkish_support_evidence"] = tr_evidence

    phone_numbers = []
    for p in pages:
        html_text = p.get("html", "")
        if html_text:
            phone_numbers.extend(extract_turkish_phones_from_html(html_text))
    phone_numbers = dedupe_keep_order(phone_numbers)
    result["turkey_phone_numbers"] = phone_numbers
    result["turkey_phone"] = len(phone_numbers) > 0

    membership, membership_evidence = detect_membership(pages, auth_links)
    result["membership"] = membership
    result["membership_evidence"] = membership_evidence

    return result


def compact_list_html(items, limit=8):
    if not items:
        return "-"
    items = dedupe_keep_order(items)
    if len(items) > limit:
        shown = items[:limit]
        extra = len(items) - limit
        return "<br>".join(html.escape(x) for x in shown) + f"<br><em>... +{extra} adet daha</em>"
    return "<br>".join(html.escape(x) for x in items)


def badge_html(value: bool, yes_text="Evet", no_text="Hayır"):
    if value:
        return f'<span class="badge yes">{yes_text}</span>'
    return f'<span class="badge no">{no_text}</span>'


def build_html_report(results):
    created_at = time.strftime("%Y-%m-%d %H:%M:%S")

    rows = []
    for i, r in enumerate(results, start=1):
        site_link = html.escape(r["final_url"] or r["site"])
        site_title = html.escape(r["site"])
        final_url_text = html.escape(r["final_url"] or r["site"])

        rows.append(f"""
        <tr>
            <td>{i}</td>
            <td>
                <div><strong>{site_title}</strong></div>
                <div class="small"><a href="{site_link}" target="_blank">{final_url_text}</a></div>
            </td>
            <td>{html.escape(str(r["status_code"])) if r["status_code"] else "-"}</td>
            <td>{badge_html(r["turkish_support"])}</td>
            <td>{compact_list_html(r["turkish_support_evidence"], 6)}</td>
            <td>{badge_html(r["turkey_phone"])}</td>
            <td>{compact_list_html(r["turkey_phone_numbers"], 6)}</td>
            <td>{badge_html(r["membership"])}</td>
            <td>{compact_list_html(r["membership_evidence"], 6)}</td>
            <td>{compact_list_html(r["contact_links"], 5)}</td>
            <td>{compact_list_html(r["auth_links"], 5)}</td>
            <td>{html.escape(r["error"]) if r["error"] else "-"}</td>
        </tr>
        """)

    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="utf-8">
<title>Site Analiz Raporu</title>
<style>
    body {{
        font-family: Arial, Helvetica, sans-serif;
        font-size: 14px;
        color: #222;
        margin: 20px;
        background: #f7f7f7;
    }}
    h1 {{
        margin-bottom: 8px;
    }}
    .meta {{
        margin-bottom: 16px;
        color: #555;
    }}
    table {{
        width: 100%;
        border-collapse: collapse;
        background: #fff;
    }}
    th, td {{
        border: 1px solid #dcdcdc;
        padding: 8px 10px;
        vertical-align: top;
        text-align: left;
    }}
    th {{
        background: #efefef;
        position: sticky;
        top: 0;
    }}
    tr:nth-child(even) {{
        background: #fafafa;
    }}
    .badge {{
        display: inline-block;
        padding: 4px 8px;
        border-radius: 12px;
        font-weight: 700;
        font-size: 12px;
        color: #fff;
    }}
    .yes {{ background: #138a36; }}
    .no {{ background: #b42318; }}
    .small {{
        font-size: 12px;
        color: #666;
        margin-top: 4px;
        word-break: break-all;
    }}
    a {{
        color: #0b57d0;
        text-decoration: none;
    }}
    a:hover {{
        text-decoration: underline;
    }}
    .note {{
        margin-top: 14px;
        font-size: 12px;
        color: #555;
        background: #fff;
        border: 1px solid #ddd;
        padding: 12px;
    }}
</style>
</head>
<body>
    <h1>Site Analiz Raporu</h1>
    <div class="meta">
        Oluşturulma zamanı: <strong>{created_at}</strong><br>
        Toplam site sayısı: <strong>{len(results)}</strong>
    </div>

    <table>
        <thead>
            <tr>
                <th>#</th>
                <th>Site</th>
                <th>HTTP</th>
                <th>Türkçe Desteği</th>
                <th>Türkçe Desteği Bulguları</th>
                <th>Türkiye Telefonu</th>
                <th>Bulunan Telefonlar</th>
                <th>Üyelik / Online Hesap</th>
                <th>Üyelik Bulguları</th>
                <th>İletişim Sayfaları</th>
                <th>Üyelik Sayfaları</th>
                <th>Hata / Not</th>
            </tr>
        </thead>
        <tbody>
            {''.join(rows)}
        </tbody>
    </table>

    <div class="note">
        <strong>Not:</strong><br>
        - Analiz HTML ve bağlantı sinyallerine göre yapılır.<br>
        - JS ile sonradan yüklenen bazı üyelik veya telefon bilgileri kaçabilir.<br>
        - Türkiye hattı için +90 ve 0 ile başlayan formatlar kontrol edilir.
    </div>
</body>
</html>
"""


# =========================
# GUI
# =========================
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Site Analiz Aracı")
        self.root.geometry("1100x760")

        default_output = str(Path.cwd() / "site_analiz_raporu.html")
        self.output_path_var = tk.StringVar(value=default_output)
        self.open_after_var = tk.BooleanVar(value=True)
        self.is_running = False

        self.build_ui()

    def build_ui(self):
        top_frame = ttk.Frame(self.root, padding=10)
        top_frame.pack(fill="x")

        title = ttk.Label(
            top_frame,
            text="Site Analiz Aracı",
            font=("Segoe UI", 16, "bold")
        )
        title.pack(anchor="w")

        desc = ttk.Label(
            top_frame,
            text="URL'leri alt alta gir. Program Türkçe desteği, Türkiye telefon hattı ve üyelik sistemi olup olmadığını analiz eder.",
            wraplength=1000
        )
        desc.pack(anchor="w", pady=(4, 10))

        input_frame = ttk.LabelFrame(self.root, text="Site URL Listesi", padding=10)
        input_frame.pack(fill="both", expand=False, padx=10, pady=(0, 10))

        self.urls_text = ScrolledText(input_frame, height=12, font=("Consolas", 10))
        self.urls_text.pack(fill="both", expand=True)
        self.urls_text.insert(
            "1.0",
            "https://example.com\nhttps://example.org\n"
        )

        output_frame = ttk.LabelFrame(self.root, text="Çıktı Ayarları", padding=10)
        output_frame.pack(fill="x", padx=10, pady=(0, 10))

        ttk.Label(output_frame, text="HTML çıktı dosyası:").grid(row=0, column=0, sticky="w")
        self.output_entry = ttk.Entry(output_frame, textvariable=self.output_path_var, width=80)
        self.output_entry.grid(row=0, column=1, padx=8, pady=5, sticky="we")

        browse_btn = ttk.Button(output_frame, text="Kaydet Yeri Seç", command=self.choose_output_file)
        browse_btn.grid(row=0, column=2, padx=5, pady=5)

        open_check = ttk.Checkbutton(
            output_frame,
            text="İşlem bitince HTML raporu aç",
            variable=self.open_after_var
        )
        open_check.grid(row=1, column=1, sticky="w", pady=4)

        output_frame.columnconfigure(1, weight=1)

        button_frame = ttk.Frame(self.root, padding=(10, 0))
        button_frame.pack(fill="x")

        self.start_btn = ttk.Button(button_frame, text="Analizi Başlat", command=self.start_analysis)
        self.start_btn.pack(side="left")

        self.clear_btn = ttk.Button(button_frame, text="URL Alanını Temizle", command=self.clear_urls)
        self.clear_btn.pack(side="left", padx=8)

        self.sample_btn = ttk.Button(button_frame, text="Örnek URL Ekle", command=self.insert_sample_urls)
        self.sample_btn.pack(side="left")

        self.progress = ttk.Progressbar(button_frame, mode="indeterminate", length=220)
        self.progress.pack(side="right")

        log_frame = ttk.LabelFrame(self.root, text="İşlem Günlüğü", padding=10)
        log_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.log_text = ScrolledText(log_frame, height=18, font=("Consolas", 10), state="disabled")
        self.log_text.pack(fill="both", expand=True)

    def log(self, msg):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"{time.strftime('%H:%M:%S')} - {msg}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
        self.root.update_idletasks()

    def choose_output_file(self):
        path = filedialog.asksaveasfilename(
            title="HTML çıktı dosyasını seç",
            defaultextension=".html",
            filetypes=[("HTML Dosyası", "*.html"), ("Tüm Dosyalar", "*.*")]
        )
        if path:
            self.output_path_var.set(path)

    def clear_urls(self):
        self.urls_text.delete("1.0", "end")

    def insert_sample_urls(self):
        self.urls_text.insert("end", "https://example.net\n")

    def parse_urls(self):
        raw = self.urls_text.get("1.0", "end").strip()
        lines = [x.strip() for x in raw.splitlines()]
        urls = [normalize_url(x) for x in lines if normalize_url(x)]
        return dedupe_keep_order(urls)

    def start_analysis(self):
        if self.is_running:
            return

        urls = self.parse_urls()
        if not urls:
            messagebox.showwarning("Uyarı", "Lütfen en az bir site adresi gir.")
            return

        output_path = self.output_path_var.get().strip()
        if not output_path:
            messagebox.showwarning("Uyarı", "Lütfen çıktı dosya adını belirt.")
            return

        self.is_running = True
        self.start_btn.configure(state="disabled")
        self.progress.start(10)
        self.log("Analiz başladı.")
        self.log(f"Toplam site: {len(urls)}")

        t = threading.Thread(target=self.run_analysis, args=(urls, output_path), daemon=True)
        t.start()

    def finish_analysis(self):
        self.is_running = False
        self.start_btn.configure(state="normal")
        self.progress.stop()

    def run_analysis(self, urls, output_path):
        try:
            results = []
            total = len(urls)

            for idx, url in enumerate(urls, start=1):
                self.root.after(0, self.log, f"[{idx}/{total}] Analiz ediliyor: {url}")
                try:
                    res = analyze_site(url)
                    results.append(res)

                    summary = []
                    summary.append("TR dil: Evet" if res["turkish_support"] else "TR dil: Hayır")
                    summary.append("TR tel: Evet" if res["turkey_phone"] else "TR tel: Hayır")
                    summary.append("Üyelik: Evet" if res["membership"] else "Üyelik: Hayır")

                    self.root.after(0, self.log, f"Tamamlandı: {url} | " + " | ".join(summary))
                except Exception as e:
                    self.root.after(0, self.log, f"Hata: {url} -> {e}")
                    results.append({
                        "site": url,
                        "final_url": url,
                        "status_code": "",
                        "turkish_support": False,
                        "turkish_support_evidence": [],
                        "turkey_phone": False,
                        "turkey_phone_numbers": [],
                        "membership": False,
                        "membership_evidence": [],
                        "contact_links": [],
                        "auth_links": [],
                        "lang_links": [],
                        "scanned_pages": [],
                        "error": str(e),
                    })

            report_html = build_html_report(results)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(report_html)

            self.root.after(0, self.log, f"HTML rapor oluşturuldu: {output_path}")

            if self.open_after_var.get():
                try:
                    abs_path = Path(output_path).resolve()

                    if sys.platform.startswith("win"):
                        os.startfile(str(abs_path))
                    else:
                        webbrowser.open(abs_path.as_uri())

                    self.root.after(0, self.log, f"HTML rapor açıldı: {abs_path}")
                except Exception as e:
                    self.root.after(0, self.log, f"Rapor açılamadı: {e}")

            self.root.after(
                0,
                lambda: messagebox.showinfo("Tamam", f"Analiz tamamlandı.\n\nÇıktı:\n{output_path}")
            )
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Hata", str(e)))
            self.root.after(0, self.log, f"Genel hata: {e}")
        finally:
            self.root.after(0, self.finish_analysis)


if __name__ == "__main__":
    root = tk.Tk()
    try:
        style = ttk.Style()
        if "vista" in style.theme_names():
            style.theme_use("vista")
        elif "clam" in style.theme_names():
            style.theme_use("clam")
    except Exception:
        pass

    app = App(root)
    root.mainloop()