
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, StreamingResponse
import requests, re, io, csv, time
from bs4 import BeautifulSoup
from urllib.parse import quote

app = FastAPI()

HTML = """
<html><body style="font-family:Arial;padding:30px">
<h2>500 Public LinkedIn URL Crawler</h2>
<form action="/search" method="post">
<textarea name="jd" rows="10" cols="80" placeholder="Paste Job Description"></textarea><br><br>
<input name="location" placeholder="Location (e.g. Hyderabad)" />
<input name="limit" value="500" />
<button type="submit">Find Profiles</button>
</form>
</body></html>
"""

def extract_titles(jd: str):
    base = []
    patterns = ["Data Analyst","BI Analyst","Business Analyst","Power BI Developer","SQL Analyst","Python Developer"]
    for p in patterns:
        if re.search(p, jd, re.I):
            base.append(p)
    return base or ["Data Analyst","BI Analyst","Business Analyst"]

def location_variants(loc: str):
    loc = loc.strip()
    return list(dict.fromkeys([loc, f"{loc} Telangana", f"{loc} India"]))

def ddg_search(query, max_pages=5):
    results=[]
    url="https://html.duckduckgo.com/html/"
    headers={"User-Agent":"Mozilla/5.0"}
    for _ in range(max_pages):
        r=requests.post(url, data={"q":query}, headers=headers, timeout=20)
        soup=BeautifulSoup(r.text,"html.parser")
        links=soup.select("a.result__a")
        if not links:
            break
        for a in links:
            href=a.get("href","")
            title=a.get_text(" ", strip=True)
            if "linkedin.com/in" in href:
                results.append({"profile_url":href, "result_title":title, "query":query})
        time.sleep(1)
        break
    return results

@app.get("/", response_class=HTMLResponse)
def home():
    return HTML

@app.post("/search")
def search(jd: str = Form(...), location: str = Form(...), limit: int = Form(500)):
    rows=[]
    seen=set()
    for title in extract_titles(jd):
        for loc in location_variants(location):
            q=f'site:linkedin.com/in "{title}" "{loc}"'
            for row in ddg_search(q, max_pages=5):
                if row["profile_url"] not in seen:
                    seen.add(row["profile_url"])
                    rows.append(row)
                if len(rows) >= limit:
                    break
            if len(rows) >= limit:
                break
        if len(rows) >= limit:
            break

    output=io.StringIO()
    writer=csv.DictWriter(output, fieldnames=["profile_url","result_title","query"])
    writer.writeheader()
    writer.writerows(rows)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition":"attachment; filename=linkedin_public_urls.csv"}
    )
