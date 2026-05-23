"""ParseAgent — extract structured data from resumes/CVs."""
import re
import json
from .base_agent import BaseAgent
from ..mimo.client import mimo_chat


class ParseAgent(BaseAgent):
    """Parses resume text to extract skills, experience, and education."""

    async def run(self, resume_text: str = "", resume_path: str = "", **kwargs) -> dict:
        """Parse a resume and extract structured candidate data."""
        if not resume_text:
            return self._err("No resume text provided")

        prompt = f"""Analyze this resume/CV and extract structured information.
Return a JSON object with these fields:
- name: candidate full name
- email: email address (or null)
- phone: phone number (or null)
- skills: list of technical and professional skills
- experience_years: total years of professional experience (number)
- education: list of education entries with degree, institution, year
- work_history: list of jobs with title, company, duration, description
- certifications: list of certifications
- summary: 2-3 sentence professional summary

RESUME TEXT:
{resume_text[:4000]}

Return ONLY valid JSON, no markdown."""

        response = await mimo_chat(
            system="You are a resume parsing expert. Extract structured data accurately. Return only valid JSON.",
            user=prompt,
            temperature=0.1,
        )

        try:
            data = json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                data = json.loads(match.group())
            else:
                return self._err("Failed to parse LLM response as JSON")

        # Ensure required fields
        data.setdefault("skills", [])
        data.setdefault("experience_years", 0)
        data.setdefault("education", [])

        self.logger.info(f"Parsed resume for: {data.get('name', 'unknown')}")
        return self._ok(data)
