"""
Local LLM Provider

Supports multiple local inference methods:
1. Direct model loading (transformers, llama.cpp) - PRIORITY 1 (truly local-first)
2. Ollama server API - PRIORITY 2 (fallback)
3. Other local API endpoints - PRIORITY 3 (fallback)

This enables "true local-first" operation where models run in-process
without requiring a separate server to be running.
"""

import os
from datetime import datetime
from typing import AsyncGenerator, Optional, Dict, Any
from pathlib import Path
from loguru import logger

from .base import BaseLLMProvider, LLMRequest, LLMResponse

# Try to import dependencies (all optional with graceful fallbacks)
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    logger.debug("httpx not installed. Ollama server fallback unavailable.")

try:
    import torch
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        pipeline
    )
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.debug("transformers not installed. Direct model loading unavailable.")


class DirectModelWrapper:
    """
    Wrapper for directly-loaded transformers models

    Loads models into memory and runs them in-process without
    requiring a separate server.
    """

    def __init__(self, model_name: str, cache_dir: Optional[str] = None):
        """
        Initialize direct model wrapper

        Args:
            model_name: HuggingFace model name (e.g., "microsoft/phi-2")
            cache_dir: Optional cache directory for model files
        """
        self.model_name = model_name
        self.cache_dir = cache_dir or os.path.expanduser("~/.ai-pal/models")
        self.model = None
        self.tokenizer = None
        self.pipeline = None

        # Ensure cache directory exists
        Path(self.cache_dir).mkdir(parents=True, exist_ok=True)

        logger.info(f"DirectModelWrapper initialized for {model_name}")

    def load(self):
        """Load model and tokenizer into memory"""
        if self.model is not None:
            return  # Already loaded

        logger.info(f"Loading {self.model_name} directly (this may take a moment)...")

        try:
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                cache_dir=self.cache_dir,
                trust_remote_code=True
            )

            # Load model with optimal settings
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                cache_dir=self.cache_dir,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto",  # Automatically use GPU if available
                trust_remote_code=True,
                low_cpu_mem_usage=True
            )

            # Create pipeline for easier inference
            self.pipeline = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device_map="auto"
            )

            logger.info(f"✓ {self.model_name} loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load {self.model_name} directly: {e}")
            raise

    def generate(self, prompt: str, max_tokens: int = 2000,
                 temperature: float = 0.7, top_p: float = 0.9) -> str:
        """
        Generate text using the loaded model

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter

        Returns:
            Generated text
        """
        if self.pipeline is None:
            self.load()

        try:
            outputs = self.pipeline(
                prompt,
                max_new_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=True,
                return_full_text=False  # Only return generated text
            )

            return outputs[0]["generated_text"]

        except Exception as e:
            logger.error(f"Direct generation failed: {e}")
            raise

    def unload(self):
        """Unload model from memory to free resources"""
        if self.model is not None:
            del self.model
            del self.tokenizer
            del self.pipeline
            self.model = None
            self.tokenizer = None
            self.pipeline = None

            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            logger.info(f"Unloaded {self.model_name}")


class LocalLLMProvider(BaseLLMProvider):
    """
    Local LLM Provider with multi-tier fallback

    Priority order:
    1. Direct in-process loading (transformers) - Fastest, truly local
    2. Ollama server API - Fast, requires separate process
    3. Falls back to cloud via orchestrator - Slowest, requires internet

    This enables "local-first" operation where simple tasks run entirely
    locally without any server dependencies.
    """

    # Model name mappings (HuggingFace name → Ollama name)
    MODEL_MAPPINGS = {
        "phi-2": "microsoft/phi-2",
        "phi-3": "microsoft/phi-3-mini-4k-instruct",
        "llama3.2": "meta-llama/Llama-3.2-3B-Instruct",
        "tinyllama": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "http://localhost:11434",
        enable_direct_loading: bool = True,
        model_cache_dir: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize Local LLM provider

        Args:
            api_key: Not used for local models
            base_url: Base URL for Ollama API (fallback)
            enable_direct_loading: Enable direct transformers loading (default: True)
            model_cache_dir: Directory to cache models
            **kwargs: Additional configuration
        """
        super().__init__(api_key, **kwargs)

        self.base_url = base_url or os.getenv("LOCAL_LLM_URL", "http://localhost:11434")
        self.enable_direct_loading = enable_direct_loading and TRANSFORMERS_AVAILABLE
        self.model_cache_dir = model_cache_dir

        # Cache for loaded models (to avoid reloading)
        self.loaded_models: Dict[str, DirectModelWrapper] = {}

        # Capability flags
        self.has_transformers = TRANSFORMERS_AVAILABLE
        self.has_httpx = HTTPX_AVAILABLE

        if self.enable_direct_loading:
            logger.info(f"Local LLM provider initialized (DIRECT MODE: transformers available)")
        elif self.has_httpx:
            logger.info(f"Local LLM provider initialized (SERVER MODE: Ollama API at {self.base_url})")
        else:
            logger.warning("Local LLM provider initialized but no backends available!")

    def is_available(self) -> bool:
        """Check if local LLM provider is available"""
        return self.enable_direct_loading or self.has_httpx

    def _get_hf_model_name(self, model_name: str) -> str:
        """Convert Ollama model name to HuggingFace model name"""
        return self.MODEL_MAPPINGS.get(model_name, model_name)

    async def _generate_direct(
        self,
        request: LLMRequest,
        model_name: str
    ) -> LLMResponse:
        """
        Generate using direct model loading (Priority 1)

        This loads the model directly into Python process memory and
        runs inference without requiring any external server.
        """
        start_time = datetime.now()

        try:
            # Get HuggingFace model name
            hf_model_name = self._get_hf_model_name(model_name)

            # Get or load model
            if model_name not in self.loaded_models:
                logger.info(f"First use of {model_name}, loading directly...")
                self.loaded_models[model_name] = DirectModelWrapper(
                    hf_model_name,
                    cache_dir=self.model_cache_dir
                )

            model_wrapper = self.loaded_models[model_name]

            # Build prompt
            full_prompt = request.prompt
            if request.system_prompt:
                full_prompt = f"{request.system_prompt}\n\nUser: {request.prompt}\n\nAssistant:"

            logger.debug(f"Generating with direct {model_name} ({len(full_prompt)} chars)")

            # Generate (this loads model if not already loaded)
            generated_text = model_wrapper.generate(
                full_prompt,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p
            )

            # Estimate tokens
            prompt_tokens = len(full_prompt) // 4
            completion_tokens = len(generated_text) // 4
            total_tokens = prompt_tokens + completion_tokens

            # Calculate latency
            latency_ms = (datetime.now() - start_time).total_seconds() * 1000

            logger.info(
                f"✓ Direct {model_name}: ~{completion_tokens} tokens, {latency_ms:.0f}ms"
            )

            return LLMResponse(
                generated_text=generated_text,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                cost_usd=0.0,
                model_name=model_name,
                provider="local-direct",
                latency_ms=latency_ms,
                finish_reason="complete",
                requested_at=start_time,
                completed_at=datetime.now(),
                raw_response={"method": "direct", "model": hf_model_name},
            )

        except Exception as e:
            logger.warning(f"Direct loading failed for {model_name}: {e}")
            raise

    async def _generate_ollama_server(
        self,
        request: LLMRequest,
        model_name: str
    ) -> LLMResponse:
        """
        Generate using Ollama server API (Priority 2 fallback)

        This requires Ollama server to be running separately.
        """
        start_time = datetime.now()

        try:
            # Build prompt
            full_prompt = request.prompt
            if request.system_prompt:
                full_prompt = f"{request.system_prompt}\n\nUser: {request.prompt}\n\nAssistant:"

            logger.debug(f"Calling Ollama server {model_name} ({len(full_prompt)} chars)")

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": model_name,
                        "prompt": full_prompt,
                        "stream": False,
                        "options": {
                            "temperature": request.temperature,
                            "top_p": request.top_p,
                            "num_predict": request.max_tokens,
                        }
                    }
                )

                response.raise_for_status()
                data = response.json()

            generated_text = data.get("response", "")

            # Estimate tokens
            prompt_tokens = len(full_prompt) // 4
            completion_tokens = len(generated_text) // 4
            total_tokens = prompt_tokens + completion_tokens

            latency_ms = (datetime.now() - start_time).total_seconds() * 1000

            logger.info(
                f"✓ Ollama {model_name}: ~{completion_tokens} tokens, {latency_ms:.0f}ms"
            )

            return LLMResponse(
                generated_text=generated_text,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                cost_usd=0.0,
                model_name=model_name,
                provider="local-ollama",
                latency_ms=latency_ms,
                finish_reason="complete",
                requested_at=start_time,
                completed_at=datetime.now(),
                raw_response=data,
            )

        except httpx.HTTPError as e:
            logger.warning(f"Ollama server failed: {e}")
            logger.info("Hint: Start Ollama with 'ollama serve'")
            raise
        except Exception as e:
            logger.warning(f"Ollama server generation failed: {e}")
            raise

    async def generate(
        self,
        request: LLMRequest,
        model_name: str = "phi-2"
    ) -> LLMResponse:
        """
        Generate completion from local LLM with automatic fallback

        Tries methods in priority order:
        1. Direct transformers loading (if available)
        2. Ollama server API (if available)
        3. Raises exception (orchestrator will handle cloud fallback)

        Args:
            request: LLM request
            model_name: Local model name

        Returns:
            LLM response

        Raises:
            RuntimeError: If all local methods fail
        """
        errors = []

        # Priority 1: Direct loading (truly local-first)
        if self.enable_direct_loading:
            try:
                logger.debug(f"Trying direct loading for {model_name}...")
                return await self._generate_direct(request, model_name)
            except Exception as e:
                error_msg = f"Direct loading failed: {e}"
                errors.append(error_msg)
                logger.debug(error_msg)

        # Priority 2: Ollama server (fallback)
        if self.has_httpx:
            try:
                logger.debug(f"Trying Ollama server for {model_name}...")
                return await self._generate_ollama_server(request, model_name)
            except Exception as e:
                error_msg = f"Ollama server failed: {e}"
                errors.append(error_msg)
                logger.debug(error_msg)

        # All local methods failed
        error_summary = " | ".join(errors) if errors else "No local backends available"
        logger.error(f"All local generation methods failed: {error_summary}")

        raise RuntimeError(
            f"Local generation failed for {model_name}. "
            f"Tried: {len(errors)} method(s). "
            f"Install transformers for direct loading, or start Ollama server. "
            f"Details: {error_summary}"
        )

    async def generate_streaming(
        self,
        request: LLMRequest,
        model_name: str = "phi-2"
    ) -> AsyncGenerator[str, None]:
        """
        Generate completion with streaming

        Currently only supports Ollama server mode for streaming.
        Direct mode returns full text at once.

        Args:
            request: LLM request
            model_name: Local model name

        Yields:
            Tokens as they're generated
        """
        # For direct mode, generate full text then yield it
        if self.enable_direct_loading and not self.has_httpx:
            response = await self._generate_direct(request, model_name)
            # Simulate streaming by yielding in chunks
            text = response.generated_text
            chunk_size = 10
            for i in range(0, len(text), chunk_size):
                yield text[i:i+chunk_size]
            return

        # Ollama server streaming mode
        if not self.has_httpx:
            raise RuntimeError("Streaming not available without httpx")

        try:
            # Build prompt
            full_prompt = request.prompt
            if request.system_prompt:
                full_prompt = f"{request.system_prompt}\n\nUser: {request.prompt}\n\nAssistant:"

            # Call Ollama API with streaming
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/generate",
                    json={
                        "model": model_name,
                        "prompt": full_prompt,
                        "stream": True,
                        "options": {
                            "temperature": request.temperature,
                            "top_p": request.top_p,
                            "num_predict": request.max_tokens,
                        }
                    }
                ) as response:
                    response.raise_for_status()

                    # Parse NDJSON stream
                    async for line in response.aiter_lines():
                        if line.strip():
                            import json
                            data = json.loads(line)
                            if "response" in data:
                                yield data["response"]

        except Exception as e:
            logger.error(f"Local LLM streaming failed: {e}")
            raise

    def unload_all_models(self):
        """Unload all loaded models to free memory"""
        for model_name, wrapper in self.loaded_models.items():
            wrapper.unload()
        self.loaded_models.clear()
        logger.info("Unloaded all local models")


# Alias for backward compatibility
LocalProvider = LocalLLMProvider
