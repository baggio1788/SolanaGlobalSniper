# 🚀 Solana Global Sniper & Monitor (Pump.fun + Meteora)

A high-performance, GUI-based trading bot and monitor for the Solana blockchain. This tool tracks new token launches on **Pump.fun** and **Meteora** in real-time, analyzes developer wallets for "rug pull" risks, and allows for instant sniping with Stop-Loss/Take-Profit automation.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Solana](https://img.shields.io/badge/Solana-Mainnet-green)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)

## ✨ Key Features

* **Real-Time Monitoring:**
    * **Pump.fun:** Websocket connection for live trade updates.
    * **Meteora:** RPC polling for genesis dev tracking and Jupiter-based price feeds.
    * **Movers Filter:** Scrapes top movers to find trending tokens instantly.
* **Safety First (Anti-Rug):**
    * **Dev Check:** Automatically scans the Creator's wallet history for suspicious bot activity (Jito, MEV bundles) and checks their SOL balance.
    * **Visual Indicators:** 🟢 Clean / 🔴 Bot Heavy / 💀 Rugged.
* **Trading Engine:**
    * **Multi-DEX Support:** Routes trades via **PumpPortal** (for bonding curves) and **Jupiter/Raydium** (for graduated tokens).
    * **Automated Exits:** Built-in **Stop-Loss** and **Take-Profit** (Multiplier) logic.
* **GUI Interface:**
    * Dark mode interface built with `tkinter`.
    * One-click Buy/Sell buttons.
    * Direct links to Solscan and Token pages.

## 🛠️ Installation & Setup

### Prerequisites
* Python 3.12 not higher!
* A Solana Wallet (Private Key required).
* (Optional) Jupiter API Key for faster Raydium routing.

### 1. Clone the Repository
```bash
git clone https://github.com/baggio1788/SolanaGlobalSniper.git
cd SolanaGlobalSniper
```
2. Install Dependencies
Install the required Python libraries using pip:

```bash
pip install -r requirements.txt
```
Note: If you don't have a requirements.txt, install these manually:

```bash
pip install solana solders requests websockets base58 borsh-construct construct pyperclip urllib3
```
🚀 How to Run
Simply execute the script:

```bash
python snipersolanaglobal.py
```
GUI Usage Guide
Connect Wallet: Paste your Private Key (Base58) into the top input field and click CONNECT WALLET.

Security Note: Keys are stored in RAM only and never sent to external servers.

Settings:

Amount: SOL to spend per trade.

Exit (X): Target multiplier (e.g., 2 for 2x profit).

Stop Loss (%): e.g., -30.

Filters: Set Min/Max Age and Min Market Cap to filter the token list.

Start Sniping:

Watch the list populate with new tokens.

Wait for the STATUS to verify the token (e.g., ✅ TRADEABLE).

Click 🚀 BUY.

The bot will automatically manage the trade based on your Stop-Loss/Exit settings.

🧠 Code Architecture
This project is divided into several asynchronous modules:

1. Core Logic (WalletManager)
File: snipersolanaglobal.py (Class: WalletManager)

Function: Handles connection to Solana RPC.

Key Methods:

buy_token: Routes transactions to PumpPortal or Jupiter based on token status (Graduated vs. Bonding Curve).

sell_token: Handles exits with slippage protection.

send_dev_fee: Automatically calculates and sends the protocol fee.

2. Monitoring Loops
pumportal_subscriber: Connects to wss://pumpportal.fun to get live trade data and detect when a coin completes the bonding curve.

meteora_listener_loop: Polls RPC for new Meteora pools and analyzes initial liquidity.

movers_fast_start_checker: Scrapes the "Top Movers" API to populate the list with trending coins that meet filter criteria.

3. Analysis & Safety
analyze_dev_since_launch: Uses solders and requests to fetch the developer's transaction history. It compares signatures against a KNOWN_ENTITIES list (Jito, MEV bots) to flag "bundled" launches.

4. User Interface
StableSniperGUI: Built with tkinter. It runs on a separate thread to keep the GUI responsive while asyncio loops handle the blockchain data in the background.

⚠️ Disclaimer
Educational Purposes Only. Trading cryptocurrency, especially meme coins on Solana, carries high risk. You can lose your entire capital. The developer is not responsible for any financial losses, failed transactions, or API errors. Use at your own risk.

📄 License
Copyright © 2024. All Rights Reserved. Modification, redistribution, or removal of the developer fee logic is strictly prohibited without explicit permission.
