"""
FreelancerX Lead Scraper — Backend API
FastAPI + Python | Free deployment on Render.com
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
import uuid
import asyncio
import os
import logging
from datetime import datetime

from app.scrapers.google_scraper import GoogleScraper
from app.scrapers.yelp_scraper import YelpScraper
from app.scrapers.yellowpages_scraper import YellowPagesScraper
from app.utils.validator import validate_leads
from app.utils.deduplicator import deduplicate
from app.exporters.csv_exporter import export_csv
from app.exporters.xlsx_exporter import export_xlsx
from app.exporters.docx_exporter import export_docx

# ─── SETUP ──────────────────────────────────────
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("freelankarx")

app = FastAPI(
    title="FreelancerX Lead Scraper API",
    description="Professional lead generation backend",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Lock down to your GitHub Pages URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job store (resets on restart — fine for free tier)
JOBS: dict = {}
EXPORT_DIR = "/tmp/freelankarx_exports"
os.makedirs(EXPORT_DIR, exist_ok=True)


# ─── SCHEMAS ────────────────────────────────────
class ScrapeRequest(BaseModel):
    niche: str
    country: Optional[str] = ""
    location: Optional[str] = ""
    limit: int = 100
    filter_email: bool = False
    filter_website: bool = False
    filter_phone: bool = False
    include_social: bool = True
    export_format: str = "csv"  # csv | xlsx | docx | all


class ExportRequest(BaseModel):
    leads: List[dict]


class JobStatus(BaseModel):
    job_id: str
    status: str          # pending | running | done | error
    progress: float
    found: int
    step: int
    step_label: str
    leads: Optional[List[dict]] = None
    recent_leads: Optional[List[dict]] = None
    download_url: Optional[str] = None
    error: Optional[str] = None


# ─── ROUTES ─────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "service": "FreelancerX Lead Scraper", "version": "1.0.0"}


@app.post("/scrape/start")
async def start_scrape(req: ScrapeRequest, background_tasks: BackgroundTasks):
    """Start an async scrape job. Returns job_id for polling."""
    if req.limit < 1 or req.limit > 1000:
        raise HTTPException(400, "limit must be between 1 and 1000")
    if not req.niche.strip():
        raise HTTPException(400, "niche is required")

    job_id = str(uuid.uuid4())[:8]
    JOBS[job_id] = {
        "status": "pending",
        "progress": 0,
        "found": 0,
        "step": 1,
        "step_label": "Initializing...",
        "leads": [],
        "recent_leads": [],
        "download_url": None,
        "error": None
    }

    background_tasks.add_task(run_scrape_job, job_id, req)
    logger.info(f"Job {job_id} started — niche={req.niche}, limit={req.limit}")
    return {"job_id": job_id, "status": "pending"}


@app.get("/scrape/status/{job_id}", response_model=JobStatus)
async def get_status(job_id: str):
    if job_id not in JOBS:
        raise HTTPException(404, "Job not found")
    j = JOBS[job_id]
    return JobStatus(
        job_id=job_id,
        status=j["status"],
        progress=j["progress"],
        found=j["found"],
        step=j["step"],
        step_label=j["step_label"],
        leads=j["leads"] if j["status"] == "done" else None,
        recent_leads=j["recent_leads"][-20:],
        download_url=j["download_url"],
        error=j["error"]
    )


@app.post("/export/xlsx")
async def export_xlsx_endpoint(req: ExportRequest):
    path = export_xlsx(req.leads, EXPORT_DIR)
    return FileResponse(path, filename=os.path.basename(path), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@app.post("/export/docx")
async def export_docx_endpoint(req: ExportRequest):
    path = export_docx(req.leads, EXPORT_DIR)
    return FileResponse(path, filename=os.path.basename(path), media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")


@app.get("/export/download/{filename}")
async def download_file(filename: str):
    path = os.path.join(EXPORT_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(404, "File not found")
    return FileResponse(path, filename=filename)


# ─── CORE SCRAPE JOB ────────────────────────────

async def run_scrape_job(job_id: str, req: ScrapeRequest):
    """Main background scrape task."""
    j = JOBS[job_id]
    try:
        j["status"] = "running"

        # Step 1 — Initialize
        j["step"] = 1
        j["step_label"] = "Initializing scraper"
        j["progress"] = 5
        await asyncio.sleep(0.5)

        # Step 2 — Search multiple sources
        j["step"] = 2
        j["step_label"] = "Searching directories"
        j["progress"] = 15

        scrapers = [
            GoogleScraper(),
            YelpScraper(),
            YellowPagesScraper(),
        ]

        raw_leads = []
        per_source = max(req.limit // len(scrapers) + 10, 20)

        for i, scraper in enumerate(scrapers):
            j["step_label"] = f"Scanning {scraper.name}..."
            j["progress"] = 15 + (i * 20)
            try:
                results = await scraper.scrape(
                    niche=req.niche,
                    country=req.country,
                    location=req.location,
                    limit=per_source,
                    include_social=req.include_social
                )
                raw_leads.extend(results)
                j["found"] = len(raw_leads)

                for lead in results:
                    j["recent_leads"].append(lead)
                    if len(j["recent_leads"]) > 100:
                        j["recent_leads"] = j["recent_leads"][-100:]

                logger.info(f"[{job_id}] {scraper.name}: {len(results)} leads")
            except Exception as e:
                logger.warning(f"[{job_id}] {scraper.name} failed: {e}")

        # Step 3 — Extract / enrich
        j["step"] = 3
        j["step_label"] = "Extracting contact details"
        j["progress"] = 60
        await asyncio.sleep(0.3)

        # Step 4 — Validate emails
        j["step"] = 4
        j["step_label"] = "Validating emails"
        j["progress"] = 70
        validated = validate_leads(raw_leads)
        logger.info(f"[{job_id}] Validated: {len(validated)} / {len(raw_leads)}")

        # Step 5 — Deduplicate
        j["step"] = 5
        j["step_label"] = "Removing duplicates"
        j["progress"] = 80
        unique_leads = deduplicate(validated)
        logger.info(f"[{job_id}] After dedup: {len(unique_leads)}")

        # Apply filters
        filtered = unique_leads
        if req.filter_email:
            filtered = [l for l in filtered if l.get("email")]
        if req.filter_website:
            filtered = [l for l in filtered if l.get("website")]
        if req.filter_phone:
            filtered = [l for l in filtered if l.get("phone")]

        # Trim to requested limit
        final = filtered[:req.limit]
        logger.info(f"[{job_id}] Final leads: {len(final)}")

        # Step 6 — Export
        j["step"] = 6
        j["step_label"] = "Exporting file"
        j["progress"] = 90

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_niche = req.niche.replace(" ", "_").lower()[:20]
        download_url = None

        fmt = req.export_format
        try:
            if fmt == "csv" or fmt == "all":
                path = export_csv(final, EXPORT_DIR, f"{safe_niche}_{ts}.csv")
                download_url = f"/export/download/{os.path.basename(path)}"
            if fmt == "xlsx" or fmt == "all":
                path = export_xlsx(final, EXPORT_DIR, f"{safe_niche}_{ts}.xlsx")
                if not download_url:
                    download_url = f"/export/download/{os.path.basename(path)}"
            if fmt == "docx" or fmt == "all":
                path = export_docx(final, EXPORT_DIR, f"{safe_niche}_{ts}.docx")
                if not download_url:
                    download_url = f"/export/download/{os.path.basename(path)}"
        except Exception as e:
            logger.warning(f"[{job_id}] Export error: {e}")

        j["leads"] = final
        j["found"] = len(final)
        j["progress"] = 100
        j["step"] = 6
        j["step_label"] = f"Done — {len(final)} leads exported"
        j["download_url"] = download_url
        j["status"] = "done"
        logger.info(f"[{job_id}] COMPLETE — {len(final)} leads")

    except Exception as e:
        j["status"] = "error"
        j["error"] = str(e)
        j["step_label"] = "Error occurred"
        logger.error(f"[{job_id}] ERROR: {e}", exc_info=True)
