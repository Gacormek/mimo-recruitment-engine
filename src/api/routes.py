"""API routes for MiMo Recruitment Engine."""
import json
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
from ..database import execute_query, execute_write
from ..kernel import AgentKernel

router = APIRouter()

# Kernel is set by main.py
kernel: AgentKernel = None


def set_kernel(k: AgentKernel):
    global kernel
    kernel = k


# ─── Candidates ────────────────────────────────────────────────────
@router.get("/api/candidates")
async def list_candidates():
    rows = await execute_query("SELECT * FROM candidates ORDER BY created_at DESC")
    return {"candidates": rows}


@router.post("/api/candidates")
async def create_candidate(
    name: str = Form(...),
    email: str = Form(""),
    phone: str = Form(""),
    resume_text: str = Form(""),
    resume_file: Optional[UploadFile] = File(None),
):
    text = resume_text
    path = ""
    if resume_file:
        content = await resume_file.read()
        path = f"data/uploads/{resume_file.filename}"
        import os
        os.makedirs("data/uploads", exist_ok=True)
        with open(path, "wb") as f:
            f.write(content)
        if resume_file.filename.endswith(".pdf"):
            try:
                from PyPDF2 import PdfReader
                import io
                reader = PdfReader(io.BytesIO(content))
                text = "\n".join(p.extract_text() or "" for p in reader.pages)
            except Exception:
                pass
        elif resume_file.filename.endswith(".txt"):
            text = content.decode("utf-8", errors="replace")

    # Parse with agent if we have text
    skills_json = "[]"
    exp_years = 0
    edu_json = "[]"
    if text and kernel:
        result = await kernel.execute("ParseAgent", resume_text=text)
        if result.get("status") == "success" and result.get("data", {}).get("data"):
            parsed = result["data"]["data"]
            skills_json = json.dumps(parsed.get("skills", []))
            exp_years = parsed.get("experience_years", 0)
            edu_json = json.dumps(parsed.get("education", []))
            if not name or name == "auto":
                name = parsed.get("name", name)
            if not email:
                email = parsed.get("email", "")

    cid = await execute_write(
        "INSERT INTO candidates (name, email, phone, resume_text, resume_path, skills, experience_years, education) VALUES (?,?,?,?,?,?,?,?)",
        (name, email, phone, text, path, skills_json, exp_years, edu_json),
    )
    return {"id": cid, "name": name, "status": "created"}


@router.get("/api/candidates/{candidate_id}")
async def get_candidate(candidate_id: int):
    rows = await execute_query("SELECT * FROM candidates WHERE id=?", (candidate_id,))
    if not rows:
        raise HTTPException(404, "Candidate not found")
    return rows[0]


@router.delete("/api/candidates/{candidate_id}")
async def delete_candidate(candidate_id: int):
    await execute_write("DELETE FROM candidates WHERE id=?", (candidate_id,))
    return {"status": "deleted"}


# ─── Jobs ──────────────────────────────────────────────────────────
@router.get("/api/jobs")
async def list_jobs():
    rows = await execute_query("SELECT * FROM jobs ORDER BY created_at DESC")
    return {"jobs": rows}


@router.post("/api/jobs")
async def create_job(data: dict):
    jid = await execute_write(
        "INSERT INTO jobs (title, company, description, required_skills, preferred_skills, min_experience, education_requirement, salary_range) VALUES (?,?,?,?,?,?,?,?)",
        (
            data.get("title", ""),
            data.get("company", ""),
            data.get("description", ""),
            json.dumps(data.get("required_skills", [])),
            json.dumps(data.get("preferred_skills", [])),
            data.get("min_experience", 0),
            data.get("education_requirement", ""),
            data.get("salary_range", ""),
        ),
    )
    return {"id": jid, "status": "created"}


@router.get("/api/jobs/{job_id}")
async def get_job(job_id: int):
    rows = await execute_query("SELECT * FROM jobs WHERE id=?", (job_id,))
    if not rows:
        raise HTTPException(404, "Job not found")
    return rows[0]


@router.delete("/api/jobs/{job_id}")
async def delete_job(job_id: int):
    await execute_write("DELETE FROM jobs WHERE id=?", (job_id,))
    return {"status": "deleted"}


# ─── Pipeline: Match ──────────────────────────────────────────────
@router.post("/api/match")
async def match_candidate(data: dict):
    """Match a candidate to a job."""
    cid = data.get("candidate_id")
    jid = data.get("job_id")
    cands = await execute_query("SELECT * FROM candidates WHERE id=?", (cid,))
    jobs = await execute_query("SELECT * FROM jobs WHERE id=?", (jid,))
    if not cands or not jobs:
        raise HTTPException(404, "Candidate or job not found")

    cand = cands[0]
    job = jobs[0]
    cand["skills"] = json.loads(cand.get("skills", "[]") or "[]")
    cand["education"] = json.loads(cand.get("education", "[]") or "[]")
    job["required_skills"] = json.loads(job.get("required_skills", "[]") or "[]")
    job["preferred_skills"] = json.loads(job.get("preferred_skills", "[]") or "[]")

    result = await kernel.execute("MatchAgent", candidate=cand, job=job)
    if result.get("status") != "success":
        raise HTTPException(500, result.get("error", "Match failed"))

    md = result["data"]["data"]
    mid = await execute_write(
        "INSERT INTO matches (candidate_id, job_id, skill_overlap_score, experience_fit_score, overall_match_score, match_details) VALUES (?,?,?,?,?,?)",
        (cid, jid, md.get("skill_overlap_score", 0), md.get("experience_fit_score", 0), md.get("overall_match_score", 0), json.dumps(md)),
    )
    return {"id": mid, "match": md}


# ─── Pipeline: Score ──────────────────────────────────────────────
@router.post("/api/score")
async def score_candidate(data: dict):
    cid = data.get("candidate_id")
    jid = data.get("job_id")
    cands = await execute_query("SELECT * FROM candidates WHERE id=?", (cid,))
    jobs = await execute_query("SELECT * FROM jobs WHERE id=?", (jid,))
    if not cands or not jobs:
        raise HTTPException(404, "Candidate or job not found")

    cand = cands[0]
    job = jobs[0]
    cand["skills"] = json.loads(cand.get("skills", "[]") or "[]")
    cand["education"] = json.loads(cand.get("education", "[]") or "[]")
    job["required_skills"] = json.loads(job.get("required_skills", "[]") or "[]")

    result = await kernel.execute("ScoreAgent", candidate=cand, job=job)
    if result.get("status") != "success":
        raise HTTPException(500, result.get("error", "Score failed"))

    sd = result["data"]["data"]
    sid = await execute_write(
        "INSERT INTO scores (candidate_id, job_id, technical_score, experience_score, education_score, cultural_fit_score, overall_score, scoring_rationale) VALUES (?,?,?,?,?,?,?,?)",
        (cid, jid, sd.get("technical_score", 0), sd.get("experience_score", 0), sd.get("education_score", 0), sd.get("cultural_fit_score", 0), sd.get("overall_score", 0), sd.get("rationale", "")),
    )
    return {"id": sid, "scores": sd}


# ─── Pipeline: Questions ──────────────────────────────────────────
@router.post("/api/questions/generate")
async def generate_questions(data: dict):
    jid = data.get("job_id")
    count = data.get("count", 10)
    jobs = await execute_query("SELECT * FROM jobs WHERE id=?", (jid,))
    if not jobs:
        raise HTTPException(404, "Job not found")

    job = jobs[0]
    job["required_skills"] = json.loads(job.get("required_skills", "[]") or "[]")
    job["preferred_skills"] = json.loads(job.get("preferred_skills", "[]") or "[]")

    result = await kernel.execute("QuestionAgent", job=job, count=count)
    if result.get("status") != "success":
        raise HTTPException(500, result.get("error", "Question generation failed"))

    questions = result["data"]["data"].get("questions", [])
    saved = []
    for q in questions:
        qid = await execute_write(
            "INSERT INTO questions (job_id, category, question_text, expected_answer, difficulty) VALUES (?,?,?,?,?)",
            (jid, q.get("category", ""), q.get("question_text", ""), q.get("expected_answer", ""), q.get("difficulty", "medium")),
        )
        saved.append({"id": qid, **q})
    return {"questions": saved, "count": len(saved)}


@router.get("/api/questions/{job_id}")
async def list_questions(job_id: int):
    rows = await execute_query("SELECT * FROM questions WHERE job_id=? ORDER BY created_at DESC", (job_id,))
    return {"questions": rows}


# ─── Pipeline: Evaluate ──────────────────────────────────────────
@router.post("/api/evaluate")
async def evaluate_answer(data: dict):
    qid = data.get("question_id")
    answer = data.get("answer", "")
    cid = data.get("candidate_id")
    qs = await execute_query("SELECT * FROM questions WHERE id=?", (qid,))
    if not qs:
        raise HTTPException(404, "Question not found")

    result = await kernel.execute("EvaluateAgent", question=qs[0], answer=answer)
    if result.get("status") != "success":
        raise HTTPException(500, result.get("error", "Evaluation failed"))

    ed = result["data"]["data"]
    eid = await execute_write(
        "INSERT INTO evaluations (candidate_id, question_id, answer_text, score, feedback) VALUES (?,?,?,?,?)",
        (cid, qid, answer, ed.get("score", 0), ed.get("feedback", "")),
    )
    return {"id": eid, "evaluation": ed}


# ─── Pipeline: Compare ────────────────────────────────────────────
@router.post("/api/compare")
async def compare_candidates(data: dict):
    jid = data.get("job_id")
    candidate_ids = data.get("candidate_ids", [])
    if len(candidate_ids) < 2:
        raise HTTPException(400, "Need at least 2 candidates")

    jobs = await execute_query("SELECT * FROM jobs WHERE id=?", (jid,))
    if not jobs:
        raise HTTPException(404, "Job not found")

    job = jobs[0]
    job["required_skills"] = json.loads(job.get("required_skills", "[]") or "[]")

    candidates = []
    for cid in candidate_ids:
        rows = await execute_query("SELECT * FROM candidates WHERE id=?", (cid,))
        if rows:
            c = rows[0]
            c["skills"] = json.loads(c.get("skills", "[]") or "[]")
            c["education"] = json.loads(c.get("education", "[]") or "[]")
            # Attach score if available
            scores = await execute_query("SELECT overall_score FROM scores WHERE candidate_id=? AND job_id=? ORDER BY created_at DESC LIMIT 1", (cid, jid))
            c["overall_score"] = scores[0]["overall_score"] if scores else "N/A"
            candidates.append(c)

    result = await kernel.execute("CompareAgent", candidates=candidates, job=job)
    if result.get("status") != "success":
        raise HTTPException(500, result.get("error", "Comparison failed"))

    cd = result["data"]["data"]
    comp_id = await execute_write(
        "INSERT INTO comparisons (job_id, candidate_ids, ranking, comparison_matrix, summary) VALUES (?,?,?,?,?)",
        (jid, json.dumps(candidate_ids), json.dumps(cd.get("ranking", [])), json.dumps(cd), cd.get("summary", "")),
    )
    return {"id": comp_id, "comparison": cd}


# ─── Pipeline: Report ─────────────────────────────────────────────
@router.post("/api/reports/generate")
async def generate_report(data: dict):
    jid = data.get("job_id")
    jobs = await execute_query("SELECT * FROM jobs WHERE id=?", (jid,))
    if not jobs:
        raise HTTPException(404, "Job not found")

    job = jobs[0]
    job["required_skills"] = json.loads(job.get("required_skills", "[]") or "[]")

    # Get all candidates matched/scored for this job
    scored = await execute_query(
        "SELECT c.*, s.overall_score FROM candidates c JOIN scores s ON c.id = s.candidate_id WHERE s.job_id=? ORDER BY s.overall_score DESC",
        (jid,),
    )
    if not scored:
        raise HTTPException(400, "No scored candidates for this job")

    for c in scored:
        c["skills"] = json.loads(c.get("skills", "[]") or "[]")
        c["education"] = json.loads(c.get("education", "[]") or "[]")

    # Get comparison if available
    comps = await execute_query("SELECT * FROM comparisons WHERE job_id=? ORDER BY created_at DESC LIMIT 1", (jid,))
    comparison = json.loads(comps[0]["comparison_matrix"]) if comps else None

    result = await kernel.execute("ReportAgent", job=job, candidates=scored, comparison=comparison)
    if result.get("status") != "success":
        raise HTTPException(500, result.get("error", "Report generation failed"))

    rd = result["data"]["data"]
    top = scored[0]["id"] if scored else None
    rid = await execute_write(
        "INSERT INTO reports (job_id, report_type, content, top_candidate_id) VALUES (?,?,?,?)",
        (jid, "hiring_recommendation", json.dumps(rd), top),
    )
    return {"id": rid, "report": rd}


@router.get("/api/reports")
async def list_reports():
    rows = await execute_query("SELECT * FROM reports ORDER BY created_at DESC")
    return {"reports": rows}


@router.get("/api/reports/{report_id}")
async def get_report(report_id: int):
    rows = await execute_query("SELECT * FROM reports WHERE id=?", (report_id,))
    if not rows:
        raise HTTPException(404, "Report not found")
    return rows[0]


# ─── Scores List ──────────────────────────────────────────────────
@router.get("/api/scores/{job_id}")
async def list_scores(job_id: int):
    rows = await execute_query(
        "SELECT s.*, c.name as candidate_name FROM scores s JOIN candidates c ON c.id = s.candidate_id WHERE s.job_id=? ORDER BY s.overall_score DESC",
        (job_id,),
    )
    return {"scores": rows}


# ─── System ────────────────────────────────────────────────────────
@router.get("/api/status")
async def get_status():
    return kernel.get_status() if kernel else {"error": "Kernel not initialized"}
