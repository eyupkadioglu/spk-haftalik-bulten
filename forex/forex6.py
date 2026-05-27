import os
import re
import sys
import time
import html
import gzip
import zlib
import random
import threading
import webbrowser
from pathlib import Path
from urllib.parse import urljoin, urlparse, urldefrag, parse_qs, unquote

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup

try:
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
    PLAYWRIGHT_IMPORT_ERROR = ""
except Exception as _playwright_import_error:
    PlaywrightTimeoutError = Exception
    sync_playwright = None
    PLAYWRIGHT_AVAILABLE = False
    PLAYWRIGHT_IMPORT_ERROR = re.sub(r"\s+", " ", str(_playwright_import_error)).strip()

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText


# =========================
# SETTINGS
# =========================
CONNECT_TIMEOUT = 10
READ_TIMEOUT = 30
MAX_EXTRA_PAGES = 4
PLAYWRIGHT_NAV_TIMEOUT_MS = 45000
PLAYWRIGHT_IDLE_TIMEOUT_MS = 5000

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) "
    "Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
]

BASE_HEADERS = {
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Upgrade-Insecure-Requests": "1",
    "DNT": "1",
}

BLOCK_PAGE_HOSTS = {
    "aidiyet.esb.org.tr",
}

CONTACT_KEYWORDS = [
    "contact", "contact-us", "contactus", "contacts",
    "iletisim", "bize-ulasin", "support", "help", "yardim",
    "customer-service", "customer-support", "reach-us", "about", "hakkimizda"
]

AUTH_KEYWORDS = [
    "register", "signup", "sign-up", "sign_up", "create-account",
    "createaccount", "my-account", "account", "login", "log-in",
    "signin", "sign-in", "member", "membership", "customer-portal",
    "portal", "uye", "uye-ol", "kayit", "hesap", "hesap-olustur",
    "giris", "oturum", "b2b", "dealer-login", "bayi", "musteri"
]

LANG_KEYWORDS = [
    "turkce", "turkish", "language", "lang", "locale"
]

TR_PHONE_HINT_PREFIXES = ("2", "3", "4", "5", "8", "9")


# =========================
# HELPERS
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


def normalize_search_text(text: str) -> str:
    if not text:
        return ""

    translation = str.maketrans({
        "ç": "c", "Ç": "c",
        "ğ": "g", "Ğ": "g",
        "ı": "i", "I": "i", "İ": "i",
        "ö": "o", "Ö": "o",
        "ş": "s", "Ş": "s",
        "ü": "u", "Ü": "u",
    })
    normalized = text.translate(translation).lower()
    return re.sub(r"\s+", " ", normalized).strip()


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


def extract_lang_candidates_from_html(base_url: str, html_text: str):
    if not html_text:
        return []

    candidates = []
    patterns = [
        r"""https?://[^\s"'<>]+/(?:tr|tr-tr|tr_tr)(?:[/?#][^\s"'<>]*)?""",
        r"""[/"'](?:tr|tr-tr|tr_tr)(?:/[^\s"'<>]*)?""",
        r"""https?://[^\s"'<>]+[?&](?:lang|locale|language)=tr(?:[&#][^\s"'<>]*)?""",
        r"""[/"'][^\s"'<>]*[?&](?:lang|locale|language)=tr(?:[&#][^\s"'<>]*)?""",
    ]

    for pattern in patterns:
        for match in re.findall(pattern, html_text, flags=re.I):
            cleaned = str(match).strip('\'"')
            abs_url = absolutize(base_url, cleaned)
            if abs_url.startswith(("http://", "https://")) and same_domain(base_url, abs_url):
                candidates.append(abs_url)

    return dedupe_keep_order(candidates)


def looks_like_turkish_text(text: str) -> bool:
    if not text:
        return False

    txt = " " + normalize_search_text(text) + " "
    common_words = [
        " icin ", " urun ", " iletisim ", " kampanya ", " sepet ",
        " giris ", " uye ", " uyelik ", " hesabim ", " hakkimizda ",
        " destek ", " teslimat ", " odeme ", " siparis ", " musteri "
    ]
    score = sum(1 for w in common_words if w in txt)

    tr_like_words = [
        "turkiye", "turkce", "giris", "hesap", "kayit",
        "musteri", "iletisim", "satis", "destek"
    ]
    score += sum(1 for w in tr_like_words if w in txt)

    return score >= 4


def clean_exception_message(exc) -> str:
    text = str(exc).strip()
    text = re.sub(r"\s+", " ", text)
    return text[:1000] if len(text) > 1000 else text


def merge_warnings(*parts):
    items = []
    for part in parts:
        if not part:
            continue
        for piece in str(part).split(" | "):
            piece = piece.strip()
            if piece and piece not in items:
                items.append(piece)
    return " | ".join(items)


def classify_site_status(result) -> str:
    if not result:
        return "Bilinmiyor"

    if result.get("blocked_by_filter"):
        return "Engelli"

    error_text = normalize_search_text(result.get("error", ""))
    warning_text = normalize_search_text(result.get("warning", ""))
    combined = f"{error_text} {warning_text}".strip()
    status_code = result.get("status_code")

    if result.get("html"):
        if status_code in (403, 406, 429):
            return "Bot korumasi"
        return "Basarili"

    if "zaman asimi" in combined or "timeout" in combined:
        return "Zaman asimi"

    if any(x in combined for x in [
        "site istegi engelliyor olabilir",
        "access denied",
        "forbidden",
        "cloudflare",
        "captcha",
        "ddos",
        "browser",
        "bot",
        "playwright fallback kullanildi",
        "playwright ile sayfa yuklendi ama http 403 dondu",
        "playwright ile sayfa yuklendi ama http 406 dondu",
        "playwright ile sayfa yuklendi ama http 429 dondu",
    ]):
        return "Bot korumasi"

    if any(x in combined for x in [
        "baglanti hatasi",
        "connection reset",
        "connection aborted",
        "uzak sunucu baglantiyi kapatti",
        "connectionpool",
    ]):
        return "Baglanti reddi"

    if isinstance(status_code, int) and status_code >= 400:
        return "Hata"

    return "Dogrulanamadi"


def is_block_page_url(url: str) -> bool:
    try:
        parsed = urlparse(url or "")
        host = (parsed.netloc or "").lower().strip()
        path = (parsed.path or "").lower().strip()
        return host in BLOCK_PAGE_HOSTS and "landpage" in path
    except Exception:
        return False


def extract_original_target_from_block_url(url: str) -> str:
    try:
        parsed = urlparse(url or "")
        qs = parse_qs(parsed.query or "")
        ms_values = qs.get("ms", [])
        if ms_values:
            return unquote(ms_values[0])
    except Exception:
        pass
    return ""


def make_session(user_agent=None):
    session = requests.Session()

    retry = Retry(
        total=3,
        connect=3,
        read=3,
        redirect=2,
        status=3,
        backoff_factor=1.2,
        allowed_methods=frozenset(["GET", "HEAD", "OPTIONS"]),
        status_forcelist=[429, 500, 502, 503, 504],
        raise_on_status=False,
        respect_retry_after_header=True,
    )

    adapter = HTTPAdapter(
        max_retries=retry,
        pool_connections=10,
        pool_maxsize=10,
    )

    session.mount("http://", adapter)
    session.mount("https://", adapter)

    headers = BASE_HEADERS.copy()
    headers.update(make_request_headers(user_agent=user_agent))
    session.headers.update(headers)

    return session


def make_request_headers(url: str = "", referer: str = "", user_agent=None):
    ua = user_agent or random.choice(USER_AGENTS)
    parsed = urlparse(url or "")
    origin = f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else ""

    headers = {
        "User-Agent": ua,
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none" if not referer else "same-origin",
        "Sec-Fetch-User": "?1",
    }

    if referer:
        headers["Referer"] = referer
    if origin:
        headers["Origin"] = origin

    ua_lower = ua.lower()
    if "firefox" in ua_lower:
        headers["TE"] = "trailers"
    else:
        headers["Sec-CH-UA"] = '"Chromium";v="124", "Not.A/Brand";v="24", "Google Chrome";v="124"'
        headers["Sec-CH-UA-Mobile"] = "?0"
        headers["Sec-CH-UA-Platform"] = '"Windows"'

    return headers


def prime_session(session, url: str):
    parsed = urlparse(url or "")
    if not parsed.scheme or not parsed.netloc:
        return

    homepage = f"{parsed.scheme}://{parsed.netloc}/"
    try:
        time.sleep(random.uniform(0.8, 1.4))
        session.get(
            homepage,
            timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
            allow_redirects=True,
            verify=True,
        )
    except Exception:
        pass


def should_try_playwright(result) -> bool:
    if not result or result.get("html") or result.get("blocked_by_filter"):
        return False

    if result.get("status_code") in (403, 406, 429):
        return True

    err = normalize_search_text(result.get("error", ""))
    suspicious_fragments = [
        "site istegi engelliyor olabilir",
        "access denied",
        "forbidden",
        "cloudflare",
        "ddos",
        "captcha",
        "javascript",
        "browser",
        "bot",
    ]
    return any(fragment in err for fragment in suspicious_fragments)


def build_playwright_unavailable_warning():
    msg = "Playwright fallback atlandi: playwright kurulu degil"
    if PLAYWRIGHT_IMPORT_ERROR:
        msg += f" ({PLAYWRIGHT_IMPORT_ERROR})"
    return msg


def fetch_with_playwright(url: str, referer: str = "", user_agent=None):
    result = {
        "requested_url": url,
        "final_url": url,
        "status_code": None,
        "html": "",
        "error": "",
        "warning": "",
        "content_type": "",
        "blocked_by_filter": False,
        "blocked_target": "",
    }

    if not PLAYWRIGHT_AVAILABLE:
        result["warning"] = build_playwright_unavailable_warning()
        result["error"] = "Playwright fallback kullanilamadi"
        return result

    ua = user_agent or random.choice(USER_AGENTS)

    try:
        time.sleep(random.uniform(1.0, 2.0))

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=ua,
                locale="tr-TR",
                ignore_https_errors=False,
                viewport={"width": 1440, "height": 900},
                extra_http_headers=make_request_headers(url=url, referer=referer, user_agent=ua),
            )

            page = context.new_page()
            page.set_default_navigation_timeout(PLAYWRIGHT_NAV_TIMEOUT_MS)

            response = page.goto(
                url,
                wait_until="domcontentloaded",
                referer=referer or None,
                timeout=PLAYWRIGHT_NAV_TIMEOUT_MS,
            )

            try:
                page.wait_for_load_state("networkidle", timeout=PLAYWRIGHT_IDLE_TIMEOUT_MS)
            except PlaywrightTimeoutError:
                pass

            result["final_url"] = page.url or url
            if response:
                result["status_code"] = response.status
                result["content_type"] = response.headers.get("content-type", "")

            if is_block_page_url(result["final_url"]):
                result["blocked_by_filter"] = True
                result["blocked_target"] = extract_original_target_from_block_url(result["final_url"])
                result["error"] = "ESB / erisim engeli sayfasina yonlendirildi"
                if result["blocked_target"]:
                    result["warning"] = f"Orijinal hedef: {result['blocked_target']}"
                context.close()
                browser.close()
                return result

            html_text = page.content()
            if html_text and ("text/html" in result["content_type"].lower() or "<html" in html_text.lower() or not result["content_type"]):
                result["html"] = html_text
                if response and response.status in (403, 406, 429):
                    result["warning"] = f"Playwright ile sayfa yuklendi ama HTTP {response.status} dondu"
                    result["error"] = ""
            else:
                result["error"] = "Playwright HTML icerigi alamadi"

            context.close()
            browser.close()

    except PlaywrightTimeoutError:
        result["error"] = "Playwright zaman asimi"
    except Exception as e:
        result["error"] = f"Playwright hatasi: {clean_exception_message(e)}"

    return result


def fetch_once(url: str, user_agent=None, session=None, referer: str = ""):
    result = {
        "requested_url": url,
        "final_url": url,
        "status_code": None,
        "html": "",
        "error": "",
        "warning": "",
        "content_type": "",
        "blocked_by_filter": False,
        "blocked_target": "",
    }

    own_session = session is None
    if own_session:
        session = make_session(user_agent=user_agent)
    elif user_agent:
        session.headers.update(make_request_headers(user_agent=user_agent))

    effective_user_agent = user_agent or session.headers.get("User-Agent")

    try:
        time.sleep(random.uniform(1.0, 2.2))

        resp = session.get(
            url,
            timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
            allow_redirects=True,
            verify=True,
            stream=True,
            headers=make_request_headers(url=url, referer=referer, user_agent=effective_user_agent),
        )

        result["final_url"] = resp.url
        result["status_code"] = resp.status_code
        result["content_type"] = resp.headers.get("Content-Type", "")

        if is_block_page_url(resp.url):
            result["blocked_by_filter"] = True
            result["blocked_target"] = extract_original_target_from_block_url(resp.url)
            result["error"] = "ESB / erisim engeli sayfasina yonlendirildi"
            if result["blocked_target"]:
                result["warning"] = f"Orijinal hedef: {result['blocked_target']}"
            return result

        if resp.status_code in (403, 406, 429):
            result["error"] = f"HTTP {resp.status_code} - site istegi engelliyor olabilir"
            return result

        try:
            resp.raw.decode_content = False
            raw_bytes = resp.raw.read()
        except Exception as e:
            result["error"] = f"Icerik okunamadi: {clean_exception_message(e)}"
            return result

        content_encoding = (resp.headers.get("Content-Encoding", "") or "").lower()
        detected_encoding = resp.encoding or resp.apparent_encoding or "utf-8"

        text_data = None

        if "gzip" in content_encoding:
            try:
                text_data = gzip.decompress(raw_bytes).decode(detected_encoding, errors="replace")
            except Exception:
                try:
                    text_data = zlib.decompress(raw_bytes, 16 + zlib.MAX_WBITS).decode(
                        detected_encoding, errors="replace"
                    )
                except Exception:
                    try:
                        text_data = raw_bytes.decode(detected_encoding, errors="replace")
                        result["warning"] = "Sunucu gzip header gonderdi ama veri duz metin geldi"
                    except Exception as e:
                        result["error"] = f"Gzip icerik cozulmedi: {clean_exception_message(e)}"
                        return result

        elif "deflate" in content_encoding:
            try:
                text_data = zlib.decompress(raw_bytes).decode(detected_encoding, errors="replace")
            except Exception:
                try:
                    text_data = raw_bytes.decode(detected_encoding, errors="replace")
                    result["warning"] = "Sunucu deflate header gonderdi ama veri duz metin geldi"
                except Exception as e:
                    result["error"] = f"Deflate icerik cozulmedi: {clean_exception_message(e)}"
                    return result

        else:
            try:
                text_data = raw_bytes.decode(detected_encoding, errors="replace")
            except Exception:
                try:
                    text_data = raw_bytes.decode("utf-8", errors="replace")
                except Exception as e:
                    result["error"] = f"Icerik decode edilemedi: {clean_exception_message(e)}"
                    return result

        if not text_data:
            result["error"] = "Bos icerik dondu"
            return result

        if "text/html" in result["content_type"].lower() or "<html" in text_data.lower():
            result["html"] = text_data
        else:
            result["error"] = f"HTML olmayan icerik: {result['content_type']}"

    except requests.exceptions.SSLError as e:
        result["error"] = f"SSL hatasi: {clean_exception_message(e)}"
    except requests.exceptions.Timeout:
        result["error"] = "Zaman asimi"
    except requests.exceptions.ConnectionError as e:
        result["error"] = f"Baglanti hatasi / uzak sunucu baglantiyi kapatti: {clean_exception_message(e)}"
    except requests.exceptions.RequestException as e:
        result["error"] = f"Istek hatasi: {clean_exception_message(e)}"
    except Exception as e:
        result["error"] = f"Beklenmeyen hata: {clean_exception_message(e)}"
    finally:
        if own_session:
            session.close()

    return result


def fetch_url(url: str, session=None, referer: str = ""):
    own_session = session is None
    if own_session:
        session = make_session()

    result = fetch_once(url, session=session, referer=referer)

    try:
        if result.get("blocked_by_filter"):
            return result

        if result["html"]:
            return result

        first_error = result.get("error", "")
        first_warning = result.get("warning", "")

        if result.get("status_code") in (403, 406, 429):
            prime_session(session, url)

        time.sleep(random.uniform(1.5, 3.0))
        result2 = fetch_once(
            url,
            user_agent=random.choice(USER_AGENTS),
            session=session,
            referer=referer,
        )

        if result2.get("blocked_by_filter"):
            return result2

        if result2["html"]:
            result2["warning"] = merge_warnings(first_warning, result2.get("warning"))
            return result2

        final_result = result2
        parsed = urlparse(url)
        if parsed.scheme == "https":
            http_url = "http://" + parsed.netloc + parsed.path
            if parsed.query:
                http_url += "?" + parsed.query

            time.sleep(random.uniform(1.5, 3.0))
            result3 = fetch_once(
                http_url,
                user_agent=random.choice(USER_AGENTS),
                session=session,
                referer=referer,
            )

            if result3.get("blocked_by_filter"):
                if first_error:
                    result3["warning"] = merge_warnings(
                        result3.get("warning"),
                        f"HTTPS hatasi: {first_error}",
                    )
                return result3

            if result3["html"]:
                result3["warning"] = merge_warnings(
                    first_error,
                    first_warning,
                    "HTTPS basarisizdi, HTTP fallback basarili",
                    result3.get("warning"),
                )
                result3["error"] = ""
                return result3

            final_result = result3

        final_result["warning"] = merge_warnings(first_warning, final_result.get("warning"))

        if should_try_playwright(final_result):
            pw_result = fetch_with_playwright(url, referer=referer, user_agent=session.headers.get("User-Agent"))
            if pw_result.get("blocked_by_filter"):
                pw_result["warning"] = merge_warnings(final_result.get("warning"), pw_result.get("warning"))
                return pw_result

            if pw_result.get("html"):
                pw_result["warning"] = merge_warnings(
                    final_result.get("warning"),
                    "Requests basarisiz oldu, Playwright fallback kullanildi",
                    pw_result.get("warning"),
                )
                pw_result["error"] = ""
                return pw_result

            final_result["warning"] = merge_warnings(
                final_result.get("warning"),
                pw_result.get("warning"),
                f"Playwright fallback basarisiz: {pw_result.get('error', '')}" if pw_result.get("error") else "",
            )

        return final_result
    finally:
        if own_session:
            session.close()


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
        ])
        normalized_text = normalize_search_text(text)

        if any(k in normalized_text for k in CONTACT_KEYWORDS):
            contact_links.append(abs_url)

        if any(k in normalized_text for k in AUTH_KEYWORDS):
            auth_links.append(abs_url)

        if any(k in normalized_text for k in LANG_KEYWORDS):
            lang_links.append(abs_url)

        if re.search(r'([/?=&]|^)(lang|locale|language)=tr([&#/]|$)', abs_url.lower()):
            lang_links.append(abs_url)
        if re.search(r'/(tr|tr-tr|tr_tr)(/|$|\?)', abs_url.lower()):
            lang_links.append(abs_url)

    html_text = str(soup)
    lang_links.extend(extract_lang_candidates_from_html(base_url, html_text))

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
            txt = normalize_search_text(clean_text(tag.get_text(" ", strip=True)))
            href = normalize_search_text(tag.get("href") or "")
            combined = f"{txt} {href}"

            if "turkce" in combined or "turkish" in combined:
                signals.append("Dil secicide Turkce/Turkish bulundu")
            if re.search(r'([/?=&]|^)(lang|locale|language)=tr([&#/]|$)', combined):
                signals.append("URL parametresinde lang=tr bulundu")
            if re.search(r'/(tr|tr-tr|tr_tr)(/|$|\?)', combined):
                signals.append("TR dil yolu bulundu")

        current_url = (page.get("final_url") or "").lower()
        if re.search(r'([/?=&]|^)(lang|locale|language)=tr([&#/]|$)', current_url):
            signals.append("Sayfa URL sinde lang=tr bulundu")
        if re.search(r'/(tr|tr-tr|tr_tr)(/|$|\?)', current_url):
            signals.append("Sayfa URL sinde /tr bulundu")

        if extract_lang_candidates_from_html(current_url or page.get("requested_url") or "", html_text):
            signals.append("Ham HTML icinde TR dil yolu bulundu")

        if looks_like_turkish_text(page_text):
            signals.append("Sayfa metni Turkce gorunuyor")

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
        signals.append("Uyelik / hesap baglantilari bulundu")

    for page in pages:
        html_text = page.get("html", "")
        if not html_text:
            continue

        soup = get_soup(html_text)
        text = extract_page_text(soup).lower()

        if soup.find("input", attrs={"type": re.compile(r"password", re.I)}):
            signals.append("Sifre alani bulundu")

        for form in soup.find_all("form"):
            form_html = str(form).lower()
            has_password = 'type="password"' in form_html or "password" in form_html
            has_email = ('type="email"' in form_html) or ('name="email"' in form_html) or ("email" in form_html)
            action = (form.get("action") or "").lower()

            if has_password and has_email:
                signals.append("Email + sifre formu bulundu")
            elif has_password and any(
                k in action for k in [
                    "login", "signin", "account", "register",
                    "signup", "uye", "kayit"
                ]
            ):
                signals.append("Giris / hesap formu bulundu")

        phrases = [
            "sign up", "signup", "register", "create account", "my account", "customer login",
            "member", "membership", "portal", "online account",
            "uye ol", "uyelik", "kayit ol", "hesap olustur", "giris yap",
            "musteri girisi", "bayi girisi", "oturum ac", "hesabim"
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
        "site_status": "Bilinmiyor",
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
        "warning": "",
        "blocked_by_filter": False,
        "blocked_target": "",
    }

    base = normalize_url(url)
    result["site"] = base

    session = make_session()
    try:
        main = fetch_url(base, session=session)
        result["final_url"] = main.get("final_url") or base
        result["status_code"] = main.get("status_code") or ""
        result["error"] = main.get("error", "")
        result["warning"] = main.get("warning", "")
        result["blocked_by_filter"] = main.get("blocked_by_filter", False)
        result["blocked_target"] = main.get("blocked_target", "")
        result["site_status"] = classify_site_status(main)

        if result["blocked_by_filter"]:
            return result

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
            fetched = fetch_url(link, session=session, referer=result["final_url"])
            pages.append(fetched)
            result["scanned_pages"].append(fetched.get("final_url") or link)
            time.sleep(random.uniform(1.0, 2.0))

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
        result["site_status"] = classify_site_status(result)
    finally:
        session.close()

    return result


def make_error_result(url: str, error_message: str):
    return {
        "site": url,
        "final_url": url,
        "status_code": "",
        "site_status": "Hata",
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
        "error": error_message,
        "warning": "",
        "blocked_by_filter": False,
        "blocked_target": "",
    }


def compact_list_html(items, limit=8):
    if not items:
        return "-"
    items = dedupe_keep_order(items)
    if len(items) > limit:
        shown = items[:limit]
        extra = len(items) - limit
        return "<br>".join(html.escape(x) for x in shown) + f"<br><em>... +{extra} adet daha</em>"
    return "<br>".join(html.escape(x) for x in items)


def badge_html(value: bool, yes_text="Evet", no_text="Hayir"):
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
        footnotes = []

        if r.get("warning"):
            footnotes.append(f"<strong>Uyari:</strong> {html.escape(r['warning'])}")
        if r.get("error"):
            footnotes.append(f"<strong>Hata:</strong> {html.escape(r['error'])}")

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
            <td>{compact_list_html(r["lang_links"], 4)}</td>
            <td>{badge_html(r["turkey_phone"])}</td>
            <td>{compact_list_html(r["turkey_phone_numbers"], 6)}</td>
            <td>{badge_html(r["membership"])}</td>
            <td>{compact_list_html(r["membership_evidence"], 6)}</td>
            <td>{compact_list_html(r["contact_links"], 5)}</td>
            <td>{compact_list_html(r["auth_links"], 5)}</td>
            <td>{badge_html(r.get("blocked_by_filter", False), "Evet", "Hayir")}</td>
        </tr>
        """)

        if footnotes:
            rows.append(f"""
        <tr class="footnote-row">
            <td></td>
            <td colspan="12"><div class="footnote">{'<br>'.join(footnotes)}</div></td>
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
    .footnote-row td {{
        background: #fffdf5;
        border-top: none;
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
    .footnote {{
        font-size: 12px;
        color: #5b4b00;
        line-height: 1.5;
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
        Olusturulma zamani: <strong>{created_at}</strong><br>
        Toplam site sayisi: <strong>{len(results)}</strong>
    </div>

    <table>
        <thead>
            <tr>
                <th>#</th>
                <th>Site</th>
                <th>HTTP</th>
                <th>Turkce Destegi</th>
                <th>Turkce Bulgulari</th>
                <th>Turkce Linkleri</th>
                <th>Turkiye Telefonu</th>
                <th>Bulunan Telefonlar</th>
                <th>Uyelik / Online Hesap</th>
                <th>Uyelik Bulgulari</th>
                <th>Iletisim Sayfalari</th>
                <th>Uyelik Sayfalari</th>
                <th>Engel Sayfasi</th>
            </tr>
        </thead>
        <tbody>
            {''.join(rows)}
        </tbody>
    </table>

    <div class="note">
        <strong>Not:</strong><br>
        - Analiz HTML ve baglanti sinyallerine gore yapilir.<br>
        - Bazi siteler bot korumasi, WAF veya Cloudflare nedeniyle baglantiyi kapatabilir.<br>
        - Bu surum tekrar deneme, gecikme ve farkli User-Agent ile ikinci deneme kullanir.<br>
        - HTTPS olmazsa HTTP fallback denenir.<br>
        - ESB engel sayfasina yonlenirse bu ayri bir durum olarak raporlanir.<br>
        - Tam korumali sitelerde requests yetersiz kalabilir; o durumda Playwright gerekir.
    </div>
</body>
</html>
"""


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Site Analiz Araci")
        self.root.geometry("1280x800")

        default_output = str(Path.cwd() / "site_analiz_raporu.html")
        self.output_path_var = tk.StringVar(value=default_output)
        self.open_after_var = tk.BooleanVar(value=True)
        self.progress_text_var = tk.StringVar(value="Hazir")
        self.is_running = False

        self.build_ui()

    def build_ui(self):
        top_frame = ttk.Frame(self.root, padding=10)
        top_frame.pack(fill="x")

        title = ttk.Label(
            top_frame,
            text="Site Analiz Araci",
            font=("Segoe UI", 16, "bold")
        )
        title.pack(anchor="w")

        desc = ttk.Label(
            top_frame,
            text="URL leri alt alta gir. Program Turkce destegi, Turkiye telefon hatti ve uyelik sistemi olup olmadigini analiz eder.",
            wraplength=1180
        )
        desc.pack(anchor="w", pady=(4, 10))

        input_frame = ttk.LabelFrame(self.root, text="Site URL Listesi", padding=10)
        input_frame.pack(fill="both", expand=False, padx=10, pady=(0, 10))

        self.urls_text = ScrolledText(input_frame, height=12, font=("Consolas", 10))
        self.urls_text.pack(fill="both", expand=True)
        self.urls_text.insert("1.0", "https://example.com\nhttps://example.org\n")

        output_frame = ttk.LabelFrame(self.root, text="Cikti Ayarlari", padding=10)
        output_frame.pack(fill="x", padx=10, pady=(0, 10))

        ttk.Label(output_frame, text="HTML cikti dosyasi:").grid(row=0, column=0, sticky="w")
        self.output_entry = ttk.Entry(output_frame, textvariable=self.output_path_var, width=90)
        self.output_entry.grid(row=0, column=1, padx=8, pady=5, sticky="we")

        browse_btn = ttk.Button(output_frame, text="Kaydet Yeri Sec", command=self.choose_output_file)
        browse_btn.grid(row=0, column=2, padx=5, pady=5)

        open_check = ttk.Checkbutton(
            output_frame,
            text="Islem bitince HTML raporu ac",
            variable=self.open_after_var
        )
        open_check.grid(row=1, column=1, sticky="w", pady=4)

        output_frame.columnconfigure(1, weight=1)

        button_frame = ttk.Frame(self.root, padding=(10, 0))
        button_frame.pack(fill="x")

        self.start_btn = ttk.Button(button_frame, text="Analizi Baslat", command=self.start_analysis)
        self.start_btn.pack(side="left")

        self.clear_btn = ttk.Button(button_frame, text="URL Alanini Temizle", command=self.clear_urls)
        self.clear_btn.pack(side="left", padx=8)

        self.sample_btn = ttk.Button(button_frame, text="Ornek URL Ekle", command=self.insert_sample_urls)
        self.sample_btn.pack(side="left")

        self.progress_label = ttk.Label(button_frame, textvariable=self.progress_text_var)
        self.progress_label.pack(side="right", padx=(10, 0))

        self.progress = ttk.Progressbar(button_frame, mode="determinate", length=220, maximum=100)
        self.progress.pack(side="right")

        log_frame = ttk.LabelFrame(self.root, text="Islem Gunlugu", padding=10)
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
            title="HTML cikti dosyasini sec",
            defaultextension=".html",
            filetypes=[("HTML Dosyasi", "*.html"), ("Tum Dosyalar", "*.*")]
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
        lines = [x for x in lines if x and not x.startswith("#")]
        urls = [normalize_url(x) for x in lines if normalize_url(x)]
        return dedupe_keep_order(urls)

    def set_progress(self, current, total):
        total = max(total, 1)
        percent = int((current / total) * 100)
        self.progress.configure(value=percent)
        self.progress_text_var.set(f"Ilerleme: {current}/{total} (%{percent})")

    def start_analysis(self):
        if self.is_running:
            return

        urls = self.parse_urls()
        if not urls:
            messagebox.showwarning("Uyari", "Lutfen en az bir site adresi gir.")
            return

        output_path = self.output_path_var.get().strip()
        if not output_path:
            messagebox.showwarning("Uyari", "Lutfen cikti dosya adini belirt.")
            return

        self.is_running = True
        self.start_btn.configure(state="disabled")
        self.progress.configure(value=0)
        self.progress_text_var.set(f"Ilerleme: 0/{len(urls)} (%0)")
        self.log("Analiz basladi.")
        self.log(f"Toplam site: {len(urls)}")

        open_after = bool(self.open_after_var.get())
        thread = threading.Thread(
            target=self.run_analysis,
            args=(urls, output_path, open_after),
            daemon=True,
        )
        thread.start()

    def finish_analysis(self):
        self.is_running = False
        self.start_btn.configure(state="normal")
        self.progress.configure(value=0)
        self.progress_text_var.set("Hazir")

    def run_analysis(self, urls, output_path, open_after):
        try:
            results = []
            total = len(urls)

            for idx, url in enumerate(urls, start=1):
                self.root.after(0, self.log, f"[{idx}/{total}] Analiz ediliyor: {url}")
                try:
                    res = analyze_site(url)
                    results.append(res)

                    summary = []
                    summary.append(f"Durum: {res.get('site_status', 'Bilinmiyor')}")
                    summary.append("TR dil: Evet" if res["turkish_support"] else "TR dil: Hayir")
                    summary.append("TR tel: Evet" if res["turkey_phone"] else "TR tel: Hayir")
                    summary.append("Uyelik: Evet" if res["membership"] else "Uyelik: Hayir")

                    if res.get("blocked_by_filter"):
                        summary.append("Engel sayfasina yonlendirildi")
                    if res.get("blocked_target"):
                        summary.append(f"Hedef: {res['blocked_target']}")
                    if res.get("warning"):
                        summary.append(f"Uyari: {res['warning']}")
                    if res["error"]:
                        summary.append(f"Hata: {res['error']}")

                    self.root.after(0, self.log, " | ".join(summary))
                except Exception as e:
                    error_message = clean_exception_message(e)
                    self.root.after(0, self.log, f"Hata: {url} -> {error_message}")
                    results.append(make_error_result(url, error_message))

                self.root.after(0, self.set_progress, idx, total)

                time.sleep(random.uniform(1.5, 3.0))

            report_html = build_html_report(results)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(report_html)

            self.root.after(0, self.log, f"HTML rapor olusturuldu: {output_path}")

            if open_after:
                try:
                    abs_path = Path(output_path).resolve()
                    if sys.platform.startswith("win"):
                        os.startfile(str(abs_path))
                    else:
                        webbrowser.open(abs_path.as_uri())
                    self.root.after(0, self.log, f"HTML rapor acildi: {abs_path}")
                except Exception as e:
                    self.root.after(0, self.log, f"Rapor acilamadi: {clean_exception_message(e)}")

            self.root.after(
                0,
                lambda: messagebox.showinfo("Tamam", f"Analiz tamamlandi.\n\nCikti:\n{output_path}")
            )
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Hata", clean_exception_message(e)))
            self.root.after(0, self.log, f"Genel hata: {clean_exception_message(e)}")
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
