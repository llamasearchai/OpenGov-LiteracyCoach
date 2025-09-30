#!/usr/bin/env python3
"""Health check script for Docker containers."""

import asyncio
import os
import sys
import httpx
import json
from typing import Dict, Any


async def check_service_health(url: str, service_name: str) -> Dict[str, Any]:
    """Check health of a specific service."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

            return {
                "service": service_name,
                "status": "healthy",
                "url": url,
                "response_time": response.elapsed.total_seconds(),
                "data": data
            }
    except Exception as e:
        return {
            "service": service_name,
            "status": "unhealthy",
            "url": url,
            "error": str(e)
        }


async def main():
    """Run health checks for all services."""
    services = {
        "gateway": f"http://localhost:{os.environ.get('GATEWAY_PORT', '8000')}/health",
        "agent": f"http://localhost:{os.environ.get('AGENT_PORT', '8001')}/health",
        "content": f"http://localhost:{os.environ.get('CONTENT_PORT', '8002')}/health",
        "assessment": f"http://localhost:{os.environ.get('ASSESSMENT_PORT', '8003')}/health",
        "teacher": f"http://localhost:{os.environ.get('TEACHER_PORT', '8004')}/health",
    }

    # Check which services are expected to be running
    # In a single container deployment, only one service runs
    current_service = os.environ.get('LITCOACH_SERVICE', 'gateway')

    if current_service in services:
        health = await check_service_health(services[current_service], current_service)

        # Output in JSON format for Docker health check
        print(json.dumps(health, indent=2))

        # Exit with appropriate code
        sys.exit(0 if health["status"] == "healthy" else 1)
    else:
        print(json.dumps({
            "service": "unknown",
            "status": "unhealthy",
            "error": f"Unknown service: {current_service}"
        }, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())