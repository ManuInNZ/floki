from floki.agent.patterns import ReActAgent, ToolCallAgent, OpenAPIReActAgent
from floki.tool.utils.openapi import OpenAPISpecParser
from floki.memory import ConversationListMemory
from floki.llm import OpenAIChatClient
from floki.agent.base import AgentBase
from floki.llm import LLMClientBase
from floki.memory import MemoryBase
from floki.tool import AgentTool
from typing import Optional, List, Union, Type, TypeVar

T = TypeVar('T', ToolCallAgent, ReActAgent, OpenAPIReActAgent)

class AgentFactory:
    """
    Returns agent classes based on the provided pattern.
    """
    AGENT_PATTERNS = {
        "react": ReActAgent,
        "toolcalling": ToolCallAgent,
        "openapireact": OpenAPIReActAgent
    }

    @staticmethod
    def create_agent_class(pattern: str) -> Type[T]:
        """
        Selects the agent class based on the pattern.

        Args:
            pattern (str): Pattern type ('react', 'toolcalling', 'openapireact').

        Returns:
            Type: Corresponding agent class.

        Raises:
            ValueError: If the pattern is unsupported.
        """
        pattern = pattern.lower()
        agent_class = AgentFactory.AGENT_PATTERNS.get(pattern)
        if not agent_class:
            raise ValueError(f"Unsupported agent pattern: {pattern}")
        return agent_class


class Agent(AgentBase):
    """
    Dynamically creates an agent instance based on the specified pattern.
    """

    def __new__(
        cls,
        role: str,
        name: Optional[str] = None,
        pattern: str = "toolcalling",
        llm: Optional[LLMClientBase] = OpenAIChatClient(),
        memory: Optional[MemoryBase] = ConversationListMemory(),
        tools: Optional[List[AgentTool]] = [],
        **kwargs
    ) -> Union[ToolCallAgent, ReActAgent, OpenAPIReActAgent]:
        """
        Creates and returns an instance of the selected agent class.

        Args:
            role (str): Agent role.
            name (Optional[str]): Agent name.
            pattern (str): Agent pattern to use.
            llm (Optional[LLMClientBase]): LLM client for generating responses.
            memory (Optional[MemoryBase]): Memory for conversation history.
            tools (Optional[List[AgentTool]]): List of tools for task execution.

        Returns:
            Union[ToolCallAgent, ReActAgent, OpenAPIReActAgent]: The initialized agent instance.
        """
        agent_class = AgentFactory.create_agent_class(pattern)

        if pattern == "openapireact":
            kwargs.update({
                "spec_parser": kwargs.get('spec_parser', OpenAPISpecParser()),
                "auth_header": kwargs.get('auth_header', {})
            })

        instance = super().__new__(agent_class)
        agent_class.__init__(instance, role=role, name=name, llm=llm, memory=memory, tools=tools, **kwargs)
        return instance