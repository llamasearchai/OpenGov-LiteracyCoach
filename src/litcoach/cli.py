import asyncio
import os
import textwrap
from typing import Optional, List, Dict, Any

import httpx
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()
app = typer.Typer(help="Literacy Coach command-line interface")


def get_gateway_url() -> str:
    return os.environ.get("GATEWAY_URL", "http://localhost:8000")


def get_agent_url() -> str:
    return os.environ.get("AGENT_URL", "http://localhost:8001")


def get_teacher_url() -> str:
    return os.environ.get("TEACHER_URL", "http://localhost:8004")


async def fetch_json(method: str, url: str, **kwargs) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.request(method, url, **kwargs)
        response.raise_for_status()
        if response.headers.get("content-type", "").startswith("application/json"):
            return response.json()
        return {"raw": response.text}


async def run_health_checks() -> List[Dict[str, Any]]:
    services = {
        "gateway": f"{get_gateway_url()}/health",
        "agent": f"{get_agent_url()}/health",
        "content": os.environ.get("CONTENT_URL", "http://localhost:8002") + "/health",
        "assessment": os.environ.get("ASSESSMENT_URL", "http://localhost:8003") + "/health",
        "teacher": f"{get_teacher_url()}/health",
    }
    results = []
    for name, endpoint in services.items():
        try:
            data = await fetch_json("GET", endpoint)
            results.append({"service": name, "status": "ok", "data": data})
        except Exception as exc:
            results.append({"service": name, "status": "error", "error": str(exc)})
    return results


def render_health_table(results: List[Dict[str, Any]]):
    table = Table(title="Service Health", box=box.SIMPLE_HEAVY)
    table.add_column("Service", style="cyan", no_wrap=True)
    table.add_column("Status", style="green")
    table.add_column("Details", style="white")

    for item in results:
        status = item["status"]
        details = ""
        if status == "ok":
            details = textwrap.shorten(str(item.get("data")), width=60)
        else:
            details = textwrap.shorten(item.get("error", ""), width=60)
        table.add_row(item["service"], status, details)

    console.print(table)


async def run_sample_agent(prompt: str, grade: str) -> str:
    payload = {
        "messages": [
            {"role": "user", "content": f"Grade {grade} student request:\n{prompt}"}
        ],
        "mode": "tutor",
        "student_grade": grade,
    }
    data = await fetch_json("POST", f"{get_agent_url()}/agent/respond", json=payload)
    return data.get("content", "")


async def list_teacher_classes() -> List[Dict[str, Any]]:
    data = await fetch_json("GET", f"{get_teacher_url()}/classes")
    return data.get("results", [])


async def create_teacher_class(name: str) -> Dict[str, Any]:
    return await fetch_json("POST", f"{get_teacher_url()}/classes", json={"name": name})


@app.command()
def health():
    """Check health endpoints for all services."""

    async def run():
        results = await run_health_checks()
        render_health_table(results)

    asyncio.run(run())


@app.command()
def tutor(
    prompt: str = typer.Option(..., help="Student prompt or question"),
    grade: str = typer.Option("5", help="Grade level context"),
):
    """Send a sample tutoring prompt to the agent service."""

    async def run():
        console.print(Panel.fit("Contacting agent...", style="bold cyan"))
        response_text = await run_sample_agent(prompt, grade)
        if response_text:
            console.print(Panel(response_text, title="Agent Response", style="green"))
        else:
            console.print(Panel("No response received", style="yellow"))

    asyncio.run(run())


@app.command()
def classes(name: Optional[str] = typer.Option(None, help="Optional class name to create")):
    """List existing teacher classes or create a new one."""

    async def run():
        if name:
            created = await create_teacher_class(name)
            console.print(Panel(str(created), title="Class Created", style="green"))
        classes_data = await list_teacher_classes()
        table = Table(title="Teacher Classes", box=box.SIMPLE)
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="white")
        for item in classes_data:
            table.add_row(item.get("id", ""), item.get("name", ""))
        console.print(table)

    asyncio.run(run())


@app.command()
def doctor():
    """Run holistic diagnostics across services and environment."""

    async def run():
        console.print(Panel.fit("Running Literacy Coach diagnostics", style="bold cyan"))
        results = await run_health_checks()
        render_health_table(results)
        console.print(Panel.fit("Diagnostics complete", style="green"))

    asyncio.run(run())


def main():
    app()


if __name__ == "__main__":
    main()


