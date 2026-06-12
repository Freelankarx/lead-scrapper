# 🎯 FreelancerX Lead Scraper

> **Fully free lead generation platform** — beautiful dark navy/gold frontend on GitHub Pages + Python backend on Render.com. Generate up to 1,000 business leads per scrape across any niche and country.

---

## 🚀 Quick Deploy (100% Free, No Credit Card)

### Step 1 — Fork & Push to GitHub

1. Create a new GitHub repo named `freelankarx` (or anything you like)
2. Upload **all files** from this project into the repo:
   - `frontend/` → index.html, style.css, script.js
   - `backend/` → all Python files
   - `.github/workflows/deploy.yml`

```bash
git init
git add .
git commit -m "🎯 FreelancerX Lead Scraper"
git remote add origin https://github.com/YOUR_USERNAME/freelankarx.git
git push -u origin main
```

---

### Step 2 — Enable GitHub Pages (frontend)

1. Go to your repo → **Settings** → **Pages**
2. Under **Source**, select **GitHub Actions**
3. The workflow will auto-deploy your frontend
4. Your site will be live at: `https://YOUR_USERNAME.github.io/freelankarx`

That's it for the frontend! ✅

---

### Step 3 — Deploy Backend FREE on Render.com

1. Go to **https://render.com** → Sign up free (use GitHub login)
2. Click **New → Web Service**
3. Connect your GitHub repo
4. Set **Root Directory** to `backend`
5. Render auto-detects the `render.yaml` config
6. Click **Deploy**
7. Your API will be live at: `https://freelankarx-api.onrender.com`

**Note:** Render free tier spins down after 15 mins of inactivity. First request after sleep takes ~30 seconds. This is normal and free.

---

### Step 4 — Connect Frontend to Backend

1. Open your live site at `https://YOUR_USERNAME.github.io/freelankarx`
2. Scroll down to the **Docs** section
3. Enter your Render URL: `https://freelankarx-api.onrender.com`
4. Click **Test** — you should see "✓ Connected!"
5. The URL is saved in your browser. You only do this once!

---

## ✅ Using the Scraper

1. Enter a **Niche** (e.g. "digital marketing agency", "plumber", "dentist")
2. Select a **Country** and optional **City/State**
3. Set how many **leads** you want (up to 1,000)
4. Choose filters:
   - ✅ Only with Email
   - Website / Phone filters
5. Pick export format: **CSV / Excel / DOCX / All**
6. Click **🚀 Launch Scraper**
7. Watch live progress — leads appear in the table
8. Click **Download** to save your file

---

## 📁 Project Structure

```
freelankarx/
├── .github/
│   └── workflows/
│       └── deploy.yml          ← Auto-deploys frontend to GitHub Pages
│
├── frontend/
│   ├── index.html              ← Main UI (dark navy + gold theme)
│   ├── style.css               ← All styles
│   └── script.js               ← Scraper logic, polling, table, download
│
└── backend/
    ├── main.py                 ← FastAPI app, job queue, routes
    ├── requirements.txt        ← Python dependencies
    ├── render.yaml             ← Render.com free deployment config
    └── app/
        ├── scrapers/
        │   ├── google_scraper.py       ← Google search scraper
        │   ├── yelp_scraper.py         ← Yelp business scraper
        │   └── yellowpages_scraper.py  ← Yellow Pages scraper
        ├── utils/
        │   ├── contact_extractor.py    ← Email/phone/social extraction
        │   ├── validator.py            ← Email validation & data cleaning
        │   └── deduplicator.py         ← Remove duplicate leads
        └── exporters/
            ├── csv_exporter.py         ← CSV export
            ├── xlsx_exporter.py        ← Excel export (formatted)
            └── docx_exporter.py        ← Word document export
```

---

## 🔧 Local Development

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Then open `frontend/index.html` in your browser and set API URL to `http://localhost:8000`.

---

## 📊 Lead Data Fields

| Field | Description |
|-------|-------------|
| Business Name | Company/business name |
| Owner Name | Extracted from page when available |
| Email | Validated email address |
| Phone | Normalized phone number |
| Website | Business website URL |
| Address | Street address |
| City | City |
| State | State/Province |
| Country | Country |
| Facebook | Facebook profile URL |
| Instagram | Instagram profile URL |
| LinkedIn | LinkedIn company URL |
| Twitter | Twitter/X profile URL |
| Source | Data source (Google/Yelp/YP) |

---

## ⚠️ Legal & Ethical Use

- Only scrape publicly available business information
- Respect robots.txt and rate limits
- Use leads for legitimate business outreach only
- Don't spam — build real relationships

---

## 🆓 100% Free Stack

| Component | Service | Cost |
|-----------|---------|------|
| Frontend | GitHub Pages | Free |
| Backend | Render.com | Free |
| Database | None needed | Free |
| Domain | github.io subdomain | Free |

---

Built with ❤️ by FreelancerX
