"""
scraper.py - بيسكان مواقع الشغل العربية ويجيب الشغلانات المناسبة
"""
import hashlib
import time
import random
import re
import urllib.parse
import logging
import requests
from xml.etree import ElementTree as ET
from bs4 import BeautifulSoup
from src.config import SEARCH_KEYWORDS, ARAB_COUNTRIES

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def safe_request(url: str, retries: int = 3, timeout: int = 15) -> requests.Response | None:
    """بيعمل HTTP request مع retry تلقائي في حالة الفشل"""
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=timeout)
            if resp.status_code == 200:
                return resp
            elif resp.status_code == 429:
                wait = (attempt + 1) * 15
                log.warning(f"⏳ Rate limited، هستنى {wait}s ثم أحاول تاني...")
                time.sleep(wait)
            elif resp.status_code in (403, 401):
                log.warning(f"🚫 ممنوع الوصول ({resp.status_code}): {url[:60]}")
                return None
            else:
                log.warning(f"HTTP {resp.status_code}: {url[:60]}")
                return None
        except requests.exceptions.Timeout:
            log.warning(f"⌛ Timeout (محاولة {attempt + 1}/3): {url[:60]}")
        except Exception as e:
            log.warning(f"❌ Request error (محاولة {attempt + 1}/3): {e}")

        if attempt < retries - 1:
            time.sleep(random.uniform(2, 5))

    return None


def make_job_id(title: str, company: str, url: str) -> str:
    """بيعمل ID فريد لكل شغلانة"""
    raw = f"{title.lower().strip()}|{company.lower().strip()}|{url.strip()}"
    return hashlib.md5(raw.encode()).hexdigest()


def is_relevant(title: str, description: str = "") -> bool:
    """بيتحقق إن الشغلانة دي متعلقة بالقبة الفلكية"""
    text = f"{title} {description}".lower()
    keywords_lower = [k.lower() for k in SEARCH_KEYWORDS]
    return any(kw in text for kw in keywords_lower)


def is_arab_location(location: str) -> bool:
    """بيتحقق إن الشغلانة في دولة عربية"""
    loc = location.lower()
    for country in ARAB_COUNTRIES:
        if country.lower() in loc:
            return True
    return False  # FIXED: كانت return True بالغلط — كانت بتعدّي كل شغلانة حتى لو مش عربية


# ─────────────────────────────────────────────
# 1. INDEED RSS (الأكثر ثبات — بيشتغل بدون JS)
# ─────────────────────────────────────────────
def scrape_indeed_rss() -> list:
    """بيسكان Indeed عبر RSS Feed — أثبت بكتير من HTML scraping ومش محتاج JavaScript"""
    jobs = []
    log.info("🔍 بيسكان Indeed RSS...")

    indeed_domains = [
        ("https://sa.indeed.com", "Saudi Arabia"),
        ("https://ae.indeed.com", "UAE"),
        ("https://eg.indeed.com", "Egypt"),
        ("https://kw.indeed.com", "Kuwait"),
        ("https://qa.indeed.com", "Qatar"),
    ]
    keywords = ["planetarium", "dome operator", "قبة فلكية", "fulldome"]

    for domain, country in indeed_domains:
        for keyword in keywords:
            try:
                encoded = urllib.parse.quote(keyword)
                url = f"{domain}/rss?q={encoded}&sort=date"
                resp = safe_request(url, timeout=20)
                if not resp:
                    continue

                # حاول parse الـ XML
                try:
                    root = ET.fromstring(resp.content)
                    channel = root.find("channel")
                    items = channel.findall("item") if channel else []
                except ET.ParseError:
                    # Fallback: BeautifulSoup لـ XML التالف
                    soup = BeautifulSoup(resp.text, "xml")
                    items_bs = soup.find_all("item")
                    for item in items_bs:
                        try:
                            title = item.find("title").get_text(strip=True) if item.find("title") else ""
                            link  = item.find("link").get_text(strip=True)  if item.find("link")  else ""
                            desc  = item.find("description").get_text(strip=True) if item.find("description") else ""
                            if not is_relevant(title, desc):
                                continue
                            jobs.append({
                                "id":       make_job_id(title, "", link),
                                "title":    title,
                                "company":  "",
                                "location": country,
                                "url":      link,
                                "source":   f"Indeed RSS ({country})",
                            })
                            log.info(f"  ✅ {title} - {country}")
                        except Exception:
                            continue
                    time.sleep(random.uniform(1, 3))
                    continue

                for item in items:
                    try:
                        title   = (item.findtext("title")       or "").strip()
                        link    = (item.findtext("link")        or "").strip()
                        desc    = (item.findtext("description") or "").strip()
                        company = ""

                        # Indeed بيحط اسم الشركة جوه description بـ <b>
                        company_match = re.search(r"<b>([^<]+)</b>", desc)
                        if company_match:
                            company = company_match.group(1).strip()

                        if not is_relevant(title, desc):
                            continue

                        jobs.append({
                            "id":       make_job_id(title, company, link),
                            "title":    title,
                            "company":  company,
                            "location": country,
                            "url":      link,
                            "source":   f"Indeed RSS ({country})",
                        })
                        log.info(f"  ✅ {title} @ {company} - {country}")
                    except Exception:
                        continue

                time.sleep(random.uniform(1, 3))

            except Exception as e:
                log.warning(f"Indeed RSS error '{keyword}' in {country}: {e}")

    return jobs


# ─────────────────────────────────────────────
# 2. BAYT.COM
# ─────────────────────────────────────────────
def scrape_bayt() -> list:
    jobs = []
    log.info("🔍 بيسكان Bayt.com...")

    search_terms = ["planetarium", "dome operator", "قبة فلكية"]
    for term in search_terms:
        try:
            encoded = urllib.parse.quote(term)
            url = f"https://www.bayt.com/en/international/jobs/{encoded}-jobs/"
            resp = safe_request(url)
            if not resp:
                continue
            soup = BeautifulSoup(resp.text, "html.parser")

            listings = soup.find_all("li", {"data-js-job": True})
            for item in listings:
                try:
                    title_el   = item.find("h2", class_="m0 t-regular")
                    company_el = item.find("b",    {"data-automation": "jobCompany"})
                    loc_el     = item.find("span", {"data-automation": "jobCity"})
                    link_el    = item.find("a", href=True)

                    title    = title_el.get_text(strip=True)   if title_el   else ""
                    company  = company_el.get_text(strip=True) if company_el else ""
                    location = loc_el.get_text(strip=True)     if loc_el     else ""
                    link     = f"https://www.bayt.com{link_el['href']}" if link_el else url

                    if not is_relevant(title):
                        continue
                    if not is_arab_location(location):
                        continue

                    jobs.append({
                        "id":       make_job_id(title, company, link),
                        "title":    title,
                        "company":  company,
                        "location": location,
                        "url":      link,
                        "source":   "Bayt.com",
                    })
                    log.info(f"  ✅ {title} @ {company} - {location}")
                except Exception:
                    continue

            time.sleep(random.uniform(1, 3))
        except Exception as e:
            log.warning(f"Bayt error for '{term}': {e}")

    return jobs


# ─────────────────────────────────────────────
# 3. WUZZUF.NET (مصري)
# ─────────────────────────────────────────────
def scrape_wuzzuf() -> list:
    jobs = []
    log.info("🔍 بيسكان Wuzzuf.net...")

    search_terms = ["planetarium", "dome", "قبة فلكية", "فلكي"]
    for term in search_terms:
        try:
            encoded = urllib.parse.quote(term)
            url = f"https://wuzzuf.net/search/jobs/?q={encoded}"
            resp = safe_request(url)
            if not resp:
                continue
            soup = BeautifulSoup(resp.text, "html.parser")

            # Fallback selectors — Wuzzuf بتغير CSS classes باستمرار
            cards = (
                soup.find_all("div", class_="css-1gatmva")
                or soup.find_all("article", attrs={"data-wuzzuf-job": True})
                or soup.find_all("div", class_=lambda c: c and "JobCard" in (c or ""))
                or soup.find_all("div", attrs={"data-id": True})
            )

            for card in cards:
                try:
                    title_el = (
                        card.find("h2", class_="css-m604qf")
                        or card.find("h2", class_=lambda c: "title" in (c or "").lower())
                        or card.find("h2")
                    )
                    company_el = (
                        card.find("a", class_="css-17s97q8")
                        or card.find("a", class_=lambda c: "company" in (c or "").lower())
                        or card.find("span", class_=lambda c: "company" in (c or "").lower())
                    )
                    loc_el = (
                        card.find("span", class_="css-5wys0k")
                        or card.find("span", class_=lambda c: "location" in (c or "").lower())
                    )
                    link_el = title_el.find("a", href=True) if title_el else None

                    title    = title_el.get_text(strip=True)   if title_el   else ""
                    company  = company_el.get_text(strip=True) if company_el else ""
                    location = loc_el.get_text(strip=True)     if loc_el     else "Egypt"
                    link     = f"https://wuzzuf.net{link_el['href']}" if link_el else url

                    if not title or not is_relevant(title):
                        continue

                    jobs.append({
                        "id":       make_job_id(title, company, link),
                        "title":    title,
                        "company":  company,
                        "location": location,
                        "url":      link,
                        "source":   "Wuzzuf.net",
                    })
                    log.info(f"  ✅ {title} @ {company} - {location}")
                except Exception:
                    continue

            time.sleep(random.uniform(1, 3))
        except Exception as e:
            log.warning(f"Wuzzuf error for '{term}': {e}")

    return jobs


# ─────────────────────────────────────────────
# 4. GULFJOBS.COM
# ─────────────────────────────────────────────
def scrape_gulfjobs() -> list:
    jobs = []
    log.info("🔍 بيسكان GulfJobs.com...")

    try:
        url = "https://www.gulfjobs.com/search-jobs/results/?keywords=planetarium&location=0"
        resp = safe_request(url)
        if not resp:
            return jobs
        soup = BeautifulSoup(resp.text, "html.parser")

        cards = soup.find_all("div", class_="job-listing")
        for card in cards:
            try:
                title_el   = card.find("h3")
                company_el = card.find("span", class_="company-name")
                loc_el     = card.find("span", class_="location")
                link_el    = card.find("a", href=True)

                title    = title_el.get_text(strip=True)   if title_el   else ""
                company  = company_el.get_text(strip=True) if company_el else ""
                location = loc_el.get_text(strip=True)     if loc_el     else ""
                link     = link_el["href"]                 if link_el    else url

                if not is_relevant(title):
                    continue

                jobs.append({
                    "id":       make_job_id(title, company, link),
                    "title":    title,
                    "company":  company,
                    "location": location,
                    "url":      link,
                    "source":   "GulfJobs.com",
                })
                log.info(f"  ✅ {title} @ {company} - {location}")
            except Exception:
                continue

        time.sleep(random.uniform(1, 3))
    except Exception as e:
        log.warning(f"GulfJobs error: {e}")

    return jobs


# ─────────────────────────────────────────────
# 5. LINKEDIN — مع fallback selectors + 7 أيام
# ─────────────────────────────────────────────
def scrape_linkedin() -> list:
    jobs = []
    log.info("🔍 بيسكان LinkedIn...")

    keywords = ["planetarium operator", "dome operator", "قبة فلكية"]
    geo_ids = {
        "SA": "101452733",
        "AE": "101282714",
        "EG": "106556571",
        "KW": "100635387",
        "QA": "97785592",
    }

    for keyword in keywords:
        for country, geo_id in geo_ids.items():
            try:
                encoded = urllib.parse.quote(keyword)
                url = (
                    f"https://www.linkedin.com/jobs/search/?keywords={encoded}"
                    f"&geoId={geo_id}&f_TPR=r604800"  # آخر 7 أيام (كان 24 ساعة — أشمل)
                )
                resp = safe_request(url)
                if not resp:
                    time.sleep(random.uniform(3, 6))
                    continue
                soup = BeautifulSoup(resp.text, "html.parser")

                # Fallback selectors
                cards = (
                    soup.find_all("div", class_="base-card")
                    or soup.find_all("div", class_=lambda c: c and "job-search-card" in (c or ""))
                    or soup.find_all("li", class_=lambda c: c and "result" in (c or "").lower())
                )

                for card in cards:
                    try:
                        title_el = (
                            card.find("h3", class_="base-search-card__title")
                            or card.find("h3", class_=lambda c: "title" in (c or "").lower())
                            or card.find("h3")
                        )
                        company_el = (
                            card.find("h4", class_="base-search-card__subtitle")
                            or card.find("h4", class_=lambda c: "subtitle" in (c or "").lower())
                        )
                        loc_el = (
                            card.find("span", class_="job-search-card__location")
                            or card.find("span", class_=lambda c: "location" in (c or "").lower())
                        )
                        link_el = (
                            card.find("a", class_="base-card__full-link")
                            or card.find("a", href=True)
                        )

                        title    = title_el.get_text(strip=True)   if title_el   else ""
                        company  = company_el.get_text(strip=True) if company_el else ""
                        location = loc_el.get_text(strip=True)     if loc_el     else ""
                        link     = link_el["href"]                 if link_el    else url

                        if not title or not is_relevant(title):
                            continue

                        jobs.append({
                            "id":       make_job_id(title, company, link),
                            "title":    title,
                            "company":  company,
                            "location": location,
                            "url":      link,
                            "source":   "LinkedIn",
                        })
                        log.info(f"  ✅ {title} @ {company} - {location}")
                    except Exception:
                        continue

                time.sleep(random.uniform(3, 6))  # LinkedIn حساس جداً للسرعة
            except Exception as e:
                log.warning(f"LinkedIn error for '{keyword}' in {country}: {e}")

    return jobs


# ─────────────────────────────────────────────
# 6. INDEED HTML (fallback إضافي للـ RSS)
# ─────────────────────────────────────────────
def scrape_indeed_html() -> list:
    jobs = []
    log.info("🔍 بيسكان Indeed (HTML fallback)...")

    indeed_domains = [
        ("https://sa.indeed.com", "Saudi Arabia"),
        ("https://ae.indeed.com", "UAE"),
        ("https://eg.indeed.com", "Egypt"),
    ]

    for domain, country in indeed_domains:
        for term in ["planetarium", "dome operator"]:
            try:
                encoded = urllib.parse.quote(term)
                url = f"{domain}/jobs?q={encoded}&sort=date"
                resp = safe_request(url)
                if not resp:
                    continue
                soup = BeautifulSoup(resp.text, "html.parser")

                cards = (
                    soup.find_all("div", class_="job_seen_beacon")
                    or soup.find_all("div", attrs={"data-testid": "slider_item"})
                    or soup.find_all("li", class_=lambda c: c and "result" in (c or "").lower())
                )

                for card in cards:
                    try:
                        title_el = card.find("h2", class_="jobTitle") or card.find("h2")
                        company_el = (
                            card.find("span", class_="companyName")
                            or card.find("span", attrs={"data-testid": "company-name"})
                        )
                        loc_el = (
                            card.find("div", class_="companyLocation")
                            or card.find("div", attrs={"data-testid": "text-location"})
                        )
                        link_el = title_el.find("a", href=True) if title_el else None

                        title    = title_el.get_text(strip=True)   if title_el   else ""
                        company  = company_el.get_text(strip=True) if company_el else ""
                        location = loc_el.get_text(strip=True)     if loc_el     else country
                        link     = f"{domain}{link_el['href']}"    if link_el    else url

                        if not title or not is_relevant(title):
                            continue

                        jobs.append({
                            "id":       make_job_id(title, company, link),
                            "title":    title,
                            "company":  company,
                            "location": location,
                            "url":      link,
                            "source":   f"Indeed ({country})",
                        })
                        log.info(f"  ✅ {title} @ {company} - {location}")
                    except Exception:
                        continue

                time.sleep(random.uniform(2, 4))
            except Exception as e:
                log.warning(f"Indeed HTML error for '{term}' in {country}: {e}")

    return jobs


# ─────────────────────────────────────────────
# الدالة الرئيسية — بتجمع من كل المواقع
# ─────────────────────────────────────────────
def get_all_jobs() -> list:
    """بيجيب كل الشغلانات من كل المواقع"""
    all_jobs = []

    scrapers = [
        scrape_indeed_rss,    # الأكثر ثبات — RSS مباشر
        scrape_bayt,
        scrape_wuzzuf,
        scrape_gulfjobs,
        scrape_linkedin,
        scrape_indeed_html,   # HTML fallback
    ]

    for scraper in scrapers:
        try:
            found = scraper()
            all_jobs.extend(found)
            log.info(f"  📦 {scraper.__name__}: وجدنا {len(found)} شغلانة")
        except Exception as e:
            log.error(f"خطأ في {scraper.__name__}: {e}")

    # إزالة التكرار بالـ ID
    seen_ids    = set()
    unique_jobs = []
    for job in all_jobs:
        if job["id"] not in seen_ids:
            seen_ids.add(job["id"])
            unique_jobs.append(job)

    log.info(f"\n📊 المجموع: {len(unique_jobs)} شغلانة فريدة من {len(all_jobs)} نتيجة")
    return unique_jobs
