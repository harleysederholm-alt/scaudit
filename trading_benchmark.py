import os
import json
import random
import logging
import math
from typing import Dict, Any, List, Tuple
try:
    import numpy as np
except ImportError:
    np = None
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class TradingEnv:
    def __init__(self, n_steps: int = 1000):
        if np is None:
            raise ImportError("numpy is required for TradingEnv")
            
        np.random.seed(random.randint(0, 10000))
        # Generoidaan mock markkinadata: satunnaiskävely + volatiliteetti
        returns = np.random.normal(0.0001, 0.02, n_steps)
        self.prices = 100 * np.exp(np.cumsum(returns))
        self.prices = self.prices.tolist()
        
        self.current_step = 50 # Aloitetaan historiasta
        self.n_steps = len(self.prices)
        
        self.balance = 10000.0 # USDC
        self.holdings = 0.0    # BTC
        self.total_value_history = []
        self._record_value()
        
    def _record_value(self):
        current_price = self.prices[self.current_step]
        total_value = self.balance + (self.holdings * current_price)
        self.total_value_history.append(total_value)
        
    def get_observation(self) -> Dict[str, Any]:
        current_price = self.prices[self.current_step]
        total_value = self.balance + (self.holdings * current_price)
        return {
            "price": current_price,
            "prices": self.prices[self.current_step - 50: self.current_step + 1],
            "balance": self.balance,
            "holdings": self.holdings,
            "total_value": total_value
        }
        
    def step(self, action: str, percentage: float) -> Tuple[Dict[str, Any], float, bool]:
        """
        action: "buy", "sell", "hold"
        percentage: 0-100
        """
        current_price = self.prices[self.current_step]
        old_value = self.balance + (self.holdings * current_price)
        
        percentage = max(0.0, min(100.0, float(percentage)))
        fraction = percentage / 100.0
        
        if action == "buy" and self.balance > 0:
            invest_amount = self.balance * fraction
            purchased_asset = invest_amount / current_price
            self.balance -= invest_amount
            self.holdings += purchased_asset
        elif action == "sell" and self.holdings > 0:
            sell_amount = self.holdings * fraction
            received_usdc = sell_amount * current_price
            self.holdings -= sell_amount
            self.balance += received_usdc
            
        self.current_step += 1
        done = self.current_step >= self.n_steps - 1
        
        new_price = self.prices[self.current_step]
        new_value = self.balance + (self.holdings * new_price)
        
        self._record_value()
        reward = (new_value - old_value) / old_value if old_value > 0 else 0
        
        return self.get_observation(), reward, done

def llm_trading_decision(observation: Dict[str, Any], llm_model: str = "gpt-3.5-turbo") -> Dict[str, Any]:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key or OpenAI is None:
        # Mock decision ilman API-avainta
        actions = ["buy", "sell", "hold"]
        return {"action": random.choice(actions), "percentage": random.uniform(10, 50)}
        
    try:
        client = OpenAI(api_key=api_key)
        recent_prices = [round(p, 2) for p in observation["prices"][-10:]]
        
        prompt = f"""You are a crypto trading agent.
Current price (last): {observation['price']:.2f}.
Portfolio: {observation['balance']:.2f} USDC, {observation['holdings']:.4f} BTC.
Recent prices: {recent_prices}.
Recommend: buy/sell/hold and percentage (0-100). Respond JSON only. Format: {{"action": "buy", "percentage": 20}}"""

        response = client.chat.completions.create(
            model=llm_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=50,
            response_format={ "type": "json_object" }
        )
        
        result_text = response.choices[0].message.content
        decision = json.loads(result_text)
        
        action = str(decision.get("action", "hold")).lower()
        if action not in ["buy", "sell", "hold"]:
            action = "hold"
        percentage = float(decision.get("percentage", 0))
        return {"action": action, "percentage": percentage}
        
    except Exception as e:
        logger.error(f"API/Parse Error: {e}")
        return {"action": "hold", "percentage": 0}

def calculate_metrics(value_history: List[float]) -> Dict[str, float]:
    if not value_history or np is None:
        return {"sharpe": 0.0, "max_dd": 0.0, "win_rate": 0.0, "total_return": 0.0}
        
    returns = np.diff(value_history) / value_history[:-1]
    
    # Sharpe Ratio (annualisoitu, 252 paivaa)
    mean_return = np.mean(returns)
    std_return = np.std(returns)
    sharpe = (mean_return / std_return) * np.sqrt(252) if std_return > 0 else 0
    
    # Maximum Drawdown
    peak = value_history[0]
    max_dd = 0.0
    for value in value_history:
        if value > peak:
            peak = value
        dd = (peak - value) / peak
        if dd > max_dd:
            max_dd = dd
            
    # Win Rate
    wins = np.sum(returns > 0)
    win_rate = wins / len(returns) if len(returns) > 0 else 0
    
    # Total Return
    total_return = (value_history[-1] - value_history[0]) / value_history[0]
    
    return {
        "sharpe": float(sharpe),
        "max_dd": float(max_dd * 100),
        "win_rate": float(win_rate * 100),
        "total_return": float(total_return * 100)
    }

def run_trading_benchmark(llm_model: str = "gpt-3.5-turbo", steps: int = 500) -> Dict[str, Any]:
    logger.info(f"Starting Trading Benchmark with {steps} steps using {llm_model}")
    env = TradingEnv(n_steps=steps + 50)
    
    obs = env.get_observation()
    done = False
    
    for i in range(steps):
        if done:
            break
            
        decision = llm_trading_decision(obs, llm_model)
        obs, reward, done = env.step(decision["action"], decision["percentage"])
        
        if (i + 1) % 50 == 0:
            logger.info(f"Step {i+1}/{steps} | Portfolio Value: {obs['total_value']:.2f}")
            
    metrics = calculate_metrics(env.total_value_history)
    logger.info(f"Sharpe: {metrics['sharpe']:.2f}, MaxDD: {metrics['max_dd']:.2f}%, WinRate: {metrics['win_rate']:.2f}%")
    return metrics

if __name__ == "__main__":
    run_trading_benchmark("gpt-3.5-turbo", steps=100)
