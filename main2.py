import re
from datetime import datetime
from typing import Optional, Tuple, List
import requests
from bs4 import BeautifulSoup

DATE_RE = re.compile(r'^[A-Za-z]{3,9}\s+\d{1,2},\s*\d{4}$')  # e.g. "Jan 17, 1998" or "January 17, 1998"

def fetch_archive_links(url: str) -> List[Tuple[datetime.date, str]]:
    """
    Scrape `url` and return list of (date, href) for each week entry found.
    Adjust the selector if weeks live in a particular element.
    """
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')

    results = []
    for a in soup.find_all('a'):
        text = a.get_text(strip=True)
        if DATE_RE.match(text):
            # try parsing with abbreviated and full month names
            try:
                dt = datetime.strptime(text, "%b %d, %Y")  # "Jan 17, 1998"
            except ValueError:
                dt = datetime.strptime(text, "%B %d, %Y")  # "January 17, 1998"
            href = a.get('href')
            # normalize absolute/relative if you want: requests.compat.urljoin(url, href)
            results.append((dt.date(), href))
    # dedupe & sort by date
    results = sorted({(d, h) for (d, h) in results}, key=lambda x: x[0])
    return results

def find_week_for_date(available: List[Tuple[datetime.date, str]], user_date_str: str) -> Optional[Tuple[datetime.date, str]]:
    """
    Given available (date, href) pairs, and a user_date_str like '1998-01-18',
    return the (week_date, href) where week_date is the greatest available date <= user_date.
    If none found, return None.
    """
    user_date = datetime.strptime(user_date_str, "%Y-%m-%d").date()
    # filter candidates <= user_date
    candidates = [(d, h) for (d, h) in available if d <= user_date]
    if not candidates:
        return None
    # pick the latest one
    best = max(candidates, key=lambda x: x[0])
    return best

# ---- Example usage ----
archive_url = "https://musicchartsarchive.com/album-chart/"   # the page you scrape
available_weeks = fetch_archive_links(archive_url)
user_input = "1998-01-18"

matched = find_week_for_date(available_weeks, user_input)
if matched:
    week_date, href = matched
    print("User date:", user_input)
    print("Matched week:", week_date.isoformat(), "->", href)
else:
    print("No available week found on or before", user_input)
