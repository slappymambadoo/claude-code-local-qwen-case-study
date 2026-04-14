[![License: Unlicense](https://img.shields.io/badge/license-Unlicense-blue.svg)](http://unlicense.org/)
[![Experiment Status](https://img.shields.io/badge/status-raw%20data-orange)](https://github.com/slappymambadoo/claude-code-local-qwen-case-study)
[![LLM](https://img.shields.io/badge/LLM-Qwen3.5--27B-blue)](https://github.com/QwenLM/Qwen)
[![Framework](https://img.shields.io/badge/framework-llama.cpp-black)](https://github.com/ggerganov/llama.cpp)
[![Tool](https://img.shields.io/badge/tool-Claude%20Code-purple)](https://docs.anthropic.com/en/docs/claude-code)
[![Platform](https://img.shields.io/badge/platform-WSL%202.0-0078D6)](https://learn.microsoft.com/en-us/windows/wsl/)

# claude-code-local-qwen-case-study

## Using llama.cpp on WSL 2.0
'llama-server' and 'Claude Code' run under WSL

## What is this?

A raw, unedited log of running **Claude Code** (Anthropic's agentic CLI) against a **local Qwen3.5-27B** model (Q8_0) via `llama.cpp`.

The task:

    build a Python CLI todo manager ("pytasker") with:
    - `add`, `list`, `complete`, `delete` commands
    - argparse, multiple modules, JSON persistence
    - error handling, and **50 unit tests** – all passing.

**Total time:** 29 minutes, 47 seconds.  
**Iterations:** 7‑8 debugging cycles.  
**Final result:** All 50 tests pass.

## Initial Condition

The project folder started out with instructions.md and project_instructions.md **ONLY** - everything else is created by following whats in instructions.md.

## Files in this repo

| File | What it is |
|------|-------------|
| `sample_llama.cpp_log.txt` | The **llama.cpp server log** – shows prompt processing (1994 t/s), generation (38 t/s), cache thrashing (9 checkpoints evicted), and total token counts. |
| `Claude_Code_client.log` | The **Claude Code client log** – every command, failed test, code edit, and the eventual success. |
| `Qwen3.5-27B-opustuned-Q8_0.py` | The **concatenated source code** produced by the model. Contains all modules and the 50 tests. |
| `instructions.md` | The exact commands I ran for this test |
| `project_instructions.md` | The exact prompt given to Claude Code (the task description). |
| `test.log` | The **pytest output** showing 50 tests passing in 0.04 seconds. |

## The playbook (exact commands I copy‑pasted using locally compiled llama.cpp)

You can reproduce this run exactly with the following steps (no script – just copy‑paste each line):

```bash
    # Terminal 1: Start llama.cpp server
    ~/llama.cpp/build/bin/llama-server \
    --model /models/Qwen3.5-27B-opustuned-Q8_0.gguf --reasoning on \
    --n-gpu-layers 99 --no-mmap --flash-attn on --cache-type-k q8_0 --cache-type-v q8_0 \
    --temp 0.0 --top-p 0.9 --top-k 40 --repeat-penalty 1.1 \
    --ctx-size 100000 --parallel 1 --threads 14 --port 8090

    # Terminal 2: Set up environment and run Claude Code
    cd ~/ClaudeCode_Test_qwen3.5_thinking
    rm -rf .venv
    python3.12 -m venv .venv
    source .venv/bin/activate
    python3 -m pip install --upgrade pip

    export ANTHROPIC_BASE_URL="http://127.0.0.1:8090"
    export ANTHROPIC_API_KEY="local"
    export ANTHROPIC_AUTH_TOKEN="local"
    export CLAUDE_CODE_MAX_OUTPUT_TOKENS="80000"
    export CLAUDE_CODE_AUTO_COMPACT_WINDOW="95000"
    export CLAUDE_CODE_DISABLE_AUTO_COMPACT="true"

    claude --dangerously-skip-permissions "Follow the instructions in project_instructions.md"
```

The content of project_instructions.md is in that file – it's the full task description.

Final test command (to verify the result)
After the run completes, the code is ready. To run the 50 tests:

```bash
    cd /home/paul/ClaudeCode_Test_qwen3.5_thinking && .venv/bin/python -m pytest tests/ -v
```

The output is captured in test.log – all 50 tests pass.

## Key observations (from the logs)
Prompt processing: 0.50 ms/token → 1994 tokens/second (decent).

Generation: 26.37 ms/token → 38 tokens/second (slow).

Total tokens: 62,248 (prompt + generation).

Cache thrashing: 9 context checkpoints created, each ~150 MiB, several evicted due to limits.

Iterations needed: Class name mismatches (TodoStorage → TaskStorage), argument order in CLI functions, dual implementations (TodoManager vs TaskManager), missing exception handlers, environment variable support – all fixed iteratively.

## Why this matters
Most "AI coding" demos show cloud models finishing this task in 2–5 minutes. This is the real world for a local 27B model on consumer hardware. It works, but it's slow. The trade‑off: privacy, control, and no API costs.

If you're evaluating local LLMs for agentic coding, this repo gives you hard numbers and a full transcript – no curation, no marketing.
