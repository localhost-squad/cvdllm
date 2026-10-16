import eel
import needle
import json
import hashlib
import os
from dotenv import load_dotenv
from tpm import sign_hash, verify_signature

load_dotenv()

# Initialize Eel with the web folder
eel.init('web')

BANK_STATE = {
    "checking_balance": 25000.00,
    "savings_balance": 50000.00,
    "portfolio": {
        "AAPL": {"shares": 10},
        "SSNLF": {"shares": 25},
        "LNVGY": {"shares": 50},
        "HPQ": {"shares": 15}
    }
}

@needle.tool
def check_balance() -> dict:
    return {
        "checking_balance": BANK_STATE["checking_balance"],
        "savings_balance": BANK_STATE["savings_balance"],
        "portfolio": {ticker: data["shares"] for ticker, data in BANK_STATE["portfolio"].items()}
    }

@needle.tool
def transfer_money(source: str, target: str, amount: float) -> dict:
    global BANK_STATE
    source, target = source.lower(), target.lower()
    if source not in ["checking", "savings"] or target not in ["checking", "savings"] or source == target:
        return {"status": "failed", "reason": "Invalid account types."}
    if BANK_STATE[f"{source}_balance"] < amount:
        return {"status": "failed", "reason": "Insufficient funds."}
    BANK_STATE[f"{source}_balance"] -= amount
    BANK_STATE[f"{target}_balance"] += amount
    return {"status": "success", "transferred": amount, "from": source, "to": target}

@needle.tool
def buy_stocks(ticker: str, shares: int, price_per_share: float) -> dict:
    global BANK_STATE
    ticker = ticker.upper()
    if ticker not in BANK_STATE["portfolio"]:
        return {"status": "failed", "reason": "Invalid ticker."}
    cost = shares * price_per_share
    if BANK_STATE["checking_balance"] < cost:
        return {"status": "failed", "reason": "Insufficient checking balance."}
    BANK_STATE["checking_balance"] -= cost
    BANK_STATE["portfolio"][ticker]["shares"] += shares
    return {"status": "success", "ticker": ticker, "shares_bought": shares, "total_cost": cost}

@needle.tool
def sell_stocks(ticker: str, shares: int, price_per_share: float) -> dict:
    global BANK_STATE
    ticker = ticker.upper()
    if ticker not in BANK_STATE["portfolio"] or BANK_STATE["portfolio"][ticker]["shares"] < shares:
        return {"status": "failed", "reason": "Not enough shares."}
    revenue = shares * price_per_share
    BANK_STATE["portfolio"][ticker]["shares"] -= shares
    BANK_STATE["checking_balance"] += revenue
    return {"status": "success", "ticker": ticker, "shares_sold": shares, "revenue": revenue}

agent = needle.Needle(tools=[check_balance, transfer_money, buy_stocks, sell_stocks])

@eel.expose
def get_portfolio_state():
    return {
        "checking": BANK_STATE["checking_balance"],
        "savings": BANK_STATE["savings_balance"],
        "portfolio": {t: d["shares"] for t, d in BANK_STATE["portfolio"].items()}
    }

@eel.expose
def run_agent_prompt(prompt):
    try:
        agent.reset()
        response = agent.run(prompt)
        reply = response.get("reasoning", "Action processed.")
        if response.get("results"):
            reply += f"\n\nResult Details:\n{json.dumps(response['results'], indent=2)}"

        semantic_data = {
            "success": response.get("success"),
            "function_calls": response.get("function_calls"),
            "results": response.get("results")
        }
        json_str = json.dumps(semantic_data, sort_keys=True)
        h = hashlib.sha256(json_str.encode('utf-8')).hexdigest()

        addr = os.getenv("TPM_NVRAM_ADDRESS", "0x81010002")
        tcti = os.getenv("TPM2TOOLS_TCTI", "device:/dev/tpmrm0")
        sig = sign_hash(addr, tcti, h)

        return {"reply": reply, "hash": h, "signature": sig}
    except Exception as e:
        return {"reply": f"Error: {str(e)}", "hash": "", "signature": ""}

@eel.expose
def verify_tpm_signature(h, sig):
    pub_key = os.getenv("TPM_PUBLIC_KEY")
    if not pub_key: return "false"
    return verify_signature(h, sig, pub_key)

def main():
    eel.start('index.html', size=(1280, 800))

if __name__ == "__main__":
    main()