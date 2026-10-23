---
name: autohedge
description: Run market analysis and trading theses with the AutoHedge multi-agent pipeline (Director, Quant, Risk, Execution). Use when the user asks to analyze a stock, token, crypto or market sector, generate an investment thesis, size risk, or draft a trade plan with AutoHedge. Analysis-only by default; never executes real trades without explicit confirmation.
---

# AutoHedge

AutoHedge (https://github.com/The-Swarm-Corporation/AutoHedge) is a Python library that runs a pipeline of agents: Director (thesis), Quant (technical/statistical analysis), Risk (position sizing), Execution (order generation). It is built on the `swarms` framework. Execution on Solana goes through Jupiter Ultra.

## Safety rules (read first)

1. **Default mode is analysis only.** Do not set or ask for `SOLANA_PRIVATE_KEY` (the README calls it `WALLET_PRIVATE_KEY`, but the code in `autohedge/tools/ultra_tools.py` reads `SOLANA_PRIVATE_KEY`). Without it, the signing step cannot run.
2. Never print, log, commit or paste a private key. Keep keys in `.env`, which must be in `.gitignore`.
3. Only move to real execution if the user explicitly asks for it in this conversation. Then show the proposed order (asset, side, size, stop, take profit) and get a clear "yes" before running anything that signs a transaction. Suggest a small test amount first.
4. Always end results with: output is AI-generated analysis, not financial advice, and can be wrong.

## Setup

```bash
pip install -U autohedge
```

Create a `.env` in the working directory:

```
OPENAI_API_KEY=      # required by the default agents
ANTHROPIC_API_KEY=   # optional
JUPITER_API_KEY=     # token price/search tools, key from https://portal.jup.ag
WORKSPACE_DIR="agent_workspace"
```

Check which keys exist (without printing values) before running:

```bash
python -c "import os;from dotenv import load_dotenv;load_dotenv();print({k:bool(os.getenv(k)) for k in ['OPENAI_API_KEY','ANTHROPIC_API_KEY','JUPITER_API_KEY']})"
```

If `OPENAI_API_KEY` is missing, tell the user and stop; do not invent keys.

## Run an analysis

Tickers are derived from the task text by the Director, so name the assets in the task.

```python
from autohedge import AutoHedge

system = AutoHedge(
    name="analysis",
    description="Analysis-only run",
    output_type="str",   # "list" (default), "dict" or "str"
)
print(system.run(task="Analyze NVDA and give a thesis, risk assessment and a hypothetical trade plan."))
```

Save it as a script in the scratchpad or `/tmp`, then run it with `python script.py`. Interactive alternative: run `autohedge` in a terminal to open the REPL.

## Writing good tasks

- Name the asset(s) and the horizon: "Analyze SOL and JUP for the next 2 weeks".
- State the budget and risk tolerance: "for a 5k allocation, max 2% risk per trade".
- Ask for the output you want: thesis, entry, stop loss, take profit, time in force.

## Reporting back

Summarize for the user: assets analyzed, thesis, key risks, suggested sizing and stop/target levels, and any step that failed (missing key, API error). Quote the raw output only if the user asks. Mark clearly that nothing was executed.

## Troubleshooting

- `ModuleNotFoundError: swarms`: reinstall with `pip install -U autohedge swarms`.
- Warning that `OPENAI_API_KEY` is not set: add it to `.env` or export it.
- Network errors on market data: the environment may block hosts; report which one instead of retrying blindly.
