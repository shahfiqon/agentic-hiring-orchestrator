"""LLM utility functions for structured output generation.

This module provides centralized LLM configuration with Pydantic model binding
for type-safe, validated responses across all workflow nodes.
"""

from typing import Type, TypeVar, Union

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from pydantic import BaseModel

from config import get_settings

T = TypeVar('T', bound=BaseModel)


def get_structured_llm(pydantic_model: Type[T]) -> Union[ChatOpenAI, ChatAnthropic]:
    """Get a configured LLM instance with structured output binding.

    This function creates an LLM instance configured according to the
    application settings (provider, temperature, max_tokens) and binds it to
    the provided Pydantic model for structured output generation.

    Supports OpenAI, Anthropic Claude, and llama.cpp server providers.

    Args:
        pydantic_model: Pydantic model class defining the expected output schema.
            The LLM will be constrained to return responses matching this schema.

    Returns:
        Configured LLM instance ready for invocation (ChatOpenAI or ChatAnthropic).
            Use pattern: `result = llm.invoke(prompt)` where result is an
            instance of `pydantic_model`.

    Raises:
        ValueError: If the LLM provider is invalid or required API keys are missing.

    Examples:
        >>> from backend.src.models.review import Rubric
        >>> llm = get_structured_llm(Rubric)
        >>> result = llm.invoke("Generate a rubric for Senior Backend Engineer")
        >>> assert isinstance(result, Rubric)

        >>> from backend.src.models.memory import WorkingMemory
        >>> llm = get_structured_llm(WorkingMemory)
        >>> result = llm.invoke(prompt)
        >>> assert isinstance(result, WorkingMemory)
    """
    settings = get_settings()

    # Validate provider configuration
    if settings.llm_provider == "openai":
        if not settings.openai_api_key:
            raise ValueError(
                "OpenAI API key is required when llm_provider='openai'. "
                "Set OPENAI_API_KEY environment variable."
            )

        # Configure OpenAI provider
        llm = ChatOpenAI(
            model=settings.openai_model_name,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
            api_key=settings.openai_api_key,
        )

    elif settings.llm_provider == "anthropic":
        if not settings.anthropic_api_key:
            raise ValueError(
                "Anthropic API key is required when llm_provider='anthropic'. "
                "Set ANTHROPIC_API_KEY environment variable."
            )

        # Configure Anthropic provider
        llm = ChatAnthropic(
            model=settings.anthropic_model_name,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
            api_key=settings.anthropic_api_key,
        )

    elif settings.llm_provider == "llamacpp-server":
        # Configure llama.cpp server provider with OpenAI-compatible API
        llm = ChatOpenAI(
            base_url=settings.llamacpp_base_url,
            api_key=settings.llamacpp_api_key,
            model="local-model",  # Model name is ignored by llama.cpp server
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
        )

    else:
        raise ValueError(
            f"Invalid llm_provider: '{settings.llm_provider}'. "
            "Must be 'openai', 'anthropic', or 'llamacpp-server'."
        )

    # Bind Pydantic model for structured output
    # This leverages provider's structured output feature for type-safe responses
    # Both OpenAI and Anthropic support this via langchain's with_structured_output
    structured_llm = llm.with_structured_output(pydantic_model)

    return structured_llm
