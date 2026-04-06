
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, StreamingResponse
import requests, re, io, csv
from bs4 import BeautifulSoup

app = FastAPI()

HTML = '''
<html><body style="font-family:Arial;padding:30px">
<h2>Public Candidate URL Finder</h2>
<form action="/search" method="post">
<textarea name="jd" rows="10" cols="80" placeholder="Paste Job Description"></textarea><br><br>
<input name="location" placeholder="Location (e.g. Hyderabad)" />
<button type="submit">Find Public Profiles</button>
</form>
</body></html>
'''

def extract_title(jd: str):
    m = re.search(r'(Data Analyst|BI Analyst|Business Analyst|Python Developer)', jd, re.I)
    return m.group(1) if m else "Data Analyst"

def search_public_profiles(title: str, location: str, limit: int = 100):
    q = f'site:linkedin.com/in "{title}" "{location}" "open to work"'
    url = "https://html.duckduckgo.com/html/"
    r = requests.post(url, data={"q": q}, timeout=20, headers={"User-Agent":"Mozilla/5.0"})
    soup = BeautifulSoup(r.text, "html.parser")
    rows = []
    for a in soup.select("a.result__a")[:limit]:
        rows.append({
            "profile_url": a.get("href", ""),
            "title": a.get_text(" ", strip=True),
        })
    return rows

@app.get("/", response_class=HTMLResponse)
def home():
    return HTML

@app.post("/search")
def search(jd: str = Form(...), location: str = Form(...)):
    title = extract_title(jd)
    rows = search_public_profiles(title, location, limit=100)

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["profile_url", "title"])
    writer.writeheader()
    writer.writerows(rows)

    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition":"attachment; filename=public_profile_urls.csv"}
    )
