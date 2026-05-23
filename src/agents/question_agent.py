"""QuestionAgent — generate role-specific interview questions."""
import json
from .base_agent import BaseAgent
from ..mimo.client import mimo_chat


class QuestionAgent(BaseAgent):
    """Generates technical and behavioral interview questions for a role."""

    async def run(self, job: dict = None, count: int = 10, **kwargs) -> dict:
        """Generate interview questions tailored to a job."""
        if not job:
            return self._err("Job data required")

        tech_count = max(3, count // 2)
        behav_count = count - tech_count

        prompt = f"""Generate interview questions for this role.

JOB DETAILS:
- Title: {job.get('title', 'N/A')}
- Description: {job.get('description', 'N/A')}
- Required Skills: {json.dumps(job.get('required_skills', []))}
- Min Experience: {job.get('min_experience', 0)} years

Generate {tech_count} technical questions and {behav_count} behavioral questions.

Return a JSON object with a "questions" array. Each question has:
- category: "technical" or "behavioral"
- question_text: the question
- expected_answer: what a strong answer looks like
- difficulty: "easy", "medium", or "hard"
- skill_tested: which skill/area this tests (for technical) or competency (for behavioral)

Return ONLY valid JSON."""

        response = await mimo_chat(
            system="You are an expert technical interviewer. Create insightful, relevant questions.",
            user=prompt,
            temperature=0.4,
        )

        try:
            data = json.loads(response)
        except json.JSONDecodeError:
            import re
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                data = json.loads(match.group())
            else:
                return self._err("Failed to parse questions response")

        questions = data.get("questions", [])
        self.logger.info(f"Generated {len(questions)} questions for {job.get('title', '?')}")
        return self._ok({"questions": questions, "job_title": job.get("title")})
