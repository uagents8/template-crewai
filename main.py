"""A CrewAI crew behind FastAPI - the uAgents8 "CrewAI" template.

Kept deliberately close to a small, proven two-agent crew shape - so nothing about the measured
footprint changes: no extra provider package is installed by default (see requirements.txt); the
Anthropic path is only probed for at runtime, the same way the OpenAI path already works.

  GET  /      health - the platform only checks that the port accepts connections
  POST /ask   {"question": "..."} -> {"question", "answer", "mode"}

Provider: set LLM_PROVIDER to "openai" (default) or "anthropic", and the matching
OPENAI_API_KEY / ANTHROPIC_API_KEY under Environment Variables with Sensitive on.
With no key set the template still starts and answers - see NO_KEY_MESSAGE below, a deliberately
better first impression than refusing to boot.

Make it yours: change the agents' roles and the tasks in build_crew().
"""

import os

# The crew sends anonymous usage data by default; this sample makes no outbound call of its own. Delete to keep it on.
os.environ.setdefault("CREWAI_DISABLE_TELEMETRY", "true")

import uvicorn  # noqa: E402
from crewai import LLM, Agent, Crew, Process, Task  # noqa: E402
from crewai.llms.base_llm import BaseLLM  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

AGENT_NAME = "template-crewai"

NO_KEY_MESSAGE = (
    "Add your API key to see a real answer: set LLM_PROVIDER to \"openai\" or \"anthropic\" and the "
    "matching OPENAI_API_KEY or ANTHROPIC_API_KEY under Environment Variables (Sensitive on), then redeploy."
)


class StubLLM(BaseLLM):
    """Offline stand-in for a model, in the format a crew agent expects (a ReAct-style "Final Answer:" line -
    CrewAI's own task-output parsing extracts just that part, so callers never see this wrapper).
    Deterministic, no network: every agent in the crew gets the same `reason` whichever step it's on."""

    llm_type: str = "stub"
    reason: str = NO_KEY_MESSAGE

    def __init__(self, reason: str = NO_KEY_MESSAGE) -> None:
        super().__init__(model="stub")
        self.reason = reason

    def call(
        self,
        messages,
        tools=None,
        callbacks=None,
        available_functions=None,
        from_task=None,
        from_agent=None,
        response_model=None,
    ):
        return f"Thought: I now can give a great answer\nFinal Answer: {self.reason}"

    def supports_function_calling(self) -> bool:
        return False


def _build_llm() -> BaseLLM:
    """LLM_PROVIDER ("openai", the default, or "anthropic") and the matching key, read fresh on
    every call (build_crew() below is called once per request, not once at import) - the same
    "re-read on every request" behaviour template-langgraph's respond() already has. With no key
    set, or the matching provider package missing, returns StubLLM instead of raising - the crew
    always starts and always answers."""
    provider = os.environ.get("LLM_PROVIDER", "openai").strip().lower()
    if provider == "anthropic":
        if not os.environ.get("ANTHROPIC_API_KEY"):
            return StubLLM(NO_KEY_MESSAGE)
        try:
            import anthropic  # noqa: F401  (native Anthropic path, "crewai[anthropic]"; not in requirements.txt by default)
        except ImportError:
            return StubLLM("ANTHROPIC_API_KEY is set but the anthropic package is not in requirements.txt.")
        model = f"anthropic/{os.environ.get('MODEL_NAME', 'claude-3-5-haiku-latest')}"
        return LLM(model=model, max_tokens=4096)  # max_tokens is required for every Anthropic model
    if not os.environ.get("OPENAI_API_KEY"):
        return StubLLM(NO_KEY_MESSAGE)
    return LLM(model=os.environ.get("MODEL_NAME", "gpt-4o-mini"))


def build_crew() -> Crew:
    llm = _build_llm()
    researcher = Agent(
        role="researcher",
        goal="List the key points a good answer to the question needs",
        backstory="You collect the facts that matter and leave out the rest.",
        llm=llm,
        allow_delegation=False,
    )
    writer = Agent(
        role="writer",
        goal="Write a short, clear answer from the researcher's key points",
        backstory="You write for busy readers: two or three sentences, no filler.",
        llm=llm,
        allow_delegation=False,
    )
    research = Task(
        description="Question: {question}\nList the key points a good answer needs.",
        expected_output="A short list of key points.",
        agent=researcher,
    )
    write = Task(
        description="Question: {question}\nUsing the key points, write a short answer.",
        expected_output="An answer of at most three sentences.",
        agent=writer,
        context=[research],
    )
    return Crew(agents=[researcher, writer], tasks=[research, write], process=Process.sequential, verbose=False)


app = FastAPI(title=AGENT_NAME)


class Ask(BaseModel):
    question: str = Field(min_length=1, max_length=500)


@app.get("/")
def index() -> dict[str, str]:
    """A friendly status route. The platform does not call it: its check is that the port accepts connections."""
    return {"status": "ok", "agent": AGENT_NAME}


@app.post("/ask")
def ask(body: Ask) -> dict[str, str]:
    crew = build_crew()
    result = crew.kickoff(inputs={"question": body.question})
    mode = "stub" if isinstance(crew.agents[0].llm, StubLLM) else "model"
    return {"question": body.question, "answer": result.raw, "mode": mode}


if __name__ == "__main__":
    # The platform sets PORT; listen on all interfaces, not just localhost.
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
