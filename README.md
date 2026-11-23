# template-crewai

[![Deploy to uagents8](https://img.shields.io/badge/Deploy%20to-uagents8-6366f1?style=for-the-badge)](https://app.uagents8.com)

A small [CrewAI](https://www.crewai.com) crew behind [FastAPI](https://fastapi.tiangolo.com), ready to deploy on
[uAgents8](https://uagents8.com) and to replace with your own crew. One of three
one-click framework templates: LangGraph, this one, and the OpenAI Agents SDK.

> **Today, the badge opens the dashboard**, where **+ Deploy Agent -> Source -> Templates ->
> CrewAI starter** deploys it in the steps below. **Use this as a GitHub template.**
> Click **Use this template** above to create your own copy in *your* GitHub account - never a
> write back to this repository. Download the code instead if you'd rather redeploy through
> Code Archive.

## What this is

One crew of two agents that work one after the other:

```text
researcher  lists the key points about the question
writer      turns those points into a short answer
```

| Route | What it does |
|---|---|
| `GET /` | A friendly status answer: `{"status": "ok", "agent": "template-crewai"}`. |
| `POST /ask` | Body `{"question": "..."}`. Answers `{"question", "answer", "mode"}`: `mode` is `"model"` once a key is set, `"stub"` otherwise. |

```bash
curl -X POST https://<your-agent>.uagents8.app/ask \
  -H 'Content-Type: application/json' \
  -d '{"question": "Why use a crew?"}'
```

## Pick a provider - or don't

It needs **no API key and no network** to start. Set `LLM_PROVIDER` to `openai` (the default)
or `anthropic`, and the matching `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` under
**Environment Variables** (**Sensitive** on). With neither key set, `POST /ask` still answers -
with a message that says exactly what to add - instead of refusing to start: a better first
impression than a crash loop (see `uagents8.json`'s `env_vars`).

The place you change to make it your own is `build_crew()` in `main.py` - the agents' roles,
backstories and tasks.

## Run it on your machine

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
PORT=8000 python main.py
```

In a second terminal:

```bash
curl http://localhost:8000/
curl -X POST http://localhost:8000/ask -H 'Content-Type: application/json' \
  -d '{"question": "Why use a crew?"}'
```

Checks: `pip install -r requirements-dev.txt && ruff check . && pytest`.

## What the platform needs, and where this template does it

- **Listen on the `PORT` environment variable, on `0.0.0.0`.** The last lines of `main.py`. The
  platform only checks that the port accepts connections; an API with only `/ask` would pass too.
- **A `main.py` at the top level that starts the server itself.** The platform runs `python main.py`.
- **A `requirements.txt` at the top level with every package pinned (`==`).** The build uses
  Python 3.12 and has no compiler, so every pin has a ready-made wheel.
- **No `Dockerfile` needed.** The platform writes one from your code.
- **Open the port quickly.** The port has to accept connections within about 150 seconds of the
  container starting.

## Deploy it from uAgents8

1. Press **+ Deploy Agent**.
2. **Details**: give it a name.
3. **Source**: **Templates -> CrewAI starter** (fastest), or **GitHub** (this repository,
   branch `main`), or **Code Archive**: from this folder run
   `zip template-crewai.zip main.py requirements.txt` and upload the file.
4. **Configure**: **Execution mode** **Continuous Service**, resource size **S** (512 MB - see
   `uagents8.json`'s `recommended_size`; this crew needs more memory than a single-agent
   template), and your provider's key if you have one.
5. **Confirm**, then **Deploy agent**.

When the status screen says **Running**, open the agent's URL and call it the same way as on your
machine.

## Use a real model

CrewAI already ships with OpenAI support (nothing to add). For Anthropic:

1. Add `anthropic` to `requirements.in`, resolve `requirements.txt` again (command in its header)
   and keep every pin.
2. Set `LLM_PROVIDER=anthropic` and `ANTHROPIC_API_KEY` under **Environment Variables**,
   **Sensitive** on.
3. Redeploy. A changed variable is only picked up on the next deploy.

`build_crew()` then calls the model and answers with `mode: "model"`. Neither provider is
exercised by the smoke tests (they cover the offline, no-key path only).

## About this repository

Maintained by the uAgents8 team. CI lints, runs the smoke tests and calls the running server on
every push and once a week (`.github/workflows/ci.yml`); a separate weekly job
(`.github/workflows/deploy-check.yml`) deploys this exact template to the platform's own e2e
sandbox, calls `POST /ask`, and deletes it - so a framework release or a dependency drift is
caught before a customer meets it, not after.
