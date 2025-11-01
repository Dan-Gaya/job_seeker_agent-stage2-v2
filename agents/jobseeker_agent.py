# # agents/jobseeker_agent.py
# from typing import List, Optional, Dict, Any
# from uuid import uuid4
# from models.a2a import A2AMessage, TaskResult, TaskStatus, Artifact, MessagePart
# from services.skill_extractor import extract_keywords
# from services.jsearch_client import JSearchClient
# from datetime import datetime

# jsearch = JSearchClient()

# # simple in-memory history storage: contextId -> list[A2AMessage]
# _HISTORY_STORE: Dict[str, List[A2AMessage]] = {}

# class JobSeekerAgent:
#     def __init__(self):
#         self.jsearch = jsearch

#     async def process_messages(
#         self,
#         messages: List[A2AMessage],
#         context_id: Optional[str] = None,
#         task_id: Optional[str] = None,
#         config: Optional[dict] = None
#     ) -> TaskResult:
#         # generate ids
#         context_id = context_id or str(uuid4())
#         task_id = task_id or str(uuid4())

#         # last user message
#         user_msg = messages[-1] if messages else None
#         if not user_msg:
#             raise ValueError("No message provided")

#         # append to history store
#         history = _HISTORY_STORE.setdefault(context_id, [])
#         history.append(user_msg)

#         # prefer structured data if provided
#         user_text = ""
#         user_data = {}
#         for p in user_msg.parts:
#             if p.kind == "text" and p.text:
#                 user_text = p.text
#             if p.kind == "data" and p.data:
#                 user_data = p.data

#         if user_data:
#             keywords = user_data.get("keywords") or user_data.get("query") or user_text
#             location = user_data.get("location")
#             user_skills = user_data.get("userSkills") or []
#         else:
#             parsed = extract_keywords(user_text or "", use_semantic=True)
#             keywords = " ".join(parsed.get("keywords") or [])
#             location = parsed.get("location")
#             user_skills = []

#         if not keywords:
#             keywords = user_text or "software engineer"

#         # fetch jobs
#         try:
#             jobs = await self.jsearch.search_jobs(query=keywords, location=location, per_page=8)
#         except Exception as e:
#             # build failed TaskResult
#             fail_msg = A2AMessage(
#                 role="agent",
#                 parts=[MessagePart(kind="text", text=f"Failed to fetch jobs: {e}")],
#                 taskId=task_id
#             )
#             history.append(fail_msg)
#             status = TaskStatus(state="failed", timestamp=datetime.utcnow().isoformat() + "Z", message=fail_msg)
#             return TaskResult(id=task_id, contextId=context_id, status=status, artifacts=[], history=history)

#         # gather skills from job descriptions
#         all_skills = []
#         for j in jobs:
#             jd = j.get("job_description") or j.get("description") or ""
#             sk = extract_keywords(jd, use_semantic=True)
#             all_skills.extend(sk.get("keywords") or [])

#         from collections import Counter
#         c = Counter(all_skills)
#         top_skills = [k for k,_ in c.most_common(10)]

#         # build agent message
#         summary_text = f"Found {len(jobs)} job(s) for '{keywords}'" + (f" in {location}." if location else ".")
#         summary_text += f" Top skills: {', '.join(top_skills[:6])}."

#         agent_message = A2AMessage(
#             role="agent",
#             parts=[MessagePart(kind="text", text=summary_text)],
#             taskId=task_id
#         )
#         # append to history
#         history.append(agent_message)

#         # artifacts
#         jobs_part = MessagePart(kind="data", data={"jobs": jobs})
#         skills_part = MessagePart(kind="data", data={"top_skills": top_skills})
#         rec_text = self._build_recommendations(top_skills, user_skills)
#         rec_part = MessagePart(kind="text", text=rec_text)

#         artifacts = [
#             Artifact(name="jobs", parts=[jobs_part]),
#             Artifact(name="skills", parts=[skills_part]),
#             Artifact(name="recommendation", parts=[rec_part]),
#         ]

#         state = "input-required" if jobs and len(jobs) > 0 else "completed"
#         status = TaskStatus(state=state, timestamp=datetime.utcnow().isoformat() + "Z", message=agent_message)

#         # return TaskResult with history (list of A2AMessage)
#         return TaskResult(id=task_id, contextId=context_id, status=status, artifacts=artifacts, history=history)

#     def _build_recommendations(self, top_skills, user_skills):
#         if user_skills:
#             uset = {s.strip().lower() for s in user_skills}
#             req = {s.strip().lower() for s in top_skills}
#             missing = list(req - uset)
#             if missing:
#                 return "Recommended skills to learn: " + ", ".join(missing[:8]) + ". Resume tip: add keywords from top skills."
#         return "You match many top skills. Highlight projects and quantify outcomes."

# agents/jobseeker_agent.py
from typing import List, Optional, Dict, Any
from uuid import uuid4
from models.a2a import A2AMessage, TaskResult, TaskStatus, Artifact, MessagePart
from services.skill_extractor import extract_keywords
from services.jobseeker_service import find_jobs_and_skills
from utils.a2a_response import make_agent_message, make_artifact, make_task_result
from datetime import datetime

# in-memory history store: contextId -> list[A2AMessage]
_HISTORY_STORE: Dict[str, List[A2AMessage]] = {}

class JobSeekerAgent:
    def __init__(self):
        pass

    async def process_messages(self, messages: List[A2AMessage], context_id: Optional[str] = None, task_id: Optional[str] = None, config: Optional[dict] = None) -> TaskResult:
        context_id = context_id or str(uuid4())
        task_id = task_id or str(uuid4())

        user_msg = messages[-1] if messages else None
        if not user_msg:
            raise ValueError("No message provided")

        # ensure text parts are dicts (if incoming text is string, caller should have wrapped it)
        # append incoming to history
        history = _HISTORY_STORE.setdefault(context_id, [])
        history.append(user_msg)

        # parse structured data if provided
        user_text = ""
        user_data = {}
        for p in user_msg.parts:
            if p.kind == "text" and p.text:
                # p.text is dict per schema. look for "query" or "message"
                user_text = p.text.get("query") or p.text.get("message") or ""
            if p.kind == "data" and p.data:
                user_data = p.data

        if user_data:
            keywords = user_data.get("keywords") or user_data.get("query") or user_text
            location = user_data.get("location")
            user_skills = user_data.get("userSkills") or []
        else:
            parsed = extract_keywords(user_text or "", use_semantic=True)
            keywords = " ".join(parsed.get("keywords") or [])
            location = parsed.get("location")
            user_skills = []

        if not keywords:
            keywords = user_text or "software engineer"

        # call job service
        try:
            res = await find_jobs_and_skills(keywords, location, per_page=8)
            jobs = res["jobs"]
            top_skills = res["top_skills"]
        except Exception as e:
            # build failure A2A error via raising; controller will catch and convert to A2A error reply
            raise e

        # agent message
        summary_text = f"Found {len(jobs)} job(s) for '{keywords}'" + (f" in {location}." if location else ".")
        summary_text += f" Top skills: {', '.join(top_skills[:6])}."

        agent_msg = make_agent_message(summary_text, task_id)
        history.append(agent_msg)

        # artifacts
        jobs_art = make_artifact("jobs", "data", {"jobs": jobs})
        skills_art = make_artifact("skills", "data", {"top_skills": top_skills})
        rec_text = self._build_recommendations(top_skills, user_skills)
        rec_art = make_artifact("recommendation", "text", rec_text)

        artifacts = [jobs_art, skills_art, rec_art]

        state = "input-required" if jobs and len(jobs) > 0 else "completed"
        task_result = make_task_result(task_id, context_id, state, agent_msg, artifacts, history)
        return task_result

    def _build_recommendations(self, top_skills, user_skills):
        if user_skills:
            uset = {s.strip().lower() for s in user_skills}
            req = {s.strip().lower() for s in top_skills}
            missing = list(req - uset)
            if missing:
                return "Recommended skills to learn: " + ", ".join(missing[:8]) + ". Resume tip: add keywords from top skills."
        return "You match many top skills. Highlight projects and quantify outcomes."
