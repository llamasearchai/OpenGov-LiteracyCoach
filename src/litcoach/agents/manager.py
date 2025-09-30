"""Agent Manager for OpenAI Agents SDK integration."""

import asyncio
import json
from typing import Dict, Any, List, Optional, Callable
from openai import AsyncOpenAI
from ..services.ollama_client import HybridLLMClient
from ..agents.security import SecureKeyManager
from ..agents.tools import AgentTools
from ..agents.vector_store import VectorStoreManager
from ..agents.retrieval import RetrievalManager


class AgentManager:
    """Manages OpenAI Agents SDK integration with enhanced features."""

    def __init__(self):
        self.key_manager = SecureKeyManager()
        self.openai_client = None
        self.ollama_client = None
        self.tools = AgentTools()
        self.vector_store = VectorStoreManager()
        self.retrieval = RetrievalManager(self.vector_store)
        self._initialize_clients()

    def _initialize_clients(self) -> None:
        """Initialize LLM clients based on available keys."""
        # Initialize OpenAI client if key is available
        openai_key = self.key_manager.get_openai_key()
        if openai_key:
            import os
            os.environ["OPENAI_API_KEY"] = openai_key
            self.openai_client = AsyncOpenAI(api_key=openai_key)

        # Initialize Ollama client
        ollama_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        self.ollama_client = HybridLLMClient(ollama_url, openai_key)

    async def create_agent_session(
        self,
        model: str = "gpt-4o-mini",
        provider: str = "auto",
        tools: Optional[List[Dict[str, Any]]] = None,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new agent session with specified configuration."""
        session_id = f"agent_{asyncio.get_event_loop().time()}"

        # Auto-detect provider if not specified
        if provider == "auto":
            if self.openai_client:
                provider = "openai"
            elif self.ollama_client:
                provider = "ollama"
            else:
                raise RuntimeError("No LLM provider available")

        session = {
            "id": session_id,
            "provider": provider,
            "model": model,
            "tools": tools or self.tools.get_default_tools(),
            "system_prompt": system_prompt,
            "messages": [],
            "metadata": {
                "created_at": asyncio.get_event_loop().time(),
                "last_activity": asyncio.get_event_loop().time()
            }
        }

        return session

    async def run_agent(
        self,
        session: Dict[str, Any],
        user_message: str,
        **kwargs
    ) -> str:
        """Run agent with user message and return response."""
        # Add user message to session
        user_msg = {
            "role": "user",
            "content": user_message,
            "timestamp": asyncio.get_event_loop().time()
        }
        session["messages"].append(user_msg)

        try:
            # Get response based on provider
            if session["provider"] == "openai" and self.openai_client:
                response = await self._run_openai_agent(session, **kwargs)
            elif session["provider"] == "ollama" and self.ollama_client:
                response = await self._run_ollama_agent(session, **kwargs)
            else:
                return "No suitable LLM provider available."

            # Add assistant response to session
            assistant_msg = {
                "role": "assistant",
                "content": response,
                "timestamp": asyncio.get_event_loop().time()
            }
            session["messages"].append(assistant_msg)
            session["metadata"]["last_activity"] = asyncio.get_event_loop().time()

            return response

        except Exception as e:
            error_msg = f"Agent execution failed: {str(e)}"
            # Add error message to session
            error_message = {
                "role": "assistant",
                "content": error_msg,
                "timestamp": asyncio.get_event_loop().time(),
                "is_error": True
            }
            session["messages"].append(error_message)
            return error_msg

    async def _run_openai_agent(
        self,
        session: Dict[str, Any],
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """Run agent using OpenAI client."""
        if not self.openai_client:
            raise RuntimeError("OpenAI client not initialized")

        # Prepare messages for OpenAI
        messages = []

        # Add system prompt if specified
        if session.get("system_prompt"):
            messages.append({
                "role": "system",
                "content": session["system_prompt"]
            })

        # Add conversation history
        for msg in session["messages"]:
            if not msg.get("is_error"):  # Skip error messages in history
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        # Add tools if available
        tools = session.get("tools", [])
        if tools:
            # Convert tools to OpenAI format
            openai_tools = []
            for tool in tools:
                openai_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool["description"],
                        "parameters": tool.get("parameters", {})
                    }
                })

            response = await self.openai_client.chat.completions.create(
                model=session["model"],
                messages=messages,
                tools=openai_tools if openai_tools else None,
                tool_choice="auto" if openai_tools else None,
                temperature=temperature,
                max_tokens=max_tokens
            )

            message = response.choices[0].message

            # Handle tool calls
            if hasattr(message, 'tool_calls') and message.tool_calls:
                # Execute tool calls
                tool_results = []
                for tool_call in message.tool_calls:
                    tool_result = await self._execute_tool_call(tool_call)
                    tool_results.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_call.function.name,
                        "content": json.dumps(tool_result)
                    })

                # Add tool results to messages and get final response
                messages.extend([
                    {"role": "assistant", "content": message.content, "tool_calls": message.tool_calls}
                ])
                messages.extend(tool_results)

                # Get final response
                final_response = await self.openai_client.chat.completions.create(
                    model=session["model"],
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )

                return final_response.choices[0].message.content

            return message.content

        else:
            # Simple completion without tools
            response = await self.openai_client.chat.completions.create(
                model=session["model"],
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            return response.choices[0].message.content

    async def _run_ollama_agent(
        self,
        session: Dict[str, Any],
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """Run agent using Ollama client."""
        if not self.ollama_client:
            raise RuntimeError("Ollama client not initialized")

        # Prepare messages for Ollama
        messages = []
        for msg in session["messages"]:
            if not msg.get("is_error"):  # Skip error messages in history
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        return await self.ollama_client.chat_completion(
            messages,
            model=session["model"],
            temperature=temperature,
            max_tokens=max_tokens
        )

    async def _execute_tool_call(self, tool_call) -> Any:
        """Execute a tool call from the agent."""
        try:
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)

            # Route to appropriate tool handler
            if tool_name == "lookup_texts":
                return await self.tools.lookup_texts(**tool_args)
            elif tool_name == "rag_search":
                return await self.tools.rag_search(**tool_args)
            elif tool_name == "assess_read_aloud":
                return await self.tools.assess_read_aloud(**tool_args)
            elif tool_name == "score_writing":
                return await self.tools.score_writing(**tool_args)
            elif tool_name == "search_vector_store":
                return await self.vector_store.search(**tool_args)
            elif tool_name == "add_to_vector_store":
                return await self.vector_store.add(**tool_args)
            else:
                return {"error": f"Unknown tool: {tool_name}"}

        except Exception as e:
            return {"error": f"Tool execution failed: {str(e)}"}

    async def add_knowledge_base(self, documents: List[Dict[str, Any]]) -> bool:
        """Add documents to the vector store for retrieval."""
        try:
            for doc in documents:
                await self.vector_store.add(
                    text=doc["content"],
                    metadata=doc.get("metadata", {})
                )
            return True
        except Exception:
            return False

    async def search_knowledge_base(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search the knowledge base for relevant information."""
        try:
            return await self.vector_store.search(query, top_k=top_k)
        except Exception:
            return []

    def get_session_stats(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Get statistics for a session."""
        messages = session.get("messages", [])

        return {
            "message_count": len(messages),
            "user_messages": len([m for m in messages if m["role"] == "user"]),
            "assistant_messages": len([m for m in messages if m["role"] == "assistant"]),
            "error_messages": len([m for m in messages if m.get("is_error")]),
            "session_duration": (
                asyncio.get_event_loop().time() - session["metadata"]["created_at"]
                if "created_at" in session["metadata"] else 0
            )
        }

    def cleanup_old_sessions(self, max_age_hours: int = 24) -> int:
        """Clean up old sessions. Returns number of sessions removed."""
        # This would be implemented to clean up old session data
        # For now, return 0
        return 0

    async def health_check(self) -> Dict[str, Any]:
        """Check health of all components."""
        health = {
            "openai_available": self.openai_client is not None,
            "ollama_available": self.ollama_client is not None,
            "vector_store_healthy": await self.vector_store.health_check(),
            "tools_available": len(self.tools.get_default_tools()) > 0
        }

        return health