"""Ollama client for local LLM integration."""

import json
import asyncio
from typing import List, Dict, Any, Optional
import httpx
from ..utils.openai_client import get_client as get_openai_client


class OllamaClient:
    """Client for interacting with Ollama API."""

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=300.0)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def list_models(self) -> List[Dict[str, Any]]:
        """List available models."""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            data = response.json()
            return data.get("models", [])
        except Exception as e:
            return []

    async def pull_model(self, model_name: str) -> bool:
        """Pull a model from Ollama registry."""
        try:
            async with self.client.stream(
                "POST",
                f"{self.base_url}/api/pull",
                json={"name": model_name}
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            data = json.loads(line)
                            if data.get("status"):
                                print(f"Pull status: {data['status']}")
                        except json.JSONDecodeError:
                            pass
            return True
        except Exception as e:
            print(f"Error pulling model {model_name}: {e}")
            return False

    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: str = "llama3",
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """Generate chat completion using Ollama."""
        try:
            # Convert messages to Ollama format
            ollama_messages = []
            for msg in messages:
                ollama_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

            payload = {
                "model": model,
                "messages": ollama_messages,
                "temperature": temperature,
                "num_predict": max_tokens,
                "stream": False
            }

            response = await self.client.post(
                f"{self.base_url}/api/chat",
                json=payload
            )
            response.raise_for_status()

            data = response.json()
            return data.get("message", {}).get("content", "")

        except Exception as e:
            raise RuntimeError(f"Ollama chat completion failed: {str(e)}")

    async def generate_completion(
        self,
        prompt: str,
        model: str = "llama3",
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """Generate text completion using Ollama."""
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "temperature": temperature,
                "num_predict": max_tokens,
                "stream": False
            }

            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json=payload
            )
            response.raise_for_status()

            data = response.json()
            return data.get("response", "")

        except Exception as e:
            raise RuntimeError(f"Ollama completion failed: {str(e)}")

    async def create_embeddings(self, texts: List[str], model: str = "nomic-embed-text") -> List[List[float]]:
        """Create embeddings for texts using Ollama."""
        try:
            payload = {
                "model": model,
                "prompt": texts[0] if len(texts) == 1 else "\n".join(texts)
            }

            response = await self.client.post(
                f"{self.base_url}/api/embeddings",
                json=payload
            )
            response.raise_for_status()

            data = response.json()
            embedding = data.get("embedding", [])

            # If multiple texts, return the same embedding for each (simplified)
            return [embedding] * len(texts)

        except Exception as e:
            raise RuntimeError(f"Ollama embeddings failed: {str(e)}")

    async def check_health(self) -> bool:
        """Check if Ollama service is healthy."""
        try:
            response = await self.client.get(f"{self.base_url}/api/version")
            return response.status_code == 200
        except Exception:
            return False

    async def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific model."""
        try:
            response = await self.client.post(
                f"{self.base_url}/api/show",
                json={"name": model_name}
            )
            response.raise_for_status()
            return response.json()
        except Exception:
            return None


class HybridLLMClient:
    """Client that can use both Ollama and OpenAI."""

    def __init__(self, ollama_base_url: str = "http://localhost:11434", openai_api_key: Optional[str] = None):
        self.ollama_client = OllamaClient(ollama_base_url)
        self.openai_client = None
        if openai_api_key:
            import os
            os.environ["OPENAI_API_KEY"] = openai_api_key
            self.openai_client = get_openai_client()

    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        provider: str = "ollama",
        model: str = "llama3",
        **kwargs
    ) -> str:
        """Get chat completion from specified provider."""
        if provider == "ollama":
            return await self.ollama_client.chat_completion(messages, model, **kwargs)
        elif provider == "openai" and self.openai_client:
            return await self._openai_chat_completion(messages, model, **kwargs)
        else:
            raise ValueError(f"Unknown provider: {provider}")

    async def _openai_chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """Get completion from OpenAI."""
        if not self.openai_client:
            raise RuntimeError("OpenAI client not initialized")

        response = self.openai_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )

        return response.choices[0].message.content

    async def create_embeddings(
        self,
        texts: List[str],
        provider: str = "ollama",
        model: str = "nomic-embed-text"
    ) -> List[List[float]]:
        """Create embeddings using specified provider."""
        if provider == "ollama":
            return await self.ollama_client.create_embeddings(texts, model)
        elif provider == "openai" and self.openai_client:
            return await self._openai_embeddings(texts, model)
        else:
            raise ValueError(f"Unknown provider: {provider}")

    async def _openai_embeddings(self, texts: List[str], model: str = "text-embedding-3-small") -> List[List[float]]:
        """Create embeddings using OpenAI."""
        if not self.openai_client:
            raise RuntimeError("OpenAI client not initialized")

        response = self.openai_client.embeddings.create(
            input=texts,
            model=model
        )

        return [data.embedding for data in response.data]

    async def check_health(self, provider: str = "ollama") -> bool:
        """Check health of specified provider."""
        if provider == "ollama":
            return await self.ollama_client.check_health()
        elif provider == "openai" and self.openai_client:
            try:
                # Simple health check
                await self.openai_client.models.list()
                return True
            except Exception:
                return False
        return False