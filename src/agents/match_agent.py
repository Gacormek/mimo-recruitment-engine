"""MatchAgent — match candidate profiles to job requirements."""
import json
from .base_agent import BaseAgent
from ..mimo.client import mimo_chat


class MatchAgent(BaseAgent):
    """Matches a candidate profile against job requirements."""

    async def run(self, candidate: dict = None, job: dict = None, **kwargs) -> dict:
        """Compute match scores between candidate and job."""
        if not candidate or not job:
            return self._err("Both candidate and job data required")

        prompt = f"""Compare this candidate against the job requirements and compute match scores.

CANDIDATE:
- Skills: {json.dumps(candidate.get('skills', []))}
- Experience: {candidate.get('experience_years', 0)} years
- Education: {json.dumps(candidate.get('education', []))}

JOB REQUIREMENTS:
- Title: {job.get('title', 'N/A')}
- Required Skills: {json.dumps(job.get('required_skills', []))}
- Preferred Skills: {json.dumps(job.get('preferred_skills', []))}
- Min Experience: {job.get('min_experience', 0)} years
- Education: {job.get('education_requirement', 'N/A')}

Return a JSON object with:
- skill_overlap_score: 0-100 (percentage of required skills matched)
- preferred_skill_score: 0-100 (percentage of preferred skills matched)
- experience_fit_score: 0-100 (how well experience matches)
- education_fit_score: 0-100
- overall_match_score: 0-100 (weighted composite)
- matched_skills: list of skills that match
- missing_skills: list of required skills candidate lacks
- match_reasoning: brief explanation

Return ONLY valid JSON."""

        response = await mimo_chat(
            system="You are a talent matching expert. Score candidates objectively.",
            user=prompt,
            temperature=0.2,
        )

        try:
            data = json.loads(response)
        except json.JSONDecodeError:
            import re
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                data = json.loads(match.group())
            else:
                return self._err("Failed to parse match response")

        self.logger.info(
            f"Match: {candidate.get('name', '?')} → {job.get('title', '?')} = {data.get('overall_match_score', 0)}"
        )
        return self._ok(data)
