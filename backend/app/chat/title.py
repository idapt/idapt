import logging
import os
import re
from typing import List, Optional
from llama_index.core.llms import LLM
from app.chat.schemas import MessageData
from llama_index.core.prompts import PromptTemplate
from llama_index.core.settings import Settings

logger = logging.getLogger("uvicorn")

TITLE_PROMPT = """You're a helpful assistant! Your task is to Generate a title for the chat. 
Here is the conversation history
---------------------
{conversation}
---------------------
Given the conversation history, please give me a title for the chat!
Your answer should be wrapped in one stick which follows the following format:
```
<title>
```"""


class ChatTitleGenerator:
    """
    Generate a title for the chat based on the conversation history
    """

    @classmethod
    def get_configured_prompt(cls) -> Optional[str]:
        prompt = TITLE_PROMPT
        if not prompt or prompt == "":
            return None
        return PromptTemplate(prompt)

    @classmethod
    async def generate_title(
        cls,
        llm: LLM,
        messages: List[MessageData],
    ) -> Optional[str]:
        """
        Generate a title for the chat based on the conversation history
        Return None if there is an error
        """
        prompt_template = cls.get_configured_prompt()
        if not prompt_template:
            return None

        try:
            # Reduce the cost by only using the last two messages
            last_user_message = None
            last_assistant_message = None
            for message in reversed(messages):
                if message.role == "user":
                    last_user_message = f"User: {message.content}"
                elif message.role == "assistant":
                    last_assistant_message = f"Assistant: {message.content}"
                if last_user_message and last_assistant_message:
                    break
            conversation: str = f"{last_user_message}\n{last_assistant_message}"

            # Call the LLM and parse questions from the output
            prompt = prompt_template.format(conversation=conversation)
            output = await llm.acomplete(prompt)
            title = cls._extract_title(output.text)

            return title
        except Exception as e:
            logger.error(f"Error when generating title: {e}")
            return None

    @classmethod
    def _extract_title(cls, text: str) -> str | None:
        content_match = re.search(r"```(.*?)```", text, re.DOTALL)
        content = content_match.group(1) if content_match else None
        if not content:
            return None
        return content.strip()