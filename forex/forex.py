# -*- coding: utf-8 -*-
"""
Çoklu site analiz aracı
Analiz edilenler:
1) Türkçe dil desteği var mı?
2) İletişim bilgilerinde Türkiye telefon hattı var mı?
3) Üye olma / online üyelik / hesap sistemi var mı?

Çıktı:
- site_analiz_raporu.html

Kullanım:
1) urls.txt içine site adreslerini satır satır yaz:
   https://ornek1.com
   https://ornek2.com
   https://ornek3.com

2) Çalıştır:
   python site_analiz.py

Alternatif:
   python site_analiz.py https://site1.com https://site2.com

Gerekli paketler:
   pip install requests beautifulsoup4
"""

import os
import re
import sys
import html
import time
from urllib.parse import urljoin, urlparse, urldefrag
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup

# =========================
# AYARLAR
# =========================
URLS_FILE = "urls.txt"
OUTPUT_HTML = "site_analiz_raporu.html"
MAX_WORKERS = 5
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

TR_PHONE_HINT_PREFIXES = ("2", "3", "4", "5", "8", "9")  # Türkiye sabit/mobil/850 vb.

session = requests.Session()
session.headers.update(HEADERS)


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


def safe_filename_html(text: str) -> str:
    return html.escape(text or "")


def compact_list_html(items, limit=8):
    if not items:
        return "-"
    items = dedupe_keep_order(items)
    if len(items) > limit:
        shown = items[:limit]
        extra = len(items) - limit
        return "<br>".join(html.escape(x) for x in shown) + f"<br><em>... +{extra} adet daha</em>"
    return "<br>".join(html.escape(x) for x in items)


def fetch_url(url: str):
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

    if signals:
        return True, signals
    return False, []


def normalize_digits(raw: str) -> str:
    d = re.sub(r"\D", "", raw or "")
    if d.startswith("0090"):
        d = d[2:]  # 0090xxxx -> 90xxxx
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

    # tel: linkleri
    for a in soup.find_all("a", href=True):
        href = a.get("href", "").strip()
        if href.lower().startswith("tel:"):
            d = normalize_digits(href)
            if is_turkish_phone_strong(d):
                found.append(format_tr_phone(d))

    # ham metin
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

        # Şifre alanı
        if soup.find("input", attrs={"type": re.compile(r"password", re.I)}):
            signals.append("Şifre alanı bulundu")

        # Form analizi
        for form in soup.find_all("form"):
            form_html = str(form).lower()
            has_password = 'type="password"' in form_html or "password" in form_html
            has_email = ('type="email"' in form_html) or ("name=\"email\"" in form_html) or ("email" in form_html)
            action = (form.get("action") or "").lower()

            if has_password and has_email:
                signals.append("Email + şifre formu bulundu")
            elif has_password and any(k in action for k in ["login", "signin", "account", "register", "signup", "uye", "üye", "kayit", "kayıt"]):
                signals.append("Giriş / hesap formu bulundu")

        # Metin bazlı sinyaller
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

    if signals:
        return True, signals
    return False, []


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

    # Türkçe dil desteği
    tr_support, tr_evidence = detect_turkish_support(pages)
    result["turkish_support"] = tr_support
    result["turkish_support_evidence"] = tr_evidence

    # Türkiye telefon hattı
    phone_pages = pages[:]
    phone_numbers = []
    for p in phone_pages:
        html_text = p.get("html", "")
        if html_text:
            phone_numbers.extend(extract_turkish_phones_from_html(html_text))
    phone_numbers = dedupe_keep_order(phone_numbers)
    result["turkey_phone_numbers"] = phone_numbers
    result["turkey_phone"] = len(phone_numbers) > 0

    # Üyelik / online hesap
    membership, membership_evidence = detect_membership(pages, auth_links)
    result["membership"] = membership
    result["membership_evidence"] = membership_evidence

    return result


def badge(value: bool, yes_text="Evet", no_text="Hayır"):
    if value:
        return '<span class="badge yes">' + yes_text + '</span>'
    return '<span class="badge no">' + no_text + '</span>'


def build_html_report(results):
    created_at = time.strftime("%Y-%m-%d %H:%M:%S")

    rows = []
    for i, r in enumerate(results, start=1):
        rows.append(f"""
        <tr>
            <td>{i}</td>
            <td>
                <div><strong>{safe_filename_html(r["site"])}</strong></div>
                <div class="small"><a href="{html.escape(r["final_url"] or r["site"])}" target="_blank">{safe_filename_html(r["final_url"] or r["site"])}</a></div>
            </td>
            <td>{safe_filename_html(str(r["status_code"])) or "-"}</td>
            <td>{badge(r["turkish_support"])}</td>
            <td>{compact_list_html(r["turkish_support_evidence"], limit=6)}</td>
            <td>{badge(r["turkey_phone"])}</td>
            <td>{compact_list_html(r["turkey_phone_numbers"], limit=6)}</td>
            <td>{badge(r["membership"])}</td>
            <td>{compact_list_html(r["membership_evidence"], limit=6)}</td>
            <td>{compact_list_html(r["contact_links"], limit=5)}</td>
            <td>{compact_list_html(r["auth_links"], limit=5)}</td>
            <td>{safe_filename_html(r["error"]) if r["error"] else "-"}</td>
        </tr>
        """)

    html_doc = f"""<!DOCTYPE html>
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
        - Bu analiz HTML içeriği ve sayfa bağlantıları üzerinden heuristik olarak yapılır.<br>
        - JS ile sonradan yüklenen içeriklerde bazı bulgular kaçabilir.<br>
        - Türkiye telefon hattı için +90 / 0xxx yapısına göre tespit yapılır.<br>
        - Üyelik analizi; üye ol, hesap oluştur, giriş formu, şifre alanı ve hesap bağlantıları gibi sinyallere dayanır.
    </div>
</body>
</html>
"""
    return html_doc


def load_urls():
    # 1) Komut satırından geldiyse
    argv_urls = [normalize_url(x) for x in sys.argv[1:] if normalize_url(x)]
    if argv_urls:
        return dedupe_keep_order(argv_urls)

    # 2) urls.txt varsa
    if os.path.exists(URLS_FILE):
        urls = []
        with open(URLS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = normalize_url(line.strip())
                if line:
                    urls.append(line)
        urls = dedupe_keep_order(urls)
        if urls:
            return urls

    # 3) Kullanıcıdan al
    raw = input("URL'leri virgülle ayırarak veya satır satır girin: ").strip()
    if not raw:
        return []

    parts = re.split(r"[\n,;]+", raw)
    urls = [normalize_url(x) for x in parts if normalize_url(x)]
    return dedupe_keep_order(urls)


def main():
    urls = load_urls()
    if not urls:
        print("Analiz edilecek URL bulunamadı.")
        return

    print(f"Toplam {len(urls)} site analiz edilecek...")

    results = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_map = {executor.submit(analyze_site, url): url for url in urls}
        for future in as_completed(future_map):
            url = future_map[future]
            try:
                res = future.result()
                results.append(res)
                print(f"[OK] {url}")
            except Exception as e:
                print(f"[HATA] {url} -> {e}")
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

    # Giriş sırasına göre sırala
    result_map = {r["site"]: r for r in results}
    ordered_results = [result_map.get(normalize_url(u), result_map.get(u)) for u in urls]
    ordered_results = [r for r in ordered_results if r]

    report_html = build_html_report(ordered_results)
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(report_html)

    print(f"\nTamamlandı. HTML rapor oluşturuldu: {OUTPUT_HTML}")


if __name__ == "__main__":
    main()