"""EvaluateAgent — analyze and score interview responses."""
import json
from .base_agent import BaseAgent
from ..mimo.client import mimo_chat


class EvaluateAgent(BaseAgent):
    """Evaluates candidate answers to interview questions."""

    async def run(self, question: dict = None, answer: str = "", **kwargs) -> dict:
        """Score a candidate's answer to an interview question."""
        if not question or not answer:
            return self._err("Both question and answer required")

        prompt = f"""Evaluate this interview answer.

QUESTION: {question.get('question_text', 'N/A')}
CATEGORY: {question.get('category', 'N/A')}
DIFFICULTY: {question.get('difficulty', 'medium')}
EXPECTED ANSWER GUIDANCE: {question.get('expected_answer', 'N/A')}

CANDIDATE ANSWER:
{answer}

Return JSON with:
- score: 0-100
- feedback: detailed constructive feedback
- strengths: list of what was good
- improvements: list of suggestions
- key_points_hit: list of expected points the candidate covered
- key_points_missed: list of expected points missed

Return ONLY valid JSON."""

        response = await mimo_chat(
            system="You are a fair interview evaluator. Provide constructive, balanced feedback.",
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
                return self._err("Failed to parse evaluation response")

        self.logger.info(f"Evaluated answer: score={data.get('score', 0)}")
        return self._ok(data)
