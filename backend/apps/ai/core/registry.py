from typing import Type
from backend.apps.ai.agents.base.agent import BaseAgent


class AgentRegistry:
    _agents: dict[str, type[BaseAgent]] = {}

    @classmethod
    def register(cls, name: str, agent_cls: type[BaseAgent]) -> None:
        cls._agents[name] = agent_cls

    @classmethod
    def get(cls, name: str) -> type[BaseAgent]:
        agent_cls = cls._agents.get(name)
        if not agent_cls:
            raise KeyError(f"Agent not registered: {name}")
        return agent_cls

    @classmethod
    def list(cls) -> list[str]:
        return list(cls._agents.keys())

    @classmethod
    def create(cls, name: str, **kwargs) -> BaseAgent:
        agent_cls = cls.get(name)
        return agent_cls(**kwargs)
