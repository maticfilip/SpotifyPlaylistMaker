from imports import *

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
}
BASE_URL = "https://musicchartsarchive.com/album-chart/"

def _format_date_for_url(d):
    if isinstance(d, str):
        return d
    if isinstance(d, datetime):
        return d.date().isoformat()
    if isinstance(d, date):
        return d.isoformat()
    raise ValueError("date must be a str or datetime/date object")

def fetch_page(date_input):
    date_str = _format_date_for_url(date_input)
    url = f"{BASE_URL}{date_str}/"
    res = requests.get(url, headers=HEADERS, timeout=15)
    return res.status_code, res.text

def extract_songs_from_html(html):
    soup = BeautifulSoup(html, "html.parser")

    main = soup.find(id="content") or soup
    view = main.find(class_="view-chart-albums")
    container = view if view else main

    songs = []

    for tr in container.find_all("tr", class_=["odd", "even"]):
        a = tr.find("a")
        if a:
            txt = a.get_text(strip=True)
            if txt:
                songs.append(txt)

    if not songs:
        table = container.find("table")
        if table:
            for tr in table.find_all("tr"):
                a = tr.find("a")
                if a:
                    txt = a.get_text(strip=True)
                    if txt:
                        songs.append(txt)

    if not songs:
        for a in container.find_all("a"):
            txt = a.get_text(strip=True)
            if txt and len(txt) > 2 and not txt.lower().startswith(("read", "view", "more")):
                songs.append(txt)

    seen = set()
    filtered = []
    for s in songs:
        if s not in seen:
            seen.add(s)
            filtered.append(s)
    return filtered

def get_valid_chart_page(date_input):
    status, html = fetch_page(date_input)
    if status != 200:
        return None, None

    songs = extract_songs_from_html(html)
    if songs:
        return html, songs
    return None, None

def find_nearest(date_input, daily_window=7, weekly_weeks=52, pause=0.2):
    if isinstance(date_input, str):
        try:
            base = datetime.strptime(date_input, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("date string must be in YYYY-MM-DD format")
    elif isinstance(date_input, datetime):
        base = date_input.date()
    elif isinstance(date_input, date):
        base = date_input
    else:
        raise ValueError("date_input must be a str or datetime/date")

    for d in range(daily_window):
        candidate = base - timedelta(days=d)
        html, songs = get_valid_chart_page(candidate)
        if html:
            return candidate.isoformat(), songs
        time.sleep(pause)

    candidate = base - timedelta(days=daily_window)
    for w in range(weekly_weeks):
        candidate -= timedelta(days=7)
        html, songs = get_valid_chart_page(candidate)
        if html:
            return candidate.isoformat(), songs
        time.sleep(pause)

    return None, None