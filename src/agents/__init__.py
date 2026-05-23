"""Base agent class for all recruitment agents."""
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger("mimo.agents")


class BaseAgent(ABC):
    """Abstract base class for all agents in the recruitment engine."""

    def __init__(self):
        self.name = self.__class__.__name__
        self.logger = logging.getLogger(f"mimo.agents.{self.name}")

    async def initialize(self):
        """Called once when the kernel starts. Override for setup."""
        pass

    async def cleanup(self):
        """Called during shutdown. Override for teardown."""
        pass

    @abstractmethod
    async def run(self, **kwargs) -> dict:
        """Execute the agent's primary task. Must be implemented by subclasses."""
        raise NotImplementedError

    def _format_response(self, success: bool, data=None, error=None) -> dict:
        """Standard response format."""
        resp = {"success": success}
        if data is not None:
            resp["data"] = data
        if error is not None:
            resp["error"] = error
        return resp
