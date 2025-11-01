# # services/jsearch_client.py
# import os
# from typing import List, Dict, Any, Optional
# import httpx

# JSEARCH_BASE = os.getenv("JSEARCH_BASE_URL", "https://jsearch.p.rapidapi.com/search")
# JSEARCH_KEY = os.getenv("JSEARCH_API_KEY")
# JSEARCH_HOST = os.getenv("JSEARCH_HOST", "jsearch.p.rapidapi.com")

# class JSearchClient:
#     def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
#         self.api_key = api_key or JSEARCH_KEY
#         self.base_url = base_url or JSEARCH_BASE

#     async def search_jobs(self, query: str, location: Optional[str] = None, per_page: int = 8) -> List[Dict[str, Any]]:
#         if not self.api_key:
#             return self._mock_jobs(query, location, per_page)

#         headers = {
#             "X-RapidAPI-Key": self.api_key,
#             "X-RapidAPI-Host": JSEARCH_HOST
#         }
#         params = {"query": query, "num_pages": 1, "page": 1, "size": per_page}
#         if location:
#             params["location"] = location

#         async with httpx.AsyncClient(timeout=15.0) as client:
#             resp = await client.get(self.base_url, params=params, headers=headers)
#             resp.raise_for_status()
#             data = resp.json()
#             jobs = data.get("data") or data.get("jobs") or []
#             return jobs

#     def _mock_jobs(self, query: str, location: Optional[str], per_page: int):
#         return [
#             {
#                 "job_id": f"mock-{i}",
#                 "job_title": f"{query.title()} Engineer {i}",
#                 "employer_name": "Acme Corp",
#                 "job_city": location or "Remote",
#                 "job_country": "Anywhere",
#                 "job_description": (
#                     f"We are seeking a {query} engineer with experience in Python, SQL, Docker, "
#                     "and CI/CD. Familiarity with AWS or GCP is a plus."
#                 ),
#                 "job_apply_link": f"https://jobs.example.com/{query}-{i}"
#             }
#             for i in range(1, per_page + 1)
#         ]

# services/jsearch_client.py
import os
from typing import List, Dict, Any, Optional
import httpx

JSEARCH_BASE = os.getenv("JSEARCH_BASE_URL", "https://jsearch.p.rapidapi.com/search")
JSEARCH_KEY = os.getenv("JSEARCH_API_KEY")
JSEARCH_HOST = os.getenv("JSEARCH_HOST", "jsearch.p.rapidapi.com")

class JSearchClient:
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or JSEARCH_KEY
        self.base_url = base_url or JSEARCH_BASE

    async def search_jobs(self, query: str, location: Optional[str] = None, per_page: int = 8) -> List[Dict[str, Any]]:
        if not self.api_key:
            return self._mock_jobs(query, location, per_page)

        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": JSEARCH_HOST
        }
        params = {"query": query, "num_pages": 1, "page": 1, "size": per_page}
        if location:
            params["location"] = location

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(self.base_url, params=params, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            jobs_raw = data.get("data") or data.get("jobs") or []
            return [self._normalize_job(j) for j in jobs_raw]

    def _normalize_job(self, j: Dict[str, Any]) -> Dict[str, Any]:
        # defensive mapping; handle different provider shapes
        return {
            "job_id": j.get("job_id") or j.get("id") or j.get("jobId") or str(j.get("id", "")),
            "job_title": j.get("title") or j.get("job_title") or j.get("position") or j.get("jobTitle"),
            "employer_name": j.get("employer_name") or j.get("company_name") or j.get("company"),
            "job_city": j.get("job_city") or j.get("city") or j.get("location"),
            "job_country": j.get("job_country") or j.get("country"),
            "job_description": j.get("description") or j.get("job_description") or j.get("job_purpose") or "",
            "job_apply_link": j.get("url") or j.get("job_apply_link") or j.get("apply_link") or j.get("apply_url")
        }

    def _mock_jobs(self, query: str, location: Optional[str], per_page: int):
        return [
            {
                "job_id": f"mock-{i}",
                "job_title": f"{query.title()} Engineer {i}",
                "employer_name": "Acme Corp",
                "job_city": location or "Remote",
                "job_country": "Anywhere",
                "job_description": (
                    f"We are seeking a {query} engineer with experience in Python, SQL, Docker, "
                    "and CI/CD. Familiarity with AWS or GCP is a plus."
                ),
                "job_apply_link": f"https://jobs.example.com/{query}-{i}"
            }
            for i in range(1, per_page + 1)
        ]
