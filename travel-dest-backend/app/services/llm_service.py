"""Helpers for cheap-model JSON work and strong-model final synthesis."""
# uses injected client and settings for Azure OpenAI calls
# using async
# using tenacity for retries with exponential backoff

# implements LLM generate_json and estimate_cost

import json
from dataclasses import dataclass
from typing import Any, cast

from openai import AsyncAzureOpenAI
from openai._types import Omit, omit
from openai.types.chat.completion_create_params import ResponseFormat
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import Settings
from app.core.logging import get_logger

logger = get_logger(__name__)
JSON_OBJECT_RESPONSE_FORMAT = cast(ResponseFormat, {"type": "json_object"})


@dataclass
class LLMResult:
    """Structured LLM result with parsed content and token usage."""

    content: str
    parsed_json: dict[str, Any] | None
    prompt_tokens: int
    completion_tokens: int

    @property
    def total_tokens(self) -> int:
        """Return prompt and completion tokens combined."""
        return self.prompt_tokens + self.completion_tokens


class LLMService:
    """Wrap Azure OpenAI chat calls for mechanical and synthesis tasks."""

    def __init__(self, client: AsyncAzureOpenAI, settings: Settings) -> None:
        """Store the shared client and settings for later reuse."""
        self.client = client
        self.settings = settings

    async def _chat_completion(
        self,
        deployment: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        response_format: ResponseFormat | Omit = omit,
    ) -> LLMResult:
        """Run one Azure chat completion with retries and token logging."""
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(self.settings.LLM_MAX_RETRIES),
            wait=wait_exponential(multiplier=1, min=1, max=8),
            retry=retry_if_exception_type(Exception),
            reraise=True,
        ):
            with attempt:
                response = await self.client.chat.completions.create(
                    model=deployment,
                    temperature=temperature,
                    response_format=response_format,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                )
                content = response.choices[0].message.content or ""
                parsed_json: dict[str, Any] | None = None
                if response_format is not omit and content.strip():
                    try:
                        parsed_json = json.loads(content)
                    except json.JSONDecodeError:
                        logger.exception(
                            "Azure OpenAI returned invalid JSON content",
                            extra={
                                "event": "llm_invalid_json",
                                "deployment": deployment,
                                "content_preview": content[:1000],
                            },
                        )
                        raise

                usage = response.usage
                logger.info(
                    "Completed Azure OpenAI call",
                    extra={
                        "event": "llm_call",
                        "deployment": deployment,
                        "prompt_tokens": getattr(usage, "prompt_tokens", 0),
                        "completion_tokens": getattr(usage, "completion_tokens", 0),
                        "total_tokens": getattr(usage, "total_tokens", 0),
                        "status": "success",
                    },
                )
                return LLMResult(
                    content=content,
                    parsed_json=parsed_json,
                    prompt_tokens=getattr(usage, "prompt_tokens", 0),
                    completion_tokens=getattr(usage, "completion_tokens", 0),
                )
        raise RuntimeError("Azure OpenAI completion did not return a response.")

    async def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        use_strong_model: bool = False,
    ) -> LLMResult:
        """Use the cheap or strong deployment to return a JSON object."""
        deployment = (
            self.settings.AZURE_OPENAI_STRONG_DEPLOYMENT
            if use_strong_model
            else self.settings.AZURE_OPENAI_CHEAP_DEPLOYMENT
        )
        return await self._chat_completion(
            deployment=deployment,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0,
            response_format=JSON_OBJECT_RESPONSE_FORMAT,
        )

    async def generate_text(self, system_prompt: str, user_prompt: str) -> LLMResult:
        """Use the strong deployment to produce the final synthesized answer."""
        return await self._chat_completion(
            deployment=self.settings.AZURE_OPENAI_STRONG_DEPLOYMENT,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.3,
        )

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int, strong: bool) -> float:
        """Estimate the request cost with configurable token prices."""
        if strong:
            input_rate = self.settings.STRONG_MODEL_INPUT_COST_PER_1K
            output_rate = self.settings.STRONG_MODEL_OUTPUT_COST_PER_1K
        else:
            input_rate = self.settings.CHEAP_MODEL_INPUT_COST_PER_1K
            output_rate = self.settings.CHEAP_MODEL_OUTPUT_COST_PER_1K

        return round(
            (prompt_tokens / 1000 * input_rate) + (completion_tokens / 1000 * output_rate),
            6,
        )
