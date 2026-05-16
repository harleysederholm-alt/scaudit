# SC Audit Studio Benchmark

A novel benchmark suite for evaluating LLM capabilities in two critical Web3 domains:
1. Smart Contract Vulnerability Detection
2. Autonomous Crypto Trading

## Motivation and Economic Rationale
Standard LLM benchmarks suffer from overfitting and data contamination. This suite dynamically generates tests and environments locally, ensuring an **out-of-sample** evaluation of reasoning and economic intelligence.
- **Hedge Funds** can use this to vet AI agents for live trading.
- **Audit Firms** can use it to test internal security assistants.
- **LLM Providers** can prove their models' capabilities in high-stakes environments.

## Installation

```bash
pip install -r requirements.txt
```

Set your API Key (Optional, uses mocks if omitted):
```bash
export OPENAI_API_KEY="your-api-key"
```
Or on Windows:
```powershell
$env:OPENAI_API_KEY="your-api-key"
```

## Running the Benchmark

```bash
python benchmark_suite.py
```

This will run tests against multiple models and generate a `benchmark_results.md` file.
