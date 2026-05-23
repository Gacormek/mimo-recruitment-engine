"""ReportAgent — generate hiring recommendation reports."""
import json
from datetime import datetime
from .base_agent import BaseAgent
from ..mimo.client import mimo_chat


class ReportAgent(BaseAgent):
    """Generates comprehensive hiring recommendation reports."""

    async def run(self, job: dict = None, candidates: list = None, comparison: dict = None, **kwargs) -> dict:
        """Generate a hiring recommendation report."""
        if not job or not candidates:
            return self._err("Job and candidate data required")

        candidate_data = []
        for c in candidates:
            candidate_data.append(
                f"- {c.get('name', 'N/A')}: Score {c.get('overall_score', 'N/A')}, "
                f"Experience {c.get('experience_years', 0)}y, "
                f"Skills: {', '.join(c.get('skills', [])[:5])}"
            )

        comp_text = ""
        if comparison:
            comp_text = f"\nCOMPARISON RESULTS:\n{json.dumps(comparison, indent=2)}"

        prompt = f"""Generate a hiring recommendation report.

ROLE: {job.get('title', 'N/A')}
COMPANY: {job.get('company', 'N/A')}
DESCRIPTION: {job.get('description', 'N/A')}

CANDIDATES EVALUATED:
{chr(10).join(candidate_data)}
{comp_text}

Generate a professional report in JSON with:
- title: report title
- executive_summary: 2-3 sentence overview
- role_overview: brief role description
- evaluation_criteria: what was assessed
- candidate_analysis: for each candidate, strengths, weaknesses, and fit
- recommendation: who to hire and why
- risk_factors: potential concerns
- next_steps: recommended actions
- confidence_level: "high", "medium", or "low" in the recommendation

Return ONLY valid JSON."""

        response = await mimo_chat(
            system="You are a senior hiring consultant. Write clear, actionable reports.",
            user=prompt,
            temperature=0.3,
        )

        try:
            data = json.loads(response)
        except json.JSONDecodeError:
            import re
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                data = json.loads(match.group())
            else:
                return self._err("Failed to parse report response")

        data["generated_at"] = datetime.utcnow().isoformat()
        data["job_title"] = job.get("title")
        data["candidate_count"] = len(candidates)

        self.logger.info(f"Generated report for {job.get('title', '?')}")
        return self._ok(data)
