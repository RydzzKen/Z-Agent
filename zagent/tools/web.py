"""Web tools: fetch a single page and search via DuckDuckGo HTML."""
import requests
from bs4 import BeautifulSoup

from ..ui import colors


def fetch_web_page(url):
    """Membaca teks dari URL halaman web tertentu."""
    try:
        headers_web = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        res = requests.get(url, headers=headers_web, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')

        paragraphs = [p.get_text() for p in soup.find_all('p')]
        text_content = "\n".join(paragraphs[:10])
        return f"--- ISI WEB ({url}) ---\n{text_content[:2000]}"
    except Exception as e:
        return f"Error membaca web: {e}"


def search_web(query, num_results=5):
    """Cari informasi di internet via DuckDuckGo HTML (tanpa API key)."""
    try:
        from urllib.parse import quote_plus, urlparse, parse_qs
        headers_web = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        res = requests.get(url, headers=headers_web, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')

        results = []
        for a in soup.select('a.result__a')[:num_results]:
            title = a.get_text(strip=True)
            href = a.get('href', '')
            if 'uddg=' in href:
                href = parse_qs(urlparse(href).query).get('uddg', [''])[0]
            snippet = ''
            parent = a.find_parent('div', class_='result') or a
            sn = parent.select_one('.result__snippet')
            if sn:
                snippet = sn.get_text(strip=True)
            results.append(f"🔎 {title}\n   {href}\n   {snippet}")

        if not results:
            return f"Tidak ada hasil untuk: '{query}'"
        return "--- HASIL PENCARIAN WEB ---\n" + "\n\n".join(results)
    except Exception as e:
        return f"Error pencarian web: {e}"
