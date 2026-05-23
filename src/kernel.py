"""AgentKernel — lifecycle management for all recruitment agents."""
import asyncio
import logging
from typing import Dict, Optional, Type
from datetime import datetime

logger = logging.getLogger("mimo.kernel")


class AgentStatus:
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentKernel:
    """Central kernel managing agent lifecycle, scheduling, and coordination."""

    def __init__(self):
        self._agents: Dict[str, "BaseAgent"] = {}
        self._status: Dict[str, str] = {}
        self._history: list[dict] = []
        self._lock = asyncio.Lock()
        self._started = False

    def register(self, agent: "BaseAgent"):
        """Register an agent with the kernel."""
        name = agent.__class__.__name__
        self._agents[name] = agent
        self._status[name] = AgentStatus.IDLE
        logger.info(f"Registered agent: {name}")

    async def start(self):
        """Initialize all registered agents."""
        self._started = True
        for name, agent in self._agents.items():
            try:
                await agent.initialize()
                logger.info(f"Initialized agent: {name}")
            except Exception as e:
                logger.error(f"Failed to initialize {name}: {e}")
                self._status[name] = AgentStatus.FAILED

    async def shutdown(self):
        """Gracefully shutdown all agents."""
        for name, agent in self._agents.items():
            try:
                await agent.cleanup()
            except Exception as e:
                logger.error(f"Error shutting down {name}: {e}")
        self._started = False

    async def execute(self, agent_name: str, **kwargs) -> dict:
        """Execute an agent task with lifecycle tracking."""
        agent = self._agents.get(agent_name)
        if not agent:
            return {"error": f"Agent '{agent_name}' not found"}

        async with self._lock:
            self._status[agent_name] = AgentStatus.RUNNING

        start_time = datetime.utcnow()
        try:
            result = await agent.run(**kwargs)
            elapsed = (datetime.utcnow() - start_time).total_seconds()

            async with self._lock:
                self._status[agent_name] = AgentStatus.COMPLETED
                self._history.append({
                    "agent": agent_name,
                    "status": AgentStatus.COMPLETED,
                    "elapsed_seconds": elapsed,
                    "timestamp": start_time.isoformat(),
                })

            return {"status": "success", "data": result, "elapsed": elapsed}

        except Exception as e:
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            async with self._lock:
                self._status[agent_name] = AgentStatus.FAILED
                self._history.append({
                    "agent": agent_name,
                    "status": AgentStatus.FAILED,
                    "error": str(e),
                    "elapsed_seconds": elapsed,
                    "timestamp": start_time.isoformat(),
                })
            logger.exception(f"Agent {agent_name} failed")
            return {"status": "error", "error": str(e), "elapsed": elapsed}

    def get_status(self) -> dict:
        """Get current status of all agents."""
        return {
            "agents": dict(self._status),
            "history": self._history[-50:],
            "started": self._started,
        }

    def get_agent(self, name: str):
        """Get a registered agent by name."""
        return self._agents.get(name)
