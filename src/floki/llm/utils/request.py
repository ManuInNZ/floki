from typing import Dict, Any, Optional, List, Type, Union, Iterable
from floki.prompt.prompty import Prompty, PromptyHelper
from floki.types.message import BaseMessage
from floki.llm.utils import StructureHandler
from floki.tool.utils.tool import ToolHelper
from pydantic import BaseModel

import logging

logger = logging.getLogger(__name__)

class RequestHandler:
    """
    Handles the preparation of requests for language models.
    """

    @staticmethod
    def process_prompty_messages(prompty: Prompty, inputs: Dict[str, Any] = {}) -> List[Dict[str, Any]]:
        """
        Process and format messages based on Prompty template and provided inputs.

        Args:
            prompty (Prompty): The Prompty instance containing the template and settings.
            inputs (Dict[str, Any]): Input variables for the Prompty template (default is an empty dictionary).

        Returns:
            List[Dict[str, Any]]: Processed and prepared messages.
        """
        # Prepare inputs and generate messages from Prompty content
        api_type = prompty.model.api
        prepared_inputs = PromptyHelper.prepare_inputs(inputs, prompty.inputs, prompty.sample)
        messages = PromptyHelper.to_prompt(prompty.content, prepared_inputs, api_type=api_type)

        return messages
    
    @staticmethod
    def normalize_chat_messages(messages: Union[str, Dict[str, Any], BaseMessage, Iterable[Union[Dict[str, Any], BaseMessage]]]) -> List[Dict[str, Any]]:
        """
        Normalize and validate the input messages into a list of dictionaries.

        Args:
            messages (Union[str, Dict[str, Any], BaseMessage, Iterable[Union[Dict[str, Any], BaseMessage]]]): 
                Input messages in various formats (string, dict, BaseMessage, or an iterable).

        Returns:
            List[Dict[str, Any]]: A list of normalized message dictionaries with keys 'role' and 'content'.

        Raises:
            ValueError: If the input format is unsupported or if required fields are missing in a dictionary.
        """
        # Initialize an empty list to store the normalized messages
        normalized_messages = []

        # Use a queue to process messages iteratively and handle nested structures
        queue = [messages]

        while queue:
            msg = queue.pop(0)
            if isinstance(msg, str):
                normalized_messages.append({"role": "user", "content": msg})
            elif isinstance(msg, BaseMessage):
                normalized_messages.append(msg.model_dump())
            elif isinstance(msg, dict):
                role = msg.get("role")
                if role not in {"user", "assistant", "tool", "system"}:
                    raise ValueError(f"Unrecognized role '{role}'. Supported roles are 'user', 'assistant', 'tool', or 'system'.")
                normalized_messages.append(msg)
            elif isinstance(msg, Iterable) and not isinstance(msg, (str, dict)):
                queue.extend(msg)
            else:
                raise ValueError(f"Unsupported message format: {type(msg)}")
        return normalized_messages
    
    @staticmethod
    def process_params(
        params: Dict[str, Any],
        llm_provider: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        response_model: Optional[Type[BaseModel]] = None,
    ) -> Dict[str, Any]:
        """
        Prepare request parameters for the language model.

        Args:
            params: Parameters for the request.
            llm_provider: The LLM provider to use (e.g., 'openai').
            tools: List of tools to include in the request.
            response_model: A pydantic model to parse and validate the structured response.

        Returns:
            Dict[str, Any]: Prepared request parameters.
        """
        if tools:
            logger.info("Tools are available in the request.")
            params['tools'] = [ToolHelper.format_tool(tool, tool_format=llm_provider) for tool in tools]

        if response_model:
            logger.info("A response model has been passed to structure the response of the LLM.")
            params = StructureHandler.generate_request(response_model=response_model, llm_provider=llm_provider, **params)
        
        return params 