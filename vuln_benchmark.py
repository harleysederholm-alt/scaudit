import os
import hashlib
import random
import csv
import json
import logging
from typing import Tuple, Dict, Any, List
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

VULN_TEMPLATES = {
    "reentrancy": """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Vault {
    mapping(address => uint256) public balances;

    function deposit() public payable {
        balances[msg.sender] += msg.value;
    }

    function withdraw() public {
        uint256 bal = balances[msg.sender];
        require(bal > 0, "Insufficient balance");
        (bool success, ) = msg.sender.call{value: bal}("");
        require(success, "Transfer failed");
        balances[msg.sender] = 0;
    }
}
""",
    "access_control": """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Vault {
    address public owner;
    mapping(address => uint256) public balances;

    constructor() {
        owner = msg.sender;
    }

    function deposit() public payable {
        balances[msg.sender] += msg.value;
    }

    // Vulnerability: Missing onlyOwner modifier
    function emergencyWithdrawAll() public {
        payable(msg.sender).transfer(address(this).balance);
    }
}
""",
    "arithmetic_overflow": """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Token {
    mapping(address => uint256) public balances;

    constructor() {
        balances[msg.sender] = 10000;
    }

    function transfer(address to, uint256 amount) public {
        unchecked {
            // Vulnerability: Unchecked arithmetic can underflow
            require(balances[msg.sender] - amount >= 0, "Not enough balance");
            balances[msg.sender] -= amount;
            balances[to] += amount;
        }
    }
}
""",
    "tx_origin": """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Wallet {
    address public owner;

    constructor() {
        owner = msg.sender;
    }

    receive() external payable {}

    function withdraw(uint256 amount) public {
        // Vulnerability: Using tx.origin for authentication
        require(tx.origin == owner, "Not owner");
        payable(msg.sender).transfer(amount);
    }
}
""",
    "timestamp_dependence": """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Lottery {
    function play() public payable {
        require(msg.value == 1 ether, "Must send 1 ether");
        // Vulnerability: Using block.timestamp for randomness
        if (block.timestamp % 2 == 0) {
            payable(msg.sender).transfer(2 ether);
        }
    }
    
    receive() external payable {}
}
"""
}

def generate_vulnerable_contract(vuln_type: str) -> Tuple[str, str, str]:
    if vuln_type not in VULN_TEMPLATES:
        raise ValueError(f"Unknown vulnerability type: {vuln_type}")
    
    source_code = VULN_TEMPLATES[vuln_type]
    
    # Lisätään satunnaisuutta estämään mallin ylisovitus
    salt = f"// Salt: {random.randint(1000, 9999)}\n"
    source_code = source_code + salt
    
    unique_id = hashlib.sha256(source_code.encode('utf-8')).hexdigest()
    return source_code, vuln_type, unique_id

def query_llm_for_vulnerabilities(contract_code: str, llm_model: str = "gpt-4") -> str:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key or OpenAI is None:
        logger.warning("No OPENAI_API_KEY or openai package found, using mock LLM response.")
        return "mock response mentioning reentrancy or access_control depending on randomness"
    
    try:
        client = OpenAI(api_key=api_key)
        prompt = f"Find all security vulnerabilities in this Solidity smart contract. List each vulnerability with severity (high/medium/low) and a fix. Contract:\n{contract_code}"
        
        response = client.chat.completions.create(
            model=llm_model,
            messages=[
                {"role": "system", "content": "You are a top-tier Web3 security auditor."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"API Error: {e}")
        return ""

def score_vulnerability_detection(llm_response: str, true_vuln_type: str) -> float:
    response_lower = llm_response.lower()
    
    keywords = {
        "reentrancy": {
            "exact": ["reentrancy", "re-entrancy"],
            "partial": ["recursive call", "call after update", "checks-effects-interactions"]
        },
        "access_control": {
            "exact": ["access control", "missing modifier", "unprotected", "onlyowner"],
            "partial": ["anyone can call", "unauthorized"]
        },
        "arithmetic_overflow": {
            "exact": ["overflow", "underflow", "unchecked"],
            "partial": ["math error", "wrap around"]
        },
        "tx_origin": {
            "exact": ["tx.origin", "phishing"],
            "partial": ["origin instead of msg.sender", "authentication"]
        },
        "timestamp_dependence": {
            "exact": ["timestamp", "block.timestamp"],
            "partial": ["weak randomness", "miner manipulation"]
        }
    }
    
    if true_vuln_type not in keywords:
        return 0.0
        
    exact_matches = keywords[true_vuln_type]["exact"]
    partial_matches = keywords[true_vuln_type]["partial"]
    
    if any(kw in response_lower for kw in exact_matches):
        return 1.0
    elif any(kw in response_lower for kw in partial_matches):
        return 0.5
    
    return 0.0

def run_vulnerability_benchmark(n_tests: int = 20, llm_model: str = "gpt-4") -> float:
    logger.info(f"Starting Vulnerability Benchmark with {n_tests} tests using {llm_model}")
    vuln_types = list(VULN_TEMPLATES.keys())
    results = []
    total_score = 0.0
    
    for i in range(n_tests):
        vuln = random.choice(vuln_types)
        code, true_vuln, uid = generate_vulnerable_contract(vuln)
        
        logger.info(f"Test {i+1}/{n_tests}: Testing {true_vuln} (ID: {uid[:8]})")
        
        response = query_llm_for_vulnerabilities(code, llm_model)
        
        if not os.environ.get("OPENAI_API_KEY"):
            # Mock evaluation for demonstration if API is missing
            score = 1.0 if random.random() > 0.3 else 0.0
            response = f"Mocked correct answer for {true_vuln}" if score == 1.0 else "Mocked wrong answer"
        else:
            score = score_vulnerability_detection(response, true_vuln)
        
        total_score += score
        results.append({
            "test_id": uid,
            "true_vulnerability": true_vuln,
            "score": score,
            "llm_response_snippet": response[:100].replace('\\n', ' ') + "..."
        })
        
    accuracy = (total_score / n_tests) * 100
    logger.info(f"Vulnerability detection accuracy: {accuracy:.2f}% (N={n_tests})")
    
    os.makedirs("results", exist_ok=True)
    csv_file = f"results/vuln_benchmark_results_{llm_model}.csv"
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["test_id", "true_vulnerability", "score", "llm_response_snippet"])
        writer.writeheader()
        writer.writerows(results)
    logger.info(f"Results saved to {csv_file}")
    
    return accuracy

if __name__ == "__main__":
    run_vulnerability_benchmark(5, "gpt-3.5-turbo")
