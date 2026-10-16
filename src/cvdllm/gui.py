import sys
import json
import hashlib
import os
from dotenv import load_dotenv
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QLineEdit, QTextEdit, QPushButton, QSplitter, QMessageBox, QGroupBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

import needle
from tpm import sign_hash, verify_signature

load_dotenv()

# --- Mock Financial & Stock State ---
BANK_STATE = {
    "checking_balance": 25000.00,
    "savings_balance": 50000.00,
    "portfolio": {
        "AAPL": {"shares": 10, "name": "Apple"},
        "SSNLF": {"shares": 25, "name": "Samsung"},
        "LNVGY": {"shares": 50, "name": "Lenovo"},
        "HPQ": {"shares": 15, "name": "HP"}
    }
}

# --- Define the 4 Banking Tools ---
@needle.tool
def check_balance() -> dict:
    """Check balances and stock portfolio holdings."""
    return {
        "checking_balance": BANK_STATE["checking_balance"],
        "savings_balance": BANK_STATE["savings_balance"],
        "portfolio": {ticker: data["shares"] for ticker, data in BANK_STATE["portfolio"].items()}
    }

@needle.tool
def transfer_money(source: str, target: str, amount: float) -> dict:
    """Transfer money between checking and savings accounts."""
    global BANK_STATE
    source = source.lower()
    target = target.lower()
    if source not in ["checking", "savings"] or target not in ["checking", "savings"]:
        return {"status": "failed", "reason": "Invalid account type."}
    if source == target:
        return {"status": "failed", "reason": "Source and target must be different."}
    
    if BANK_STATE[f"{source}_balance"] < amount:
        return {"status": "failed", "reason": f"Insufficient funds in {source}."}
    
    BANK_STATE[f"{source}_balance"] -= amount
    BANK_STATE[f"{target}_balance"] += amount
    return {"status": "success", "transferred": amount, "from": source, "to": target, "checking": BANK_STATE["checking_balance"], "savings": BANK_STATE["savings_balance"]}

@needle.tool
def buy_stocks(ticker: str, shares: int, price_per_share: float) -> dict:
    """Buy stocks (AAPL, SSNLF, LNVGY, HPQ)."""
    global BANK_STATE
    ticker = ticker.upper()
    if ticker not in BANK_STATE["portfolio"]:
        return {"status": "failed", "reason": f"Invalid ticker '{ticker}'."}
    
    cost = shares * price_per_share
    if BANK_STATE["checking_balance"] < cost:
        return {"status": "failed", "reason": "Insufficient checking balance."}
    
    BANK_STATE["checking_balance"] -= cost
    BANK_STATE["portfolio"][ticker]["shares"] += shares
    return {"status": "success", "ticker": ticker, "shares_bought": shares, "total_cost": cost, "checking": BANK_STATE["checking_balance"]}

@needle.tool
def sell_stocks(ticker: str, shares: int, price_per_share: float) -> dict:
    """Sell stocks (AAPL, SSNLF, LNVGY, HPQ)."""
    global BANK_STATE
    ticker = ticker.upper()
    if ticker not in BANK_STATE["portfolio"] or BANK_STATE["portfolio"][ticker]["shares"] < shares:
        return {"status": "failed", "reason": "Not enough shares to sell."}
    
    revenue = shares * price_per_share
    BANK_STATE["portfolio"][ticker]["shares"] -= shares
    BANK_STATE["checking_balance"] += revenue
    return {"status": "success", "ticker": ticker, "shares_sold": shares, "revenue": revenue, "checking": BANK_STATE["checking_balance"]}

agent = needle.Needle(tools=[check_balance, transfer_money, buy_stocks, sell_stocks])


class NativeBankingApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CVDLLM Secure Autonomous Banking & TPM Verification")
        self.resize(1280, 800)

        self.latest_hash = ""
        self.latest_signature = ""
        self.last_full_response = {}

        agent.reset()
        self.init_ui()
        self.update_portfolio_view()

    def init_ui(self):
        # Main widget & layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # Splitter for two clean panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # --- Left Panel: Chatbot Interface ---
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)

        chat_title = QLabel("💬 Secure Autonomous Banking Assistant")
        chat_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        left_layout.addWidget(chat_title)

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setFont(QFont("Segoe UI", 11))
        self.chat_display.setStyleSheet("background-color: #F8F9FA; border: 1px solid #DADCE0; border-radius: 8px; padding: 10px;")
        left_layout.addWidget(self.chat_display)

        # Input Row
        input_layout = QHBoxLayout()
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Type a banking command or prompt...")
        self.user_input.setFont(QFont("Segoe UI", 11))
        self.user_input.setStyleSheet("padding: 8px; border: 1px solid #DADCE0; border-radius: 6px;")
        self.user_input.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.user_input)

        send_btn = QPushButton("Send")
        send_btn.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        send_btn.setStyleSheet("background-color: #1A73E8; color: white; padding: 8px 16px; border-radius: 6px;")
        send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(send_btn)

        json_btn = QPushButton("Raw JSON")
        json_btn.setFont(QFont("Segoe UI", 11))
        json_btn.setStyleSheet("background-color: #E8EAED; color: #3C4043; padding: 8px 12px; border-radius: 6px;")
        json_btn.clicked.connect(self.reveal_json)
        input_layout.addWidget(json_btn)

        left_layout.addLayout(input_layout)
        splitter.addWidget(left_container)

        # --- Right Panel: Portfolio & TPM Verification Sandbox ---
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # Portfolio Box
        right_layout.addWidget(QLabel("📊 Live Account & Portfolio", font=QFont("Segoe UI", 12, QFont.Weight.Bold)))
        self.portfolio_box = QTextEdit()
        self.portfolio_box.setReadOnly(True)
        self.portfolio_box.setMaximumHeight(140)
        self.portfolio_box.setFont(QFont("Consolas", 10))
        self.portfolio_box.setStyleSheet("background-color: #F8F9FA; border: 1px solid #DADCE0; border-radius: 8px;")
        right_layout.addWidget(self.portfolio_box)

        # TPM Sandbox
        right_layout.addWidget(QLabel("🔒 TPM Hardware Security & Audit", font=QFont("Segoe UI", 12, QFont.Weight.Bold)))
        
        right_layout.addWidget(QLabel("Latest SHA-256 Hash:", font=QFont("Segoe UI", 10, QFont.Weight.Bold)))
        self.hash_box = QTextEdit()
        self.hash_box.setReadOnly(True)
        self.hash_box.setMaximumHeight(50)
        self.hash_box.setFont(QFont("Consolas", 10))
        self.hash_box.setStyleSheet("background-color: #F8F9FA; border: 1px solid #DADCE0; border-radius: 6px;")
        right_layout.addWidget(self.hash_box)

        right_layout.addWidget(QLabel("TPM Signature (Editable for Tamper Test):", font=QFont("Segoe UI", 10, QFont.Weight.Bold)))
        self.sig_box = QTextEdit()
        self.sig_box.setMaximumHeight(90)
        self.sig_box.setFont(QFont("Consolas", 10))
        self.sig_box.setStyleSheet("background-color: #FFFFFF; border: 1px solid #DADCE0; border-radius: 6px;")
        right_layout.addWidget(self.sig_box)

        verify_btn = QPushButton("Verify Signature Against TPM")
        verify_btn.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        verify_btn.setStyleSheet("background-color: #1E8E3E; color: white; padding: 10px; border-radius: 6px;")
        verify_btn.clicked.connect(self.verify_signature)
        right_layout.addWidget(verify_btn)

        self.status_label = QLabel("Status: Ready")
        self.status_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.status_label.setStyleSheet("color: #5F6368;")
        right_layout.addWidget(self.status_label)

        # Quick Prompts
        right_layout.addWidget(QLabel("Quick Prompt Examples:", font=QFont("Segoe UI", 10, QFont.Weight.Bold)))
        prompts = [
            "What are my account balances and stocks?",
            "Transfer 1000 from checking to savings",
            "Buy 5 shares of AAPL at 180.50 each",
            "Sell 2 shares of SSNLF at 65.00"
        ]
        for p in prompts:
            btn = QPushButton(p)
            btn.setFont(QFont("Segoe UI", 10))
            btn.setStyleSheet("background-color: #F1F3F4; text-align: left; padding: 6px 10px; border-radius: 4px;")
            btn.clicked.connect(lambda checked, text=p: self.user_input.setText(text))
            right_layout.addWidget(btn)

        right_layout.addStretch()
        splitter.addWidget(right_container)
        splitter.setSizes([750, 450])

    def update_portfolio_view(self):
        p = BANK_STATE["portfolio"]
        text = (
            f"Checking Account : ${BANK_STATE['checking_balance']:,.2f}\n"
            f"Savings Account  : ${BANK_STATE['savings_balance']:,.2f}\n"
            f"----------------------------------------\n"
            f" Apple (AAPL)   : {p['AAPL']['shares']} shares\n"
            f"🅂 Samsung(SSNLF) : {p['SSNLF']['shares']} shares\n"
            f"🅛 Lenovo(LNVGY)  : {p['LNVGY']['shares']} shares\n"
            f"🄗 HP (HPQ)       : {p['HPQ']['shares']} shares"
        )
        self.portfolio_box.setText(text)

    def append_chat(self, sender, text):
        color = "#1A73E8" if sender == "You" else "#202124"
        self.chat_display.append(f"<b>{sender}:</b><br>{text.replace('\n', '<br>')}<br><br>")

    def send_message(self):
        prompt = self.user_input.text().strip()
        if not prompt:
            return
        
        self.user_input.clear()
        self.append_chat("You", prompt)

        try:
            response = agent.run(prompt)
            self.last_full_response = response

            reply_text = response.get("reasoning", "Action processed.")
            if response.get("results"):
                reply_text += f"\n\nResult Details:\n{json.dumps(response['results'], indent=2)}"

            self.append_chat("Assistant", reply_text)
            self.update_portfolio_view()

            # Hash and Sign via TPM
            semantic_data = {
                "success": response.get("success"),
                "function_calls": response.get("function_calls"),
                "results": response.get("results")
            }
            json_str = json.dumps(semantic_data, sort_keys=True)
            self.latest_hash = hashlib.sha256(json_str.encode('utf-8')).hexdigest()

            addr = os.getenv("TPM_NVRAM_ADDRESS", "0x81010002")
            tcti = os.getenv("TPM2TOOLS_TCTI", "device:/dev/tpmrm0")
            self.latest_signature = sign_hash(addr, tcti, self.latest_hash)

            self.hash_box.setText(self.latest_hash)
            self.sig_box.setText(self.latest_signature)
            self.status_label.setText("Status: 🔒 Signed & Verified by TPM")
            self.status_label.setStyleSheet("color: #137333;")

        except Exception as ex:
            QMessageBox.critical(self, "Execution Error", str(ex))

    def reveal_json(self):
        if not self.last_full_response:
            QMessageBox.information(self, "Info", "No transaction output recorded yet.")
            return
        
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Raw JSON Payload")
        dlg.setText(json.dumps(self.last_full_response, indent=2))
        dlg.exec()

    def verify_signature(self):
        if not self.latest_hash:
            QMessageBox.warning(self, "Warning", "No active transaction signature found to verify.")
            return

        current_sig = self.sig_box.toPlainText().strip()
        pub_key = os.getenv("TPM_PUBLIC_KEY")

        if not pub_key:
            QMessageBox.critical(self, "Error", "TPM_PUBLIC_KEY missing in .env file!")
            return

        try:
            result = verify_signature(self.latest_hash, current_sig, pub_key)
            if result == "true":
                self.status_label.setText("Status: 🟢 VALID (TPM Verified)")
                self.status_label.setStyleSheet("color: #137333;")
            else:
                self.status_label.setText("Status: 🔴 TAMPERED / INVALID")
                self.status_label.setStyleSheet("color: #C5221F;")
        except Exception as ex:
            self.status_label.setText(f"Status: ❌ Error: {ex}")
            self.status_label.setStyleSheet("color: #C5221F;")


def main():
    app = QApplication(sys.argv)
    window = NativeBankingApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()