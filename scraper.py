import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}

def get_html(url, timeout=10):
    try:
        if not str(url).startswith('http'):
            url = 'https://' + str(url)
        response = requests.get(url, headers=HEADERS, timeout=timeout)
        response.raise_for_status()
        return response.text
    except Exception as e:
        # Silently catch to avoid spamming the console too much, or could log it quietly
        return None

def find_subpages(html, base_url):
    try:
        soup = BeautifulSoup(html, 'html.parser')
        links = set()
        keywords = ['about', 'team', 'contact', 'staff', 'meet']
        
        for a in soup.find_all('a', href=True):
            href = a['href']
            text = a.get_text().lower()
            if any(k in href.lower() or k in text for k in keywords):
                full_url = urljoin(base_url, href)
                if urlparse(full_url).netloc == urlparse(base_url).netloc:
                    links.add(full_url)
        return list(links)[:3]
    except Exception:
        return []

def extract_text(html):
    if not html:
        return ""
    try:
        soup = BeautifulSoup(html, 'html.parser')
        for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
            script.extract()
        text = soup.get_text(separator=' ')
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        return ' '.join(chunk for chunk in chunks if chunk)
    except Exception:
        return ""
