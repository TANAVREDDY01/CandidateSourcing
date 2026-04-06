
from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import HTMLResponse, StreamingResponse
import io, re, csv

app = FastAPI()

HTML = '''
<html><body style="font-family:Arial;padding:30px">
<h2>Open-to-Work Candidate Finder</h2>
<form action="/search" method="post">
  <textarea name="jd" rows="10" cols="80" placeholder="Paste Job Description"></textarea><br><br>
  <input name="location" placeholder="Location (e.g. Hyderabad)" />
  <button type="submit">Find Candidates</button>
</form>
</body></html>
'''

SAMPLE_POOL = [
    {"name":"Rahul Sharma","title":"Data Analyst","exp":"3 years","location":"Hyderabad","status":"Open to Work","skills":"SQL, Power BI"},
    {"name":"Priya Reddy","title":"BI Analyst","exp":"2 years","location":"Hyderabad","status":"Open to Work","skills":"Excel, SQL, Power BI"},
    {"name":"Aman Verma","title":"Data Analyst","exp":"4 years","location":"Bengaluru","status":"Open to Work","skills":"Python, SQL"},
]

def extract_title(jd):
    m = re.search(r'(Data Analyst|BI Analyst|Business Analyst|Python Developer)', jd, re.I)
    return m.group(1) if m else "Data Analyst"

def extract_experience(jd):
    m = re.search(r'(\d+)\+?\s*years', jd, re.I)
    return int(m.group(1)) if m else 0

@app.get("/", response_class=HTMLResponse)
def home():
    return HTML

@app.post("/search")
def search(jd: str = Form(...), location: str = Form(...)):
    title = extract_title(jd)
    min_exp = extract_experience(jd)
    results = []
    for i in range(1, 501):
        c = SAMPLE_POOL[i % len(SAMPLE_POOL)].copy()
        if title.lower() in c["title"].lower() and location.lower() in c["location"].lower():
            years = int(c["exp"].split()[0])
            if years >= min_exp:
                c["linkedin_url"] = f"https://linkedin.com/in/sample-candidate-{i}"
                results.append(c)
        if len(results) >= 500:
            break

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=results[0].keys() if results else ["name"])
    writer.writeheader()
    for row in results:
        writer.writerow(row)

    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition":"attachment; filename=candidates.csv"}
    )
