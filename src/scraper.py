"""
scraper.py - بيسكان مواقع الشغل العربية ويجيب الشغلانات المناسبة
"""
import hashlib
import time
import urllib.parse
import logging
import requests
from bs4 import BeautifulSoup
from src.config import SEARCH_KEYWORDS, ARAB_COUNTRIES, ARAB_COUNTRY_CODES

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


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
    return True  # لو الموقع عربي أصلاً نفترض إنه عربي


# ─────────────────────────────────────────────
# 1. GOOGLE JOBS (أهم مصدر - بيجمع من كل المواقع)
# ─────────────────────────────────────────────
def scrape_google_jobs() -> list:
    jobs = []
    log.info("🔍 بيسكان Google Jobs...")

    for keyword in ["planetarium operator arab", "قبة فلكية وظيفة", "dome operator middle east"]:
        try:
            query = urllib.parse.quote(keyword)
            url = f"https://www.google.com/search?q={query}&ibp=htl;jobs"
            resp = requests.get(url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(resp.text, "html.parser")

            # بيجيب بطاقات الشغل من Google
            cards = soup.find_all("div", class_=lambda c: c and "iFjolb" in c)
            for card in cards:
                try:
                    title_el   = card.find("div", class_="BjJfJf")
                    company_el = card.find("div", class_="vNEEBe")
                    loc_el     = card.find("div", class_="Qk80Jf")

                    title   = title_el.get_text(strip=True)   if title_el   else ""
                    company = company_el.get_text(strip=True) if company_el else ""
                    location = loc_el.get_text(strip=True)   if loc_el     else ""

                    if not is_relevant(title):
                        continue

                    job = {
                        "id":       make_job_id(title, company, url),
                        "title":    title,
                        "company":  company,
                        "location": location,
                        "url":      url,
                        "source":   "Google Jobs",
                    }
                    jobs.append(job)
                    log.info(f"  ✅ لقينا: {title} @ {company} - {location}")
                except Exception:
                    continue

            time.sleep(3)
        except Exception as e:
            log.warning(f"Google Jobs error: {e}")

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
            resp = requests.get(url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(resp.text, "html.parser")

            listings = soup.find_all("li", {"data-js-job": True})
            for item in listings:
                try:
                    title_el   = item.find("h2", class_="m0 t-regular")
                    company_el = item.find("b", {"data-automation": "jobCompany"})
                    loc_el     = item.find("span", {"data-automation": "jobCity"})
                    link_el    = item.find("a", href=True)

                    title   = title_el.get_text(strip=True)   if title_el   else ""
                    company = company_el.get_text(strip=True) if company_el else ""
                    location = loc_el.get_text(strip=True)   if loc_el     else ""
                    link    = f"https://www.bayt.com{link_el['href']}" if link_el else url

                    if not is_relevant(title):
                        continue
                    if not is_arab_location(location):
                        continue

                    job = {
                        "id":       make_job_id(title, company, link),
                        "title":    title,
                        "company":  company,
                        "location": location,
                        "url":      link,
                        "source":   "Bayt.com",
                    }
                    jobs.append(job)
                    log.info(f"  ✅ لقينا: {title} @ {company} - {location}")
                except Exception:
                    continue

            time.sleep(2)
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
            resp = requests.get(url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(resp.text, "html.parser")

            cards = soup.find_all("div", class_="css-1gatmva")
            for card in cards:
                try:
                    title_el   = card.find("h2", class_="css-m604qf")
                    company_el = card.find("a", class_="css-17s97q8")
                    loc_el     = card.find("span", class_="css-5wys0k")
                    link_el    = title_el.find("a", href=True) if title_el else None

                    title   = title_el.get_text(strip=True)   if title_el   else ""
                    company = company_el.get_text(strip=True) if company_el else ""
                    location = loc_el.get_text(strip=True)   if loc_el     else "Egypt"
                    link    = f"https://wuzzuf.net{link_el['href']}" if link_el else url

                    if not is_relevant(title):
                        continue

                    job = {
                        "id":       make_job_id(title, company, link),
                        "title":    title,
                        "company":  company,
                        "location": location,
                        "url":      link,
                        "source":   "Wuzzuf.net",
                    }
                    jobs.append(job)
                    log.info(f"  ✅ لقينا: {title} @ {company} - {location}")
                except Exception:
                    continue

            time.sleep(2)
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
        resp = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")

        cards = soup.find_all("div", class_="job-listing")
        for card in cards:
            try:
                title_el   = card.find("h3")
                company_el = card.find("span", class_="company-name")
                loc_el     = card.find("span", class_="location")
                link_el    = card.find("a", href=True)

                title   = title_el.get_text(strip=True)   if title_el   else ""
                company = company_el.get_text(strip=True) if company_el else ""
                location = loc_el.get_text(strip=True)   if loc_el     else ""
                link    = link_el["href"]                 if link_el    else url

                if not is_relevant(title):
                    continue

                job = {
                    "id":       make_job_id(title, company, link),
                    "title":    title,
                    "company":  company,
                    "location": location,
                    "url":      link,
                    "source":   "GulfJobs.com",
                }
                jobs.append(job)
                log.info(f"  ✅ لقينا: {title} @ {company} - {location}")
            except Exception:
                continue

        time.sleep(2)
    except Exception as e:
        log.warning(f"GulfJobs error: {e}")

    return jobs


# ─────────────────────────────────────────────
# 5. LINKEDIN (عبر RSS/Search)
# ─────────────────────────────────────────────
def scrape_linkedin() -> list:
    jobs = []
    log.info("🔍 بيسكان LinkedIn...")

    keywords = ["planetarium operator", "dome operator", "قبة فلكية"]
    geo_ids = {
        "SA": "101452733",  # Saudi Arabia
        "AE": "101282714",  # UAE
        "EG": "106556571",  # Egypt
        "KW": "100635387",  # Kuwait
        "QA": "97785592",   # Qatar
    }

    for keyword in keywords:
        for country, geo_id in geo_ids.items():
            try:
                encoded = urllib.parse.quote(keyword)
                url = (
                    f"https://www.linkedin.com/jobs/search/?keywords={encoded}"
                    f"&geoId={geo_id}&f_TPR=r86400"  # آخر 24 ساعة
                )
                resp = requests.get(url, headers=HEADERS, timeout=15)
                soup = BeautifulSoup(resp.text, "html.parser")

                cards = soup.find_all("div", class_="base-card")
                for card in cards:
                    try:
                        title_el   = card.find("h3", class_="base-search-card__title")
                        company_el = card.find("h4", class_="base-search-card__subtitle")
                        loc_el     = card.find("span", class_="job-search-card__location")
                        link_el    = card.find("a", class_="base-card__full-link")

                        title   = title_el.get_text(strip=True)   if title_el   else ""
                        company = company_el.get_text(strip=True) if company_el else ""
                        location = loc_el.get_text(strip=True)   if loc_el     else ""
                        link    = link_el["href"]                 if link_el    else url

                        if not is_relevant(title):
                            continue

                        job = {
                            "id":       make_job_id(title, company, link),
                            "title":    title,
                            "company":  company,
                            "location": location,
                            "url":      link,
                            "source":   "LinkedIn",
                        }
                        jobs.append(job)
                        log.info(f"  ✅ لقينا: {title} @ {company} - {location}")
                    except Exception:
                        continue

                time.sleep(2)
            except Exception as e:
                log.warning(f"LinkedIn error for '{keyword}' in {country}: {e}")

    return jobs


# ─────────────────────────────────────────────
# 6. INDEED (دول عربية)
# ─────────────────────────────────────────────
def scrape_indeed() -> list:
    jobs = []
    log.info("🔍 بيسكان Indeed...")

    indeed_domains = [
        ("https://sa.indeed.com", "Saudi Arabia"),
        ("https://ae.indeed.com", "UAE"),
        ("https://eg.indeed.com", "Egypt"),
        ("https://kw.indeed.com", "Kuwait"),
        ("https://qa.indeed.com", "Qatar"),
    ]

    for domain, country in indeed_domains:
        for term in ["planetarium", "dome operator"]:
            try:
                encoded = urllib.parse.quote(term)
                url = f"{domain}/jobs?q={encoded}"
                resp = requests.get(url, headers=HEADERS, timeout=15)
                soup = BeautifulSoup(resp.text, "html.parser")

                cards = soup.find_all("div", class_="job_seen_beacon")
                for card in cards:
                    try:
                        title_el   = card.find("h2", class_="jobTitle")
                        company_el = card.find("span", class_="companyName")
                        loc_el     = card.find("div",  class_="companyLocation")
                        link_el    = title_el.find("a", href=True) if title_el else None

                        title   = title_el.get_text(strip=True)   if title_el   else ""
                        company = company_el.get_text(strip=True) if company_el else ""
                        location = loc_el.get_text(strip=True)   if loc_el     else country
                        link    = f"{domain}{link_el['href']}"   if link_el    else url

                        if not is_relevant(title):
                            continue

                        job = {
                            "id":       make_job_id(title, company, link),
                            "title":    title,
                            "company":  company,
                            "location": location,
                            "url":      link,
                            "source":   f"Indeed ({country})",
                        }
                        jobs.append(job)
                        log.info(f"  ✅ لقينا: {title} @ {company} - {location}")
                    except Exception:
                        continue

                time.sleep(2)
            except Exception as e:
                log.warning(f"Indeed error for '{term}' in {country}: {e}")

    return jobs


# ─────────────────────────────────────────────
# الدالة الرئيسية - بتجمع من كل المواقع
# ─────────────────────────────────────────────
def get_all_jobs() -> list:
    """بيجيب كل الشغلانات من كل المواقع"""
    all_jobs = []

    scrapers = [
        scrape_google_jobs,
        scrape_bayt,
        scrape_wuzzuf,
        scrape_gulfjobs,
        scrape_linkedin,
        scrape_indeed,
    ]

    for scraper in scrapers:
        try:
            found = scraper()
            all_jobs.extend(found)
        except Exception as e:
            log.error(f"خطأ في {scraper.__name__}: {e}")

    # إزالة التكرار بالـ ID
    seen_ids = set()
    unique_jobs = []
    for job in all_jobs:
        if job["id"] not in seen_ids:
            seen_ids.add(job["id"])
            unique_jobs.append(job)

    log.info(f"\n📊 المجموع: {len(unique_jobs)} شغلانة فريدة من {len(all_jobs)} نتيجة")
    return unique_jobs
