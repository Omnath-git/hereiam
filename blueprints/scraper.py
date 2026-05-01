# blueprints/scraper.py
import threading
import time
import random
import re
from datetime import datetime, timedelta
from urllib.parse import urljoin, quote

import requests
from bs4 import BeautifulSoup
from flask import Blueprint, jsonify, flash, redirect, url_for

from models import db, Job

scraper_bp = Blueprint('scraper', __name__)

# ============================================================
# CONFIGURATION
# ============================================================

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/118.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148',
]

# ============================================================
# ⭐ SCRAPING STATS TRACKER
# ============================================================

class ScrapeStats:
    """Track scraping progress and stats"""
    def __init__(self):
        self.total_websites = 0
        self.websites_done = 0
        self.websites_success = 0
        self.total_jobs_found = 0
        self.total_jobs_added = 0
        self.total_jobs_skipped = 0
        self.current_website = ""
        self.start_time = None
        self.is_running = False
    
    def start(self):
        self.start_time = datetime.utcnow()
        self.is_running = True
    
    def finish(self):
        self.is_running = False
    
    def get_progress(self):
        if self.total_websites == 0:
            return 0
        return int((self.websites_done / self.total_websites) * 100)
    
    def get_elapsed(self):
        if self.start_time:
            return str(datetime.utcnow() - self.start_time).split('.')[0]
        return "0:00"

# Global stats instance
scrape_stats = ScrapeStats()

# ============================================================
# 50+ INDIAN JOB WEBSITES
# ============================================================

ALL_JOB_WEBSITES = {
    # General Portals
    'naukri': {
        'name': 'Naukri.com',
        'base_url': 'https://www.naukri.com/{keyword}-jobs?k={keyword}',
        'card_selectors': ['.jobTuple', '[class*="jobTuple"]', '.list-item', 'article'],
        'title_selectors': ['a.title', '.jobTuple-title', 'h2 a', '.title'],
        'company_selectors': ['.subTitle', '.companyName', '.orgName'],
        'location_selectors': ['.location', '.loc', '.fleft'],
        'link_selector': 'a.title',
    },
    'indeed': {
        'name': 'Indeed India',
        'base_url': 'https://in.indeed.com/jobs?q={keyword}&l={location}',
        'card_selectors': ['.job_seen_beacon', '.cardOutline', '.resultContent'],
        'title_selectors': ['h2.jobTitle', 'h2 span', 'a.jobTitle', '.title a'],
        'company_selectors': ['.companyName', '.company_name', 'span.companyName'],
        'location_selectors': ['.companyLocation', '.location', '.recJobLoc'],
        'link_selector': 'a.jobTitle',
    },
    'linkedin': {
        'name': 'LinkedIn Jobs',
        'base_url': 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={keyword}&location={location}&start=0',
        'card_selectors': ['.base-card', '.job-search-card', 'li'],
        'title_selectors': ['.base-search-card__title', '.job-search-card__title', 'h3'],
        'company_selectors': ['.base-search-card__subtitle', '.job-search-card__subtitle', 'h4'],
        'location_selectors': ['.job-search-card__location', '.location'],
        'link_selector': 'a.base-card__full-link',
    },
    'foundit': {
        'name': 'Foundit (Monster)',
        'base_url': 'https://www.foundit.in/jobs?q={keyword}',
        'card_selectors': ['.jobCard', '[class*="job"]', '.card'],
        'title_selectors': ['h3', '.title', '[class*="title"]'],
        'company_selectors': ['.company', '.org', '[class*="company"]'],
        'location_selectors': ['.location', '[class*="location"]'],
        'link_selector': 'a',
    },
    'shine': {
        'name': 'Shine.com',
        'base_url': 'https://www.shine.com/jobs/search?q={keyword}',
        'card_selectors': ['.jobCard', '.resultCard', '[class*="job"]'],
        'title_selectors': ['h3', '.title', 'a strong'],
        'company_selectors': ['.company', '.org'],
        'location_selectors': ['.location'],
        'link_selector': 'a',
    },
    'freshersworld': {
        'name': 'Freshersworld',
        'base_url': 'https://www.freshersworld.com/jobs?q={keyword}',
        'card_selectors': ['.job-container', '.job-list', '[class*="job"]'],
        'title_selectors': ['h3', '.job-title', 'a strong'],
        'company_selectors': ['.company-name', '.company'],
        'location_selectors': ['.location'],
        'link_selector': 'a',
    },
    'internshala': {
        'name': 'Internshala',
        'base_url': 'https://internshala.com/jobs/search?keyword={keyword}',
        'card_selectors': ['.individual_internship', '[class*="individual"]'],
        'title_selectors': ['h3', 'h4', '.heading_4_5', '.job-title'],
        'company_selectors': ['.company-name', '.company_name', '.link_display_like_text'],
        'location_selectors': ['.location', '#location_names'],
        'link_selector': 'a',
    },
    'apna': {
        'name': 'Apna.co',
        'base_url': 'https://apna.co/jobs?q={keyword}',
        'card_selectors': ['.job-card', '[class*="job"]'],
        'title_selectors': ['h3', '.title', 'a'],
        'company_selectors': ['.employer-name', '.company'],
        'location_selectors': ['.location'],
        'link_selector': 'a',
    },
    'workindia': {
        'name': 'WorkIndia',
        'base_url': 'https://www.workindia.in/jobs?q={keyword}',
        'card_selectors': ['.job-card', '[class*="job"]'],
        'title_selectors': ['h3', '.title'],
        'company_selectors': ['.company'],
        'location_selectors': ['.location'],
        'link_selector': 'a',
    },
    'timesjobs': {
        'name': 'TimesJobs',
        'base_url': 'https://www.timesjobs.com/jobfunction/{keyword}-jobs',
        'card_selectors': ['.job-listing', '[class*="job"]', '.result'],
        'title_selectors': ['h3', '.title', 'a'],
        'company_selectors': ['.company', '.org'],
        'location_selectors': ['.location'],
        'link_selector': 'a',
    },
    
    # IT/Tech Specific
    'cutshort': {
        'name': 'Cutshort',
        'base_url': 'https://cutshort.io/jobs?q={keyword}',
        'card_selectors': ['.job-card', '[class*="job"]'],
        'title_selectors': ['h3', '.title', 'a strong'],
        'company_selectors': ['.company', '.org-name'],
        'location_selectors': ['.location'],
        'link_selector': 'a',
    },
    'hirist': {
        'name': 'Hirist',
        'base_url': 'https://www.hirist.tech/jobs?q={keyword}',
        'card_selectors': ['.job-listing', '[class*="job"]'],
        'title_selectors': ['h3', '.title'],
        'company_selectors': ['.company'],
        'location_selectors': ['.location'],
        'link_selector': 'a',
    },
    'wellfound': {
        'name': 'Wellfound (AngelList)',
        'base_url': 'https://wellfound.com/jobs?q={keyword}&location=india',
        'card_selectors': ['.job-listing', '[class*="job"]', '.result'],
        'title_selectors': ['h3', '.title', 'a'],
        'company_selectors': ['.company', '.startup-name'],
        'location_selectors': ['.location'],
        'link_selector': 'a',
    },
    
    # Government
    'ncs': {
        'name': 'NCS Portal',
        'base_url': 'https://www.ncs.gov.in/_layouts/15/NCS/JobsSearch.aspx?q={keyword}',
        'card_selectors': ['.job-listing', '[class*="job"]', '.card', '.result'],
        'title_selectors': ['h3', 'h4', '.title', 'a'],
        'company_selectors': ['.company', '.employer', '.org'],
        'location_selectors': ['.location'],
        'link_selector': 'a',
    },
    'sarkariresult': {
        'name': 'Sarkari Result',
        'base_url': 'https://www.sarkariresult.com/jobs/?s={keyword}',
        'card_selectors': ['.job-listing', '[class*="job"]', 'li'],
        'title_selectors': ['h3', '.title', 'a'],
        'company_selectors': ['.dept'],
        'location_selectors': ['.location'],
        'link_selector': 'a',
    },
    
    # ⭐ NGO/Social Sector
    'sams': {
        'name': 'SAMS - Social Sector Jobs',
        'base_url': 'https://www.sams.co.in/Jobs/job-list',
        'card_selectors': ['.job-listing', '.job-item', '[class*="job"]', 'article', '.listing-item'],
        'title_selectors': ['h3', 'h4', '.job-title', '.title', 'a strong'],
        'company_selectors': ['.company', '.org', '.organization', '.employer'],
        'location_selectors': ['.location', '.city', '.job-location'],
        'link_selector': 'a',
        'static_url': True,
    },
    'devnetjobsindia': {
        'name': 'DevNetJobs India',
        'base_url': 'https://devnetjobsindia.org/?s={keyword}',
        'card_selectors': ['.job-listing', '[class*="job"]', '.post'],
        'title_selectors': ['h3', '.title', 'a'],
        'company_selectors': ['.organization', '.company'],
        'location_selectors': ['.location'],
        'link_selector': 'a',
    },
    'arthan': {
        'name': 'Arthan Careers',
        'base_url': 'https://arthancareers.com/job-listing/?search={keyword}',
        'card_selectors': ['.job-listing', '[class*="job"]'],
        'title_selectors': ['h3', '.title'],
        'company_selectors': ['.organization', '.company'],
        'location_selectors': ['.location'],
        'link_selector': 'a',
    },
    'idealist': {
        'name': 'Idealist (NGO Jobs)',
        'base_url': 'https://www.idealist.org/en/jobs?q={keyword}&location=India',
        'card_selectors': ['.job-listing', '[class*="job"]', '.result'],
        'title_selectors': ['h3', '.title', 'a'],
        'company_selectors': ['.organization', '.company'],
        'location_selectors': ['.location'],
        'link_selector': 'a',
    },
    'reliefweb': {
        'name': 'ReliefWeb Jobs',
        'base_url': 'https://reliefweb.int/jobs?search={keyword}&country=India',
        'card_selectors': ['.job-listing', '[class*="job"]', 'article'],
        'title_selectors': ['h3', 'h4', '.title a'],
        'company_selectors': ['.company', '.source', '.organization'],
        'location_selectors': ['.location', '.country'],
        'link_selector': 'a',
    },
    'impactpool': {
        'name': 'Impactpool',
        'base_url': 'https://www.impactpool.org/?q={keyword}&location=India',
        'card_selectors': ['.job-listing', '[class*="job"]'],
        'title_selectors': ['h3', '.title', 'a'],
        'company_selectors': ['.organization', '.company'],
        'location_selectors': ['.location'],
        'link_selector': 'a',
    },
    'devex': {
        'name': 'Devex Jobs',
        'base_url': 'https://www.devex.com/jobs/search?filter%5Bkeywords%5D={keyword}&filter%5Blocations%5D=India',
        'card_selectors': ['.job-listing', '[class*="job"]'],
        'title_selectors': ['h3', '.title'],
        'company_selectors': ['.organization', '.company'],
        'location_selectors': ['.location'],
        'link_selector': 'a',
    },
    'unjobnet': {
        'name': 'UN Job Net',
        'base_url': 'https://www.unjobnet.org/?q={keyword}&location=India',
        'card_selectors': ['.job-listing', '[class*="job"]', '.vacancy'],
        'title_selectors': ['h3', '.title', 'a'],
        'company_selectors': ['.organization', '.agency'],
        'location_selectors': ['.location', '.country'],
        'link_selector': 'a',
    },
    'devnetjobs': {
        'name': 'DevNetJobs Global',
        'base_url': 'https://devnetjobs.org/?s={keyword}',
        'card_selectors': ['.job-listing', '[class*="job"]'],
        'title_selectors': ['h3', '.title', 'a strong'],
        'company_selectors': ['.organization', '.company'],
        'location_selectors': ['.location'],
        'link_selector': 'a',
    },
    
    # Sector Specific
    'docthub': {
        'name': 'Docthub (Healthcare)',
        'base_url': 'https://www.docthub.com/jobs?q={keyword}',
        'card_selectors': ['.job-listing', '[class*="job"]'],
        'title_selectors': ['h3', '.title'],
        'company_selectors': ['.hospital', '.clinic', '.company'],
        'location_selectors': ['.location'],
        'link_selector': 'a',
    },
    'lawbhoomi': {
        'name': 'LawBhoomi (Legal)',
        'base_url': 'https://lawbhoomi.com/jobs/?s={keyword}',
        'card_selectors': ['.job-listing', '[class*="job"]'],
        'title_selectors': ['h3', '.title'],
        'company_selectors': ['.firm', '.company'],
        'location_selectors': ['.location'],
        'link_selector': 'a',
    },
    'classdoor': {
        'name': 'ClassDoor (Education)',
        'base_url': 'https://www.classdoor.in/jobs?q={keyword}',
        'card_selectors': ['.job-listing', '[class*="job"]'],
        'title_selectors': ['h3', '.title'],
        'company_selectors': ['.school', '.college', '.institute'],
        'location_selectors': ['.location'],
        'link_selector': 'a',
    },
    
    # Aggregators
    'careerjet': {
        'name': 'CareerJet India',
        'base_url': 'https://www.careerjet.co.in/search/jobs?q={keyword}',
        'card_selectors': ['.job-listing', '[class*="job"]', '.result'],
        'title_selectors': ['h3', '.title', 'a'],
        'company_selectors': ['.company'],
        'location_selectors': ['.location'],
        'link_selector': 'a',
    },
    'jobrapido': {
        'name': 'JobRapido India',
        'base_url': 'https://in.jobrapido.com/?q={keyword}',
        'card_selectors': ['.job-listing', '[class*="job"]'],
        'title_selectors': ['h3', '.title'],
        'company_selectors': ['.company'],
        'location_selectors': ['.location'],
        'link_selector': 'a',
    },
    'fresherslive': {
        'name': 'FreshersLive',
        'base_url': 'https://www.fresherslive.com/jobs?q={keyword}',
        'card_selectors': ['.job-listing', '[class*="job"]'],
        'title_selectors': ['h3', '.title'],
        'company_selectors': ['.company'],
        'location_selectors': ['.location'],
        'link_selector': 'a',
    },
    'freejobalert': {
        'name': 'Free Job Alert',
        'base_url': 'https://www.freejobalert.com/?s={keyword}',
        'card_selectors': ['.job-listing', '[class*="job"]', '.post'],
        'title_selectors': ['h3', '.title', 'a'],
        'company_selectors': ['.dept'],
        'location_selectors': ['.location'],
        'link_selector': 'a',
    },
    'herkey': {
        'name': 'HerKey (Women)',
        'base_url': 'https://www.herkey.com/jobs?q={keyword}',
        'card_selectors': ['.job-listing', '[class*="job"]'],
        'title_selectors': ['h3', '.title'],
        'company_selectors': ['.company'],
        'location_selectors': ['.location'],
        'link_selector': 'a',
    },
}

# ============================================================
# ⭐ SEARCH KEYWORDS (50+ Categories)
# ============================================================

SEARCH_KEYWORDS = {
    'software_developer': ['software developer', 'software engineer', 'programmer'],
    'python_developer': ['python developer', 'django developer', 'python engineer'],
    'java_developer': ['java developer', 'java engineer', 'spring boot developer'],
    'javascript_developer': ['react developer', 'angular developer', 'node.js developer'],
    'dotnet_developer': ['.net developer', 'c# developer', 'asp.net developer'],
    'php_developer': ['php developer', 'laravel developer', 'wordpress developer'],
    'mobile_developer': ['android developer', 'ios developer', 'flutter developer'],
    'devops_engineer': ['devops engineer', 'cloud engineer', 'aws engineer'],
    'data_scientist': ['data scientist', 'data analyst', 'machine learning engineer'],
    'cybersecurity': ['cybersecurity analyst', 'security engineer', 'ethical hacker'],
    'qa_engineer': ['qa engineer', 'test engineer', 'automation tester'],
    'database_admin': ['database administrator', 'sql developer', 'data engineer'],
    'system_admin': ['system administrator', 'network engineer', 'it support'],
    'ui_ux': ['ui designer', 'ux designer', 'product designer'],
    'project_manager': ['project manager', 'scrum master', 'delivery manager'],
    'product_manager': ['product manager', 'product owner', 'business analyst'],
    'hr_recruitment': ['hr manager', 'recruiter', 'talent acquisition'],
    'finance_accounting': ['accountant', 'finance manager', 'chartered accountant'],
    'marketing_sales': ['marketing manager', 'digital marketing', 'sales executive', 'business development'],
    'operations': ['operations manager', 'supply chain', 'logistics'],
    'doctor': ['doctor', 'physician', 'medical officer'],
    'nurse': ['nurse', 'staff nurse', 'nursing officer'],
    'pharmacist': ['pharmacist', 'medical representative'],
    'lab_technician': ['lab technician', 'medical lab technologist'],
    'teacher': ['teacher', 'professor', 'lecturer', 'faculty'],
    'civil_engineer': ['civil engineer', 'structural engineer', 'site engineer'],
    'mechanical_engineer': ['mechanical engineer', 'design engineer', 'production engineer'],
    'electrical_engineer': ['electrical engineer', 'electronics engineer'],
    'lawyer': ['lawyer', 'attorney', 'legal advisor', 'legal counsel'],
    'content_writer': ['content writer', 'copywriter', 'technical writer'],
    'government_jobs': ['government job', 'sarkari naukri', 'public sector', 'psu jobs'],
    'banking': ['banking', 'bank job', 'bank po', 'bank clerk', 'insurance'],
    'defence': ['defence job', 'army', 'navy', 'air force', 'police'],
    'railway': ['railway job', 'rrb', 'rrb ntpc', 'railway recruitment'],
    'ngo_program': ['program manager ngo', 'program officer', 'development sector'],
    'social_work': ['social worker', 'community development', 'csr'],
    'fundraising': ['fundraising', 'partnerships', 'resource mobilization'],
    'humanitarian': ['humanitarian', 'relief work', 'disaster management'],
    'public_health_ngo': ['public health', 'health program', 'community health'],
    'fresher': ['fresher', 'trainee', 'intern', 'entry level', 'graduate trainee'],
    'work_from_home': ['work from home', 'remote job', 'virtual job'],
    'part_time': ['part time', 'weekend job', 'freelance'],
    'manufacturing': ['manufacturing', 'factory', 'production', 'assembly'],
    'retail': ['retail', 'store manager', 'merchandiser', 'sales associate'],
    'hospitality': ['hotel', 'restaurant', 'chef', 'cook', 'housekeeping'],
    'logistics': ['delivery', 'driver', 'warehouse', 'shipping', 'fleet manager'],
    'real_estate': ['real estate', 'property manager', 'broker'],
    'agriculture': ['agriculture', 'farming', 'agribusiness', 'food technology'],
    'automobile': ['automobile', 'mechanic', 'car service', 'automotive'],
    'textile': ['textile', 'garment', 'fashion designer', 'apparel'],
}

INDIAN_CITIES = [
    'Mumbai', 'Delhi', 'Bangalore', 'Hyderabad', 'Chennai', 'Kolkata', 'Pune', 'Ahmedabad',
    'Jaipur', 'Lucknow', 'Indore', 'Bhopal', 'Chandigarh', 'Kochi', 'Coimbatore',
    'Nagpur', 'Surat', 'Vadodara', 'Noida', 'Gurgaon', 'Bhubaneswar', 'Patna',
    'Ranchi', 'Dehradun', 'Guwahati', 'Thiruvananthapuram', 'India', 'Remote',
]

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_random_headers():
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'DNT': '1',
    }

def safe_request(url, timeout=15, max_retries=2):
    for attempt in range(max_retries):
        try:
            session = requests.Session()
            session.headers.update(get_random_headers())
            response = session.get(url, timeout=timeout, allow_redirects=True)
            if response.status_code == 200:
                return response
            time.sleep(1)
        except:
            time.sleep(2)
    return None

def clean_text(text):
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text).strip()[:300]

def standardize_job(job_dict):
    return {
        'title': clean_text(job_dict.get('title', ''))[:200],
        'company': clean_text(job_dict.get('company', 'Unknown'))[:200],
        'location': clean_text(job_dict.get('location', 'India'))[:200],
        'salary_range': clean_text(job_dict.get('salary_range', 'Not Disclosed'))[:100],
        'experience_required': clean_text(job_dict.get('experience_required', 'Not Specified'))[:50],
        'job_type': clean_text(job_dict.get('job_type', 'Full-time'))[:50],
        'description': clean_text(job_dict.get('description', ''))[:500],
        'requirements': clean_text(job_dict.get('requirements', ''))[:500],
        'skills_required': clean_text(job_dict.get('skills_required', ''))[:500],
        'apply_method': job_dict.get('apply_method', 'website'),
        'apply_email': job_dict.get('apply_email', ''),
        'apply_website': job_dict.get('apply_website', ''),
        'source': 'scraped',
        'source_url': job_dict.get('source_url', ''),
        'is_active': True,
        'posted_date': datetime.utcnow(),
        'last_updated': datetime.utcnow()
    }

def extract_jobs_from_html(soup, url, config):
    jobs = []
    cards = []
    
    for selector in config.get('card_selectors', []):
        cards = soup.select(selector)
        if cards:
            break
    
    if not cards:
        cards = soup.select('a[href*="job"], a[href*="career"], [class*="job"], [class*="vacancy"]')[:20]
    
    for card in cards:
        title = company = location = ''
        
        for sel in config.get('title_selectors', []):
            elem = card.select_one(sel)
            if elem:
                title = elem.text.strip()
                if title and len(title) > 3:
                    break
        
        for sel in config.get('company_selectors', []):
            elem = card.select_one(sel)
            if elem:
                company = elem.text.strip()
                if company and company != title:
                    break
        
        for sel in config.get('location_selectors', []):
            elem = card.select_one(sel)
            if elem:
                location = elem.text.strip()
                if location:
                    break
        
        job_link = ''
        link_elem = card.select_one(config.get('link_selector', 'a'))
        if link_elem:
            href = link_elem.get('href', '')
            if href:
                job_link = urljoin(url, href)
        
        if title and len(title) > 3:
            jobs.append(standardize_job({
                'title': title,
                'company': company or 'Company',
                'location': location or 'India',
                'apply_method': 'website',
                'apply_website': job_link or url,
                'source_url': job_link or url,
            }))
    
    return jobs[:3]


def scrape_single_search(keyword, location, config):
    """Scrape single search"""
    jobs = []
    try:
        if config.get('static_url'):
            url = config['base_url']
        else:
            url = config['base_url'].format(keyword=quote(keyword), location=quote(location))
        
        response = safe_request(url, timeout=10)
        if response:
            soup = BeautifulSoup(response.text, 'html.parser')
            jobs = extract_jobs_from_html(soup, url, config)
    except:
        pass
    return jobs


# ============================================================
# ⭐ INCREMENTAL SAVE FUNCTION
# ============================================================

# blueprints/scraper.py - save_jobs_incremental फंक्शन में

def save_jobs_incremental(jobs_batch):
    """Save a batch of jobs with retry on lock"""
    added = 0
    skipped = 0
    
    for job_data in jobs_batch:
        existing = Job.query.filter_by(
            title=job_data['title'],
            company=job_data['company'],
            source='scraped'
        ).first()
        
        if not existing:
            try:
                job = Job(**job_data)
                db.session.add(job)
                added += 1
            except:
                skipped += 1
        else:
            skipped += 1
    
    if added > 0:
        # ⭐ Retry on lock
        for attempt in range(5):
            try:
                db.session.commit()
                break
            except Exception as e:
                db.session.rollback()
                if 'database is locked' in str(e) and attempt < 4:
                    time.sleep(0.5 * (attempt + 1))
                    continue
                raise e
    
    return added, skipped

# ============================================================
# ⭐ AUTO-DELETE OLD JOBS (7 Days)
# ============================================================

def delete_old_jobs():
    """Delete scraped jobs older than 7 days"""
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    deleted = Job.query.filter(
        Job.source == 'scraped',
        Job.posted_date < seven_days_ago
    ).delete()
    
    if deleted:
        db.session.commit()
        print(f"🗑️ Auto-deleted {deleted} old jobs (older than 7 days)")
    
    return deleted


# ============================================================
# ⭐ COMPREHENSIVE SCRAPER WITH INCREMENTAL SAVE
# ============================================================

def scrape_all_domains():
    """Scrape all domains with incremental saving"""
    global scrape_stats
    
    # ⭐ First: Delete old jobs
    delete_old_jobs()
    
    # ⭐ Initialize stats
    scrape_stats = ScrapeStats()
    scrape_stats.start()
    scrape_stats.total_websites = len(ALL_JOB_WEBSITES)
    
    all_jobs = []
    website_keys = list(ALL_JOB_WEBSITES.keys())
    random.shuffle(website_keys)
    
    print(f"\n{'='*70}")
    print(f"🔍 COMPREHENSIVE SCRAPING: {scrape_stats.total_websites} Websites")
    print(f"📋 Categories: {len(SEARCH_KEYWORDS)}")
    print(f"⏱️  Started at: {scrape_stats.start_time.strftime('%H:%M:%S')}")
    print(f"{'='*70}")
    
    for site_key in website_keys:
        config = ALL_JOB_WEBSITES[site_key]
        site_name = config['name']
        scrape_stats.current_website = site_name
        scrape_stats.websites_done += 1
        site_jobs = []
        
        # Pick 2 random categories
        selected_categories = random.sample(list(SEARCH_KEYWORDS.keys()), min(2, len(SEARCH_KEYWORDS)))
        
        for category in selected_categories:
            keyword = random.choice(SEARCH_KEYWORDS[category])
            location = random.choice(INDIAN_CITIES[:10] + ['India'])
            
            try:
                jobs = scrape_single_search(keyword, location, config)
                if jobs:
                    site_jobs.extend(jobs)
                    all_jobs.extend(jobs)
                    
                    # ⭐ INCREMENTAL SAVE: Save every 10 jobs
                    if len(all_jobs) >= 10:
                        added, skipped = save_jobs_incremental(all_jobs)
                        scrape_stats.total_jobs_added += added
                        scrape_stats.total_jobs_skipped += skipped
                        scrape_stats.total_jobs_found += len(all_jobs)
                        
                        progress = scrape_stats.get_progress()
                        elapsed = scrape_stats.get_elapsed()
                        print(f"  💾 Saved! Progress: {progress}% | "
                              f"Site: {scrape_stats.websites_done}/{scrape_stats.total_websites} | "
                              f"Jobs: +{added} new | "
                              f"Time: {elapsed}")
                        
                        all_jobs = []  # Clear batch
            
            except Exception as e:
                pass
        
        if site_jobs:
            scrape_stats.websites_success += 1
            print(f"  ✅ {site_name}: {len(site_jobs)} jobs | "
                  f"Progress: {scrape_stats.get_progress()}%")
        else:
            print(f"  ⚠️ {site_name}: No jobs | "
                  f"Progress: {scrape_stats.get_progress()}%")
    
    # ⭐ Save remaining jobs
    if all_jobs:
        added, skipped = save_jobs_incremental(all_jobs)
        scrape_stats.total_jobs_added += added
        scrape_stats.total_jobs_skipped += skipped
        scrape_stats.total_jobs_found += len(all_jobs)
    
    # ⭐ Final cleanup
    delete_old_jobs()
    
    scrape_stats.finish()
    elapsed = scrape_stats.get_elapsed()
    
    print(f"\n{'='*70}")
    print(f"📊 FINAL RESULTS:")
    print(f"   Websites: {scrape_stats.websites_success}/{scrape_stats.total_websites} successful")
    print(f"   Jobs found: {scrape_stats.total_jobs_found}")
    print(f"   Jobs added: {scrape_stats.total_jobs_added}")
    print(f"   Jobs skipped: {scrape_stats.total_jobs_skipped}")
    print(f"   Time taken: {elapsed}")
    print(f"{'='*70}")
    
    return scrape_stats.total_jobs_added


def scrape_lightweight():
    """Lightweight scraper for scheduled runs"""
    # ⭐ Delete old jobs first
    delete_old_jobs()
    
    all_jobs = []
    sites = random.sample(list(ALL_JOB_WEBSITES.keys()), min(5, len(ALL_JOB_WEBSITES)))
    
    print(f"\n🔄 Lightweight scrape: {len(sites)} websites")
    
    for site_key in sites:
        config = ALL_JOB_WEBSITES[site_key]
        category = random.choice(list(SEARCH_KEYWORDS.keys()))
        keyword = random.choice(SEARCH_KEYWORDS[category])
        location = random.choice(INDIAN_CITIES[:10])
        
        try:
            jobs = scrape_single_search(keyword, location, config)
            if jobs:
                all_jobs.extend(jobs)
                # ⭐ Save immediately
                added, _ = save_jobs_incremental(jobs)
                print(f"  ✅ {config['name']}: +{added} jobs")
        except:
            pass
    
    print(f"📊 Light scrape done: {len(all_jobs)} jobs found")
    return len(all_jobs)


# ============================================================
# SCHEDULER
# ============================================================

def start_job_scraper(app):
    def run():
        time.sleep(10)
        with app.app_context():
            print("\n🚀 INITIAL FULL SCRAPE...")
            scrape_all_domains()
        
        while True:
            time.sleep(36000)  # 1 hour
            with app.app_context():
                print("\n🔄 SCHEDULED LIGHT SCRAPE...")
                scrape_lightweight()
    
    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    print("🔄 Scraper started (Full on start, Light every 1h, Auto-delete 7d)")


# ============================================================
# ROUTES
# ============================================================

@scraper_bp.route('/scrape-jobs-now')
def scrape_jobs_now():
    try:
        count = scrape_all_domains()
        flash(f'✅ Scraped {count} jobs! Progress saved every 10 jobs.', 'success')
    except Exception as e:
        flash(f'❌ Error: {str(e)[:100]}', 'error')
    return redirect(url_for('main.index', tab='jobs'))

@scraper_bp.route('/api/scrape-status')
def scrape_status():
    total = Job.query.filter_by(source='scraped', is_active=True).count()
    latest = Job.query.filter_by(source='scraped').order_by(Job.posted_date.desc()).first()
    
    # Delete old jobs on status check
    deleted = delete_old_jobs()
    
    return jsonify({
        'total_scraped_jobs': total,
        'last_scraped': latest.posted_date.strftime('%d %b, %Y %H:%M') if latest else 'Never',
        'websites': len(ALL_JOB_WEBSITES),
        'categories': len(SEARCH_KEYWORDS),
        'old_jobs_deleted': deleted,
        'scraper_running': scrape_stats.is_running,
        'progress': scrape_stats.get_progress() if scrape_stats.is_running else 100,
        'current_website': scrape_stats.current_website if scrape_stats.is_running else 'Idle',
    })

@scraper_bp.route('/api/delete-old-jobs')
def api_delete_old_jobs():
    """Manual trigger to delete old jobs"""
    deleted = delete_old_jobs()
    return jsonify({'success': True, 'deleted': deleted, 'message': f'Deleted {deleted} old jobs'})