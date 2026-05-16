# SC Audit Studio - LLM Benchmark Report

## 1. Smart Contract Vulnerability Detection
| Model | Accuracy (%) | Tests |
|-------|--------------|-------|
| mock-model-a | 60.00% | 10 |
| mock-model-b | 100.00% | 10 |

## 2. Dynamic Trading Agent Performance (Out-of-Sample)
| Model | Sharpe Ratio | Max Drawdown | Win Rate | Total Return |
|-------|--------------|--------------|----------|--------------|
| mock-model-a | 0.57 | 12.58% | 53.54% | 3.63% |
| mock-model-b | -0.40 | 9.97% | 52.53% | -3.00% |

## Methodology & Anti-Overfitting
- **Vulnerability Benchmark**: Generates synthetic, novel smart contracts dynamically using randomness to bypass exact string-matching memorization in LLMs.
- **Trading Benchmark**: Uses dynamically generated random walk market conditions, ensuring the model reacts to out-of-sample data, simulating real economic risk environments.

## Economic Rationale
This benchmark is commercially valuable for:
1. **Hedge Funds & Prop Trading**: Evaluating the reliability of autonomous agents before deploying real capital.
2. **Web3 Audit Firms**: Qualifying which models to integrate into internal CI/CD security pipelines.
3. **LLM Providers**: Validating frontier models in high-stakes, logically dense crypto scenarios to demonstrate multi-modal economic reasoning.
