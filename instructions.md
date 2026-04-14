## llama.cpp

# Qwen3.5-27B-opustuned-Q8_0
~/llama.cpp/build/bin/llama-server \
  --model /models/Qwen3.5-27B-opustuned-Q8_0.gguf --reasoning on \
  --n-gpu-layers 99 --no-mmap --flash-attn on --cache-type-k q8_0 --cache-type-v q8_0 \
  --temp 0.0 --top-p 0.9 --top-k 40 --repeat-penalty 1.1 --ctx-size 100000 --parallel 1 --threads 14 --port 8090

## CLAUDE TEST ##

# Setup Python environment (WSL) 
clear
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