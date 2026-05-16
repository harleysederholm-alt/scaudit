import os
import logging
from vuln_benchmark import run_vulnerability_benchmark
from trading_benchmark import run_trading_benchmark

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def generate_markdown_report(results: dict):
    md_content = f"""# SC Audit Studio - LLM Benchmark Report

## 1. Smart Contract Vulnerability Detection
| Model | Accuracy (%) | Tests |
|-------|--------------|-------|
"""
    for model, data in results["vuln"].items():
        md_content += f"| {model} | {data['accuracy']:.2f}% | {data['tests']} |\n"

    md_content += """
## 2. Dynamic Trading Agent Performance (Out-of-Sample)
| Model | Sharpe Ratio | Max Drawdown | Win Rate | Total Return |
|-------|--------------|--------------|----------|--------------|
"""
    for model, metrics in results["trading"].items():
        md_content += f"| {model} | {metrics['sharpe']:.2f} | {metrics['max_dd']:.2f}% | {metrics['win_rate']:.2f}% | {metrics['total_return']:.2f}% |\n"

    md_content += """
## Methodology & Anti-Overfitting
- **Vulnerability Benchmark**: Generates synthetic, novel smart contracts dynamically using randomness to bypass exact string-matching memorization in LLMs.
- **Trading Benchmark**: Uses dynamically generated random walk market conditions, ensuring the model reacts to out-of-sample data, simulating real economic risk environments.

## Economic Rationale
This benchmark is commercially valuable for:
1. **Hedge Funds & Prop Trading**: Evaluating the reliability of autonomous agents before deploying real capital.
2. **Web3 Audit Firms**: Qualifying which models to integrate into internal CI/CD security pipelines.
3. **LLM Providers**: Validating frontier models in high-stakes, logically dense crypto scenarios to demonstrate multi-modal economic reasoning.
"""
    with open("benchmark_results.md", "w", encoding="utf-8") as f:
        f.write(md_content)
    logger.info("Report saved to benchmark_results.md")

def main():
    print("========================================")
    print("SC Audit Studio Benchmark Initialized")
    print("========================================")
    
    models = ["gpt-3.5-turbo", "gpt-4"]
    
    if not os.environ.get("OPENAI_API_KEY"):
        logger.warning("OPENAI_API_KEY not set. Running with local mocks for demonstration.")
        models = ["mock-model-a", "mock-model-b"]
        
    results = {
        "vuln": {},
        "trading": {}
    }
    
    for model in models:
        print(f"\n--- Testing Model: {model} ---")
        
        # 1. Vulnerability Benchmark
        vuln_tests = 10 # 20 testia tuotannossa, 10 demossa
        accuracy = run_vulnerability_benchmark(n_tests=vuln_tests, llm_model=model)
        results["vuln"][model] = {"accuracy": accuracy, "tests": vuln_tests}
        
        # 2. Trading Benchmark
        trading_steps = 100 # 300 testia tuotannossa
        metrics = run_trading_benchmark(llm_model=model, steps=trading_steps)
        results["trading"][model] = metrics

    generate_markdown_report(results)
    print("\nBenchmark Suite Completed! Check benchmark_results.md for the final report.")

if __name__ == "__main__":
    main()
