# # services/jobseeker_service.py
# from typing import List, Optional
# from models.a2a import A2AMessage, TaskResult, TaskStatus, Artifact, MessagePart
# from services.skill_extractor import extract_keywords
# from services.jsearch_client import JSearchClient
# from uuid import uuid4

# jsearch = JSearchClient()

# async def handle_search_message(message: A2AMessage, context_id: Optional[str] = None, task_id: Optional[str] = None) -> TaskResult:
#     context_id = context_id or str(uuid4())
#     task_id = task_id or str(uuid4())

#     # take last text part or data part
#     user_text = ""
#     user_data = {}
#     for p in message.parts:
#         if p.kind == "text" and p.text:
#             user_text = p.text
#         if p.kind == "data" and p.data:
#             user_data = p.data

#     # If structured data provided, prefer it
#     if user_data:
#         keywords = user_data.get("keywords") or user_data.get("query") or ""
#         location = user_data.get("location")
#         user_skills = user_data.get("userSkills") or []
#     else:
#         parsed = extract_keywords(user_text or "", use_semantic=True)
#         keywords = " ".join(parsed.get("keywords") or [])
#         location = parsed.get("location")
#         user_skills = []

#     if not keywords:
#         keywords = user_text or "software engineer"

#     # fetch jobs
#     try:
#         jobs = await jsearch.search_jobs(query=keywords, location=location, per_page=8)
#     except Exception as e:
#         response_message = A2AMessage(
#             role="agent",
#             parts=[MessagePart(kind="text", text=f"Failed to fetch jobs: {e}")],
#             taskId=task_id
#         )
#         return TaskResult(
#             id=task_id,
#             contextId=context_id,
#             status=TaskStatus(state="failed", message=response_message),
#             artifacts=[],
#             history=[message, response_message]
#         )

#     # aggregate skills across job descriptions (simple: extract keywords per jd)
#     all_skills = []
#     for j in jobs:
#         jd = j.get("job_description") or j.get("description") or ""
#         sk = extract_keywords(jd, use_semantic=True)
#         all_skills.extend(sk.get("keywords") or [])

#     # top skills (simple frequency)
#     from collections import Counter
#     c = Counter(all_skills)
#     top_skills = [k for k,_ in c.most_common(10)]

#     # compare with user skills if provided
#     matched = []
#     missing = []
#     if user_skills:
#         uset = {s.strip().lower() for s in user_skills}
#         req = {s.strip().lower() for s in top_skills}
#         matched = list(req & uset)
#         missing = list(req - uset)

#     # build response message
#     summary = f"Found {len(jobs)} job(s) for '{keywords}'" + (f" in {location}." if location else ".")
#     summary += f" Top skills: {', '.join(top_skills[:6])}."
#     if user_skills:
#         summary += f" You match {len(matched)} skills; missing {len(missing)}."

#     response_message = A2AMessage(
#         role="agent",
#         parts=[MessagePart(kind="text", text=summary)],
#         taskId=task_id
#     )

#     # Artifacts
#     jobs_part = MessagePart(kind="data", data={"jobs": jobs})
#     skills_part = MessagePart(kind="data", data={"top_skills": top_skills})
#     recommendation_text = _build_recommendation_text(top_skills, matched, missing)
#     rec_part = MessagePart(kind="text", text=recommendation_text)

#     artifacts = [
#         Artifact(name="jobs", parts=[jobs_part]),
#         Artifact(name="skills", parts=[skills_part]),
#         Artifact(name="recommendation", parts=[rec_part]),
#     ]

#     state = "input-required" if jobs and len(jobs) > 0 else "completed"

#     return TaskResult(
#         id=task_id,
#         contextId=context_id,
#         status=TaskStatus(state=state, message=response_message),
#         artifacts=artifacts,
#         history=[message, response_message]
#     )

# def _build_recommendation_text(top_skills, matched, missing):
#     parts = []
#     if missing:
#         parts.append("Recommended skills to learn: " + ", ".join(missing[:8]) + ".")
#         parts.append("Resume tips: add relevant keywords to your summary and quantify achievements.")
#     else:
#         parts.append("You match many top skills. Highlight projects using these skills and add measurable results.")
#     return " ".join(parts)

# services/job_service.py
from typing import List, Dict, Any, Optional
from services.jsearch_client import JSearchClient

jsearch = JSearchClient()

async def find_jobs_and_skills(query: str, location: Optional[str] = None, per_page: int = 8) -> Dict[str, Any]:
    """
    Returns dict: {"jobs": [...], "top_skills": [...]}.
    Normalizes jobs and extracts frequent keywords via simple heuristics.
    """
    jobs = await jsearch.search_jobs(query=query, location=location, per_page=per_page)
    # Extract keywords from job_description via simple heuristics (word freq)
    all_texts = [j.get("job_description","") for j in jobs]
    tokens = []
    import re
    for t in all_texts:
        tokens.extend(re.findall(r"[A-Za-z\+\-\.#]{2,}", t.lower()))
    # naive stopwords
    stop = set(["the","and","with","for","our","we","you","is","in","on","to","a","an"])
    freq = {}
    for tk in tokens:
        if tk in stop: continue
        freq[tk] = freq.get(tk,0)+1
    # choose some known skills or most frequent tokens
    common_ordered = sorted(freq.items(), key=lambda x:-x[1])
    top_skills = [k for k,_ in common_ordered[:10]]
    return {"jobs": jobs, "top_skills": top_skills}
