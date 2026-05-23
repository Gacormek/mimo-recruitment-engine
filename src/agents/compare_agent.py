"""CompareAgent — side-by-side candidate comparison and ranking."""
import json
from .base_agent import BaseAgent
from ..mimo.client import mimo_chat


class CompareAgent(BaseAgent):
    """Compares multiple candidates and produces rankings."""

    async def run(self, candidates: list = None, job: dict = None, **kwargs) -> dict:
        """Compare candidates side by side and rank them."""
        if not candidates or len(candidates) < 2:
            return self._err("At least 2 candidates required for comparison")
        if not job:
            return self._err("Job data required")

        candidate_summaries = []
        for i, c in enumerate(candidates):
            candidate_summaries.append(
                f"CANDIDATE {i+1}: {c.get('name', f'Candidate {i+1}')}\n"
                f"  Skills: {json.dumps(c.get('skills', []))}\n"
                f"  Experience: {c.get('experience_years', 0)} years\n"
                f"  Education: {json.dumps(c.get('education', []))}\n"
                f"  Score: {c.get('overall_score', 'N/A')}"
            )

        prompt = f"""Compare these candidates for the role of {job.get('title', 'N/A')}.

{chr(10).join(candidate_summaries)}

JOB REQUIREMENTS:
- Required Skills: {json.dumps(job.get('required_skills', []))}
- Min Experience: {job.get('min_experience', 0)} years

Return JSON with:
- ranking: ordered list of candidate names (best first)
- comparison_matrix: for each dimension (skills, experience, education, overall), rank each candidate
- winner: name of the top candidate
- winner_reasoning: why the winner stands out
- summary: overall comparison summary

Return ONLY valid JSON."""

        response = await mimo_chat(
            system="You are a hiring comparison expert. Rank candidates objectively.",
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
                return self._err("Failed to parse comparison response")

        self.logger.info(f"Compared {len(candidates)} candidates for {job.get('title', '?')}")
        return self._ok(data)
