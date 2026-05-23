"""ScoreAgent — holistic candidate scoring via MiMo LLM."""
import json
from .base_agent import BaseAgent
from ..mimo.client import mimo_chat


class ScoreAgent(BaseAgent):
    """Performs weighted holistic scoring of candidates for a role."""

    WEIGHTS = {
        "technical": 0.35,
        "experience": 0.25,
        "education": 0.15,
        "cultural_fit": 0.25,
    }

    async def run(self, candidate: dict = None, job: dict = None, weights: dict = None, **kwargs) -> dict:
        """Score a candidate across multiple dimensions."""
        if not candidate or not job:
            return self._err("Both candidate and job data required")

        w = weights or self.WEIGHTS

        prompt = f"""Score this candidate for the given role across multiple dimensions.

CANDIDATE:
- Name: {candidate.get('name', 'Unknown')}
- Skills: {json.dumps(candidate.get('skills', []))}
- Experience: {candidate.get('experience_years', 0)} years
- Education: {json.dumps(candidate.get('education', []))}
- Work History: {json.dumps(candidate.get('work_history', []))}

JOB:
- Title: {job.get('title', 'N/A')}
- Description: {job.get('description', 'N/A')}
- Required Skills: {json.dumps(job.get('required_skills', []))}
- Min Experience: {job.get('min_experience', 0)} years

Score each dimension 0-100 and return JSON:
- technical_score: 0-100
- experience_score: 0-100
- education_score: 0-100
- cultural_fit_score: 0-100
- overall_score: 0-100 (weighted: technical {w['technical']}, experience {w['experience']}, education {w['education']}, cultural {w['cultural_fit']})
- rationale: detailed explanation of scores
- strengths: list of candidate strengths
- weaknesses: list of areas for improvement

Return ONLY valid JSON."""

        response = await mimo_chat(
            system="You are an expert hiring evaluator. Score candidates objectively and fairly.",
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
                return self._err("Failed to parse score response")

        # Recompute weighted overall if needed
        if "overall_score" not in data:
            data["overall_score"] = round(
                data.get("technical_score", 0) * w["technical"]
                + data.get("experience_score", 0) * w["experience"]
                + data.get("education_score", 0) * w["education"]
                + data.get("cultural_fit_score", 0) * w["cultural_fit"],
                1,
            )

        self.logger.info(f"Scored {candidate.get('name', '?')}: {data.get('overall_score', 0)}")
        return self._ok(data)
