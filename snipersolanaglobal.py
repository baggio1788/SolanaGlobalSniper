import asyncio
import json
import websockets
import base64
import base58
import requests
import time
import os
import sys
import threading
import webbrowser
from functools import partial
import tkinter as tk
from tkinter import ttk
import random

# --- ADATSTRUKTÚRÁK ---
from borsh_construct import CStruct
from construct import Bytes

# --- SOLANA IMPORTOK ---
from solders.keypair import Keypair
from solders.transaction import VersionedTransaction
from solders.message import to_bytes_versioned
from solana.rpc.async_api import AsyncClient
from solana.rpc.types import TxOpts
from solana.rpc.commitment import Confirmed
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
# --- SOLANA IMPORTOK KIEGÉSZÍTÉSE ---
from solders.pubkey import Pubkey 

# --- STABIL KAPCSOLAT 
def create_robust_session():
    session = requests.Session()
    # Ha hiba van, 3x újrapróbálja automatikusan, nem dob hibát a loopnak
    retry = Retry(total=3, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(pool_connections=20, pool_maxsize=20, max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

# Létrehozzuk a globális session-t
session = create_robust_session()

session.headers.update({"Content-Type": "application/json", "User-Agent": "PumpSniper/1.0"})

#session = requests.Session()

# --- OPCIONÁLIS IMPORT ---
try:
    import pyperclip
except ImportError:
    pyperclip = None

# --- KONFIGURÁCIÓ ---
RPC_HTTPS = "https://solana-rpc.publicnode.com"
PUMPORTAL_WSS = "wss://pumpportal.fun/api/data"
PUMPORTAL_TRADE_API = "https://pumpportal.fun/api/trade-local"
#PUMPFUN_MINT_AUTHORITY = "TSLvdd1pWpHVjahSpsvCXUbgwsL3JAcvokwaKt1eokM"
MAX_ACTIVE_SLOTS = 5
METEORA_PROGRAM_ID = "FhVo3mqL8PW5pH5U2CN4XE33DokiyZnUwuGpH2hmHLuM"
WSOL_MINT = "So11111111111111111111111111111111111111112"
METAPLEX_PROGRAM_ID = Pubkey.from_string("metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s")

JUPITER_API_KEY = ""

PRIVATE_KEY_STR = ""

# --- JUTALÉK BEÁLLÍTÁSA ---
MY_DEV_WALLET = "D9DThbgTr6iG98GfP1Kn5mzBEKgTnotCjKAvAheq96FF"
#DEV_FEE_PERCENT = 0.0050 # 0.50%

# --- README SZÖVEG (BEÉGETVE AZ EXE MIATT) ---
README_TEXT = """
==============================================================================
             🚀 PUMP.FUN SNIPER & MONITOR TOOL - USER MANUAL 🚀
==============================================================================

Thank you for using the Pump.fun Sniper Monitor. This tool is designed to scan 
new token launches on the Solana network, filter out spam, analyze developer 
wallets for previous rug-pulls, and allow fast trading execution.

IMPORTANT: This software runs as a standalone application (.exe). 
No installation or Python setup is required.

==============================================================================
                           1. INITIAL SETUP
==============================================================================

Before you start, you need two things:

A) SOLANA PRIVATE KEY (Your Wallet)
   - You need a Solana wallet (like Phantom or Solflare) with some SOL in it.
   - Export your Private Key from the wallet settings.
   - Format: It accepts both Base58 string (standard) or JSON Array format.
   
   👉 HOW TO GET IT: Open Phantom -> Settings -> Developer Settings -> 
      Export Private Key.

B) JUPITER API KEY (Optional but Recommended)
   - The bot uses Jupiter API for buying/selling on Raydium (after graduation).
   - Without this, Raydium trades might be slower or rate-limited.
   
   👉 HOW TO GET IT: 
      1. Go to: https://station.jup.ag/
      2. Sign in with your wallet.
      3. Navigate to "API V6" or "Auth" section to generate a free API Token.

==============================================================================
                        2. INTERFACE OVERVIEW
==============================================================================

The main window is divided into columns monitoring new tokens:

[SYMBOL] ..... Ticker of the token.
[MC] ......... Current Market Cap in USD.
[ATH] ........ All-Time High Market Cap since monitoring started.
[TIME] ....... Seconds elapsed since the token launched.
[BOTS] ....... Detected sniper bots involved in the early trades.
[DEV] ........ The Creator's wallet address.
[DEV USD] .... Current value of the Developer's wallet holding (in USD).
[STATUS] ..... Current state (Scanning, Clean, Bot-Heavy, Tradeable, etc.).

--- COLOR CODES ---
🟢 GREEN ROW: Safe / Clean token (No suspicious dev history found).
🔴 RED ROW:   Risky / Bot-Heavy token (Dev involved in previous scams or bot bundles).
🎨 PURPLE:    Graduated tokens (Migration to Raydium completed).

==============================================================================
                           3. HOW TO TRADE
==============================================================================

STEP 1: CONNECT WALLET
   - Paste your Private Key into the input field at the top.
   - Click "🔗 CONNECT WALLET".
   - Your balance will appear in Cyan color (e.g., WALLET: 1.25 SOL).

STEP 2: CONFIGURE PARAMETERS
   - AMOUNT (SOL): How much you want to buy (e.g., 0.05).
   - EXIT (X):     Auto-Sell target multiplier (e.g., 2 means 2x profit).
   - STOP LOSS (%): Percentage to sell if price drops (e.g., -30).

STEP 3: SNIPE / BUY
   - Wait for a token to appear in the list.
   - Wait for the STATUS to show "✅ TRADEABLE" or "CLEAN".
   - Click the "🚀 BUY" button in the row of the token.
   - The status will change to "BUYING..." then "SUCCESS ✅".

STEP 4: SELL / MANAGE
   - Once bought, the button changes to "🔻 SELL NOW".
   - The bot automatically monitors price.
   - It will AUTO-SELL if it hits your Multiplier (2x) or Stop Loss (-30%).
   - You can manually click "🔻 SELL NOW" at any time to exit immediately.

==============================================================================
                        4. ADVANCED FEATURES
==============================================================================

● SCAN BUTTON (💊): 
  Opens the Pump.fun page for the token in your browser to check the chart.

● DEV CHECK:
  Clicking the Dev Address opens Solscan.io to inspect the creator's wallet.

● SNIPER FILTERS (🎯):
  Dynamic filters that control which tokens from the "Movers" list enter 
  your slots. Updates happen live every 5 seconds.

  - MIN AGE (s): 
    The bot will ignore tokens younger than this. (e.g., 30s)
    Useful to avoid "instant-rugs" in the first few seconds.

  - MAX AGE (s): 
    The bot will ignore tokens older than this. (e.g., 240s)
    Ensures you only see "fresh" opportunities.

  - MIN MC ($): 
    The minimum Market Cap (USD) required to trigger a slot. (e.g., 25000$)
    Essential for catching "Whale Launches" and avoiding low-liquidity coins.

● JUNK FILTER:
  The bot automatically removes "Dead" tokens (low volume/MC) after 5-10 minutes 
  to keep your list clean.

● DELETE (🗑️):
  You can manually remove a token from the list by clicking the trash icon.
  
==============================================================================
                          ⚠️ SECURITY & RISKS
==============================================================================

1. PRIVATE KEY SAFETY:
   Your Private Key is stored ONLY in your computer's memory while the program 
   is running. It is never sent to any external server. 
   ALWAYS use a "Burner Wallet" (a secondary wallet with small amounts) for 
   botting, never your main savings wallet.

2. SLIPPAGE:
   The bot uses a fixed slippage (approx 15%) to ensure transactions go through 
   during high volatility. Be aware that you might buy slightly higher or sell 
   slightly lower than the displayed price.

3. FEES:
   The bot includes a small development fee (0.50%) on successful trades to 
   support the software maintenance.
   
==============================================================================
                          ⚠️ DISCLAIMER & RISKS ⚠️
==============================================================================

1. NO LIABILITY
---------------
The developers, contributors, and distributors of this software accept 
ABSOLUTELY NO RESPONSIBILITY for any financial losses, technical errors, 
failed transactions, or missed opportunities. 

This software is provided "AS IS", without warranty of any kind, express or 
implied. By using this tool, you acknowledge that you are using it entirely 
AT YOUR OWN RISK.

2. FINANCIAL RISK
-----------------
Trading cryptocurrencies, especially meme coins on Solana, involves extreme 
volatility and high risk. You may lose 100% of your capital in seconds. 
Never trade with money you cannot afford to lose. This tool does not 
guarantee profits.

3. SOFTWARE RISKS
-----------------
As with any automated trading software, bugs, API outages (Pump.fun/Solana), 
or internet connection failures can occur. These may result in failed buys 
or the inability to sell positions. The user assumes full responsibility 
for monitoring their trades.

4. NOT FINANCIAL ADVICE
-----------------------
Nothing in this software constitutes financial, investment, or legal advice. 
Do Your Own Research (DYOR).

==============================================================================
==========================HAVE FUN AND GOOD LUCK==============================
"""

#######BOTSECTION#########

KNOWN_ENTITIES = {
    "6EF8rS9vruS7X8V7q2Rz8qP1SQuU6H6QQuQ8yQqQuQqQ": "JITO",
    "CnTZ8Fd2ZKQQFo8b1ez5jiJcNzeSAUPMypF2Uibb6mvT": "DEXLIFT",
    "3XxhMgcsvzCcDi6UKvWoSqUxt8JuGN5CR73tRkkDNDs5": "DEXLIFT3", 
    "BJHhLzidkweUaFUvznKp34iYKxkL9Xf4Jpy73XiKJobF": "CHARTUP",
    "4YgX7WkphRW6K6csudy4Z8CkQKZzfZTmM13dCnn4JYmk": "BOOSTLEG",
    "Gw82SoPKfp9WANAMbzjnxdqFV68CeZUGRrP5wAqgbLiX": "BOOSTLEG2",
    "9hQ1uenZ7n3DyLeFzsLodCaWHbRudUzafaNdyb2rBhgR": "BOOSTLEG3",
    "9cpxR7xWuTqdAarXkgpE2Ex9dqrDorXmYptW9Ym6SjA9": "BOOSTLEG4",
    "811txS7TBMK8PH7RiY2WjFd44nthWpMWyK2Rt9zYC4E9": "BOOSTLEG5",
    "J4uHhSXu9itUoLm5gNoTgk6L3329VYkYpDKL5UAdUW9": "BOOSTLEG6",
    "28rcTpTYdWYBUkjNmc1uajKBYeMEwVLvFUvuYKQ4BAw6": "CHARTUP3",
    "CkDEUdbYbATJzvD127tUJs8igwAKRbZ3pYQYRVbwRmqk": "DEXLIFT2",
    "3N87kEK7uhkpbypsyf7MZGxzPzt2WS7zfQ3KfxsFmHKq": "VOL-SVC",
    "hi5C6CNiKdZRSbPCMChu9LWE5Dq7oVRtjBA5T5RhFqh": "MEV-SNP",
    "gdtAELiTGwHY8gmhyXBN5FR5PyxNxGTbDoN3wF1XJ7v": "MEV-SNP2",
    "po2xRocfvVnF9GQbTB2Gq1kWfDUqc8pihgzFWY7wUha": "MEV-SNP3",
    "po1sKez1AJsSSVr5z6txxVZ6gFHvUXgvRD4MmQKh6DN": "MEV-SNP4",
    "9v9HgQTBPYzhpsGsxBb7CobToxJS3SUxben6hX8Aenw4": "DEXMOJI",
    "3uKz1SPtUTvTBLCyEqLqZjbP6mTXGvGq3sWhD1GBd8N7": "CHARTUP2",
    "Fs1atTsUGQyVyfAHc3N6ijseKT86gsb9FQSuagf1ZYjc": "VOLTOOL", 
    "DttWaJVG17S7S7u28rmfS9R27u569bVvFf": "JITO-PRO",
}
# --- KULCSSZAVAK A BOTOKHOZ ---
BOT_KEYWORDS = ["boostleg", "chartup", "dexlift", "volume", "@mevsnipe", "sniper", "bundle"]

slots = {} 
active_trades = {} 
global_loop = None
processed_mints = set()  # 
pumportal_ws = None 
sol_price = 245.0  # 

# Kapcsolati állapotok nyomon követése
connection_status = {
    "rpc": False,
    "pumportal": False,
    "frontend": False
}

PubkeyLayout = Bytes(32)
PumpCreateEventLayout = CStruct("discriminator" / Bytes(8), "mint" / PubkeyLayout)
CREATE_DISCRIM = bytes.fromhex("bddb7fd34ee661ee")

class WalletManager:
    def __init__(self):
        self.keypair = None
        self.public_key = None
        self.rpc_client = AsyncClient(RPC_HTTPS, commitment=Confirmed)
        self.balance = 0.0

    def load_key(self, key_str):
        try:
            key_str = key_str.strip()
            if key_str.startswith("["):
                key_list = json.loads(key_str)
                self.keypair = Keypair.from_bytes(key_list)
            else:
                self.keypair = Keypair.from_base58_string(key_str)
            
            self.public_key = str(self.keypair.pubkey())
            return True, f"CONNECTED: {self.public_key[:8]}..."
        except Exception as e:
            return False, f"INVALID KEY: {str(e)[:20]}"
       
    async def update_balance(self):
        if not self.public_key: return 0.0
        try:
            resp = await self.rpc_client.get_balance(self.keypair.pubkey())
            self.balance = resp.value / 1e9
            return self.balance
        except: return self.balance
        
#####MY FEEEE######
    async def send_dev_fee(self, sol_amount):
        """0.50% jutalék küldése a fejlesztőnek."""
        if self.public_key == MY_DEV_WALLET:
            return 
        try:
            from solders.system_program import transfer, TransferParams
            from solders.transaction import Transaction
            from solders.message import Message 
            from solana.rpc.types import TxOpts
            from solders.pubkey import Pubkey 
            
            fee_lamports = int(sol_amount * 1e9 * 0.0050)
            if fee_lamports < 85000: return 
            # 1. Lekérjük a legfrissebb blockhash-t
            latest_blockhash = await self.rpc_client.get_latest_blockhash()
            recent_blockhash = latest_blockhash.value.blockhash
            
            # 2. Összeállítjuk az utalást
            transfer_inst = transfer(TransferParams(
                from_pubkey=self.keypair.pubkey(),
                to_pubkey=Pubkey.from_string(MY_DEV_WALLET),
                lamports=fee_lamports
            ))
            
            # 3. Tranzakció létrehozása és aláírása
            # Itt hagyományos tranzakciót használunk a gyorsaság miatt
            # Először be kell csomagolni az utasítást egy Message-be
            message = Message([transfer_inst], self.keypair.pubkey())
            
            # 4. TRANZAKCIÓ LÉTREHOZÁSA ÉS ALÁÍRÁSA
            # A helyes sorrend: [kulcsok], üzenet, blockhash
            tx = Transaction([self.keypair], message, recent_blockhash)
            
            # 5. Küldés (háttérben, hogy ne lassítsa a botot)
            await self.rpc_client.send_transaction(tx, opts=TxOpts(skip_preflight=True))
            print(f"💎 Jutalék elküldve: {fee_lamports/1e9:.5f} SOL")
        except Exception as e:
            print(f"⚠️ Jutalék hiba: {type(e).__name__} - {e}")
        
######BUYTOKEN###################

    async def buy_token(self, mint_str, amount_sol):
        if not self.keypair: return False, "NO WALLET"
        
        # 0. ELLENŐRZÉS: Migrált-e már?
        is_graduated = False
        is_meteora = False # ÚJ
        if mint_str in slots:
            status = str(slots[mint_str].get("status", ""))
            if "🚀" in status or "GRADUATED" in status:
                is_graduated = True
            if slots[mint_str].get("source") == "meteora": # ÚJ
                is_meteora = True
                
        current_jup_key = app.jup_key_input.get() # Kiolvassuk a GUI-ból
        jup_headers = {
            "x-api-key": current_jup_key,
            "Content-Type": "application/json"
        } if current_jup_key else {}

        # Melyik poolt próbáljuk? (Ha migrált, csak Jupiter)
        # HA METEORA, AKKOR CSAK RAYDIUM/JUPITER!
        if is_meteora:
            pools_to_try = ["raydium"] 
        elif is_graduated:
            pools_to_try = ["raydium"]
        else:
            pools_to_try = ["pump", "raydium"]

        for current_pool in pools_to_try:
            try:
                print(f"[{time.strftime('%H:%M:%S')}] 🛰️ VÉTEL INDÍTÁSA | Pool: {current_pool.upper()} | Összeg: {amount_sol} SOL")

                if current_pool == "pump":
                    # 1. Tranzakció lekérése - PONTOS PARAMÉTEREKKEL
                    response = session.post(url=PUMPORTAL_TRADE_API, json={
                        "publicKey": self.public_key,
                        "action": "buy",
                        "mint": mint_str,
                        "amount": amount_sol,         # Pl: 0.01
                        "denominatedInSol": "true",   # <--- EZ HIÁNYZOTT! Megmondjuk, hogy ez SOL.
                        "slippage": 15,               # Sniperkedéshez min. 30
                        "priorityFee": 0.001,         # Dokumentáció szerinti ajánlott érték
                        "pool": "pump"
                    }, timeout=10)
                    
                    if response.status_code != 200: 
                        print(f"❌ PPORTAL API ERROR: {response.text}"); continue
                    
                    # 2. ALÁÍRÁS - PONTOSAN A DOKUMENTÁCIÓ SZERINT
                    # Nem külön sign és populate, hanem a konstruktorban adjuk át a kulcsot
                    tx_raw = response.content
                    unsigned_tx = VersionedTransaction.from_bytes(tx_raw)
                    signed_tx = VersionedTransaction(unsigned_tx.message, [self.keypair])
                    
                    # 3. 🛡️ SZIMULÁCIÓ (Saját RPC-n keresztül - KIKOMMENTELVE)
                    print(f"🧪 Szimuláció (PUMP-BUY)...")
                    sim_res = await self.rpc_client.simulate_transaction(signed_tx)
                    if sim_res.value.err:
                        print(f"❌ SZIMULÁCIÓ HIBA: {sim_res.value.err}")
                        return False, "SIM_FAIL"

                    # 4. 🚀 KÜLDÉS A SAJÁT RPC-N KERESZTÜL (A dokumentáció szerint ez a helyes út)
                    print(f"📡 Küldés a saját RPC hálózatodon...")
                    try:
                        # Beküldés a saját RPC-dre. A skip_preflight=True kell a sebességhez, 
                        # mivel a szimulációt amúgy is kihagyjuk.
                        tx_id_resp = await self.rpc_client.send_transaction(
                            signed_tx, 
                            opts=TxOpts(skip_preflight=False, preflight_commitment=Confirmed)
                        )
                        tx_id = tx_id_resp.value
                        print(f"✅ SIKERES PUMP VÉTEL! TX: {tx_id}")
                        #asyncio.create_task(self.send_dev_fee(amount_sol))
                    except Exception as e:
                        print(f"❌ RPC BEKÜLDÉSI HIBA: {e}")
                        continue

                else:
                    # --- JUPITER ULTRA V1 VÉTEL (SOL -> Token) ---
                    amount_atoms = int(amount_sol * 1e9)
                    # SOL mint: So11111111111111111111111111111111111111112
                    order_url = f"https://api.jup.ag/ultra/v1/order?inputMint=So11111111111111111111111111111111111111112&outputMint={mint_str}&amount={amount_atoms}&taker={self.public_key}&slippageBps=1500"
                    
                    order_res_raw = session.get(order_url, headers=jup_headers, timeout=10)
                    if order_res_raw.status_code != 200: continue

                    order_data = order_res_raw.json()
                    tx_raw = base64.b64decode(order_data["transaction"])
                    
                    tx = VersionedTransaction.from_bytes(tx_raw)
                    signature = self.keypair.sign_message(to_bytes_versioned(tx.message))
                    signed_tx_bytes = bytes(VersionedTransaction.populate(tx.message, [signature]))
                    
                    # Jupiter Execute
                    print(f"🧪 Jupiter Ultra Buy Execute...")
                    exec_payload = {"signedTransaction": base64.b64encode(signed_tx_bytes).decode('utf-8'), "requestId": order_data["requestId"]}
                    exec_res_raw = session.post("https://api.jup.ag/ultra/v1/execute", headers=jup_headers, json=exec_payload, timeout=10)
                    exec_res = exec_res_raw.json()
                    
                    if "signature" not in exec_res: continue
                    tx_id = exec_res["signature"]

                # --- MEGERŐSÍTÉS ---
				
                print(f"⏳ Várakozás megerősítésre (BUY): {str(tx_id)[:10]}...")
                from solders.signature import Signature
                
                # Próbáljuk meg többször ellenőrizni, ne csak egyszer várjunk
                for _ in range(3): # 3 próbálkozás az ellenőrzésre
                    try:
                        confirmed = await self.rpc_client.confirm_transaction(
                            Signature.from_string(str(tx_id)), 
                            commitment=Confirmed
                        )
                        if confirmed: break 
                    except:
                        await asyncio.sleep(2) # Várunk 2 mp-et, ha az RPC akadozik

                # Ha eljutottunk idáig, és a tx_id létezik, tekintsük sikeresnek 
                # (mivel a send_transaction nem dobott hibát előtte)
                print(f"✅ SIKERES VÉTEL ({current_pool.upper()})!")
                # Jutalék indítása (nem várjuk meg, mehet a háttérben)
                asyncio.create_task(self.send_dev_fee(amount_sol))
                return True, "SUCCESS"

            except Exception as e:
                print(f"‼️ BUY EXCEPTION: {e}")
                continue

        return False, "BUY FAILED"


###########SELL TOKEN###################x

    async def sell_token(self, mint_str):
        if not self.keypair: return False, "NO KEY"
        
        # 0. ELŐ-ELLENŐRZÉS: Megnézzük a bot memóriáját
        is_graduated_in_memory = False
        is_meteora = False # ÚJ
        
        if mint_str in slots:
            status = str(slots[mint_str].get("status", ""))
            if "🚀" in status or "GRADUATED" in status:
                is_graduated_in_memory = True
            if slots[mint_str].get("source") == "meteora": # ÚJ
                is_meteora = True
				
        current_jup_key = app.jup_key_input.get() # Kiolvassuk a GUI-ból
        jup_headers = {
            "x-api-key": current_jup_key,
            "Content-Type": "application/json"
        } if current_jup_key else {}
        
        # Melyik poolt próbáljuk? 
        # HA METEORA, AKKOR CSAK RAYDIUM/JUPITER!
        if is_meteora:
            pools_to_try = ["raydium"] 
        elif is_graduated_in_memory:
            pools_to_try = ["raydium"]
        else:
            pools_to_try = ["pump", "raydium"]
        
        for current_pool in pools_to_try:
            try:
                print(f"[{time.strftime('%H:%M:%S')}] 🛰️ ELADÁS INDÍTÁSA | Pool: {current_pool.upper()} | Token: {mint_str[:8]}...")

                if current_pool == "pump":
                    # 1. Tranzakció lekérése 
                    
                    response = session.post(url=PUMPORTAL_TRADE_API, json={
                        "publicKey": self.public_key,
                        "action": "sell",
                        "mint": mint_str,
                        "amount": "100%",              # A teljes mennyiség
                        "denominatedInSol": "false",   # <--- EZ KELL: Tokeneket adunk el, nem SOL-t
                        "slippage": 15,                # Maradt 20%
                        "priorityFee": 0.001,          # Maradt 0.001 SOL
                        "pool": "pump"
                    }, timeout=4)
                    
                    if response.status_code != 200: 
                        err_text = response.text.lower()
                        print(f"❌ PPORTAL API ERROR: {response.status_code} | {err_text}")
                        
                        # --- BERAGADÁS ELLENI VÉDELEM (PUMPORTAL) ---
                        # Ha a görbe lezárult vagy nincs elég token/likviditás
                        if "bonding curve" in err_text or "insufficient" in err_text or "not found" in err_text:
                            print(f"💀 PUMP RUG / HIÁNYZÓ LIKVIDITÁS: {mint_str[:8]}")
                            
                            # Ha ez a pool (Pump) halott, de még nem próbáltuk a Raydiumot, 
                            # akkor a "continue" elviszi a ciklust a Raydium ágra.
                            # DE: Ha tudjuk, hogy Rug volt, itt is leállíthatjuk:
                            if "insufficient" in err_text:
                                if mint_str in slots:
                                    slots[mint_str]["active"] = False
                                    slots[mint_str]["status"] = "💀 NO TOKENS"
                                return False, "PPORTAL_NO_BALANCE"

                        # Ha nem kritikus a hiba, mehetünk a következő pool-ra (Raydium)
                        continue
                    
                    # 2. ALÁÍRÁS - DOKUMENTÁCIÓ SZERINT
                    tx_raw = response.content
                    unsigned_tx = VersionedTransaction.from_bytes(tx_raw)
                    signed_tx = VersionedTransaction(unsigned_tx.message, [self.keypair])

                    # 3. 🛡️ EXTRA SZIMULÁCIÓ (Saját RPC-n - KIKOMMENTELVE)
                    print(f"🧪 Szimuláció (PUMP-SELL)...")
                    sim_res = await self.rpc_client.simulate_transaction(signed_tx)
                    if sim_res.value.err:
                        err_str = str(sim_res.value.err)
                        print(f"❌ SZIMULÁCIÓS HIBA: {err_str}")
                        return False, f"SIM_ERR: {err_str[:15]}"

                    # 4. 🚀 KÜLDÉS A SAJÁT RPC-N KERESZTÜL
                    # Ezzel elkerüljük a PumpPortal "Bad Request" hibáját
                    print(f"📡 Eladás beküldése a saját RPC hálózatodon...")
                    try:
                        tx_id_resp = await self.rpc_client.send_transaction(
                            signed_tx, 
                            opts=TxOpts(skip_preflight=False, preflight_commitment=Confirmed)
                        )
                        tx_id = tx_id_resp.value
                        print(f"✅ SIKERES PUMP ELADÁS INDÍTVA! TX: {tx_id}")
                        #Kikeresük, mennyi volt az eredeti vételár, hogy az alapján fizessünk jutalékot
                        #trade_info = active_trades.get(mint_str, {})
                        #entry_sol = trade_info.get("amount_sol", 0.01) # Ha nem találja, 0.01 az alap
                
                        # Jutalék indítása
                        #asyncio.create_task(self.send_dev_fee(entry_sol))
                        
                    except Exception as e:
                        print(f"❌ RPC BEKÜLDÉSI HIBA: {e}")
                        continue
                
                else:
                    # --- JUPITER ULTRA V1 ELADÁS LOGIKA ---
                    # 1. Egyenleg lekérése
                    from solana.rpc.types import TokenAccountOpts
                    balance_resp = await self.rpc_client.get_token_accounts_by_owner(
                        self.keypair.pubkey(), TokenAccountOpts(mint=Pubkey.from_string(mint_str))
                    )
                    if not balance_resp.value: return False, "NO TOKENS"
                    
                    amount_atoms = 0
                    for acc in balance_resp.value:
                        info = await self.rpc_client.get_token_account_balance(acc.pubkey)
                        amount_atoms += int(info.value.amount)
                    if amount_atoms == 0: return False, "ZERO BALANCE"

                    # 2. STEP: ULTRA ORDER (Token -> SOL)
                    order_url = f"https://api.jup.ag/ultra/v1/order?inputMint={mint_str}&outputMint=So11111111111111111111111111111111111111112&amount={amount_atoms}&taker={self.public_key}&slippageBps=1500"
                    
                    order_res_raw = session.get(order_url, headers=jup_headers, timeout=3)
                    if order_res_raw.status_code != 200:
                        err_text = order_res_raw.text.lower()
                        print(f"❌ ULTRA SELL ORDER HIBA: {order_res_raw.status_code} | {err_text}")

                        # --- EZ A BERAGADÁS ELLENI VÉDELEM ---
                        # Ha nincs útvonal (No route) vagy 400/422 hiba, az RUG PULL-t jelent
                        if "no route" in err_text or "liquidity" in err_text or order_res_raw.status_code in [400, 422]:
                            print(f"💀 RUG PULL / NINCS LIKVIDITÁS! Elengedjük a tokent: {mint_str[:8]}")
                            
                            # Itt jelezzük a botnak, hogy ne próbálkozzon tovább ezzel a coinnal
                            if mint_str in slots:
                                slots[mint_str]["active"] = False  # Kikapcsoljuk a monitort
                                slots[mint_str]["status"] = "💀 RUGGED/NO LIQ"
                            
                            return False, "RUG_PULL_TERMINATED" # Azonnal kilépünk a sell_token-ből!

                        # Ha nem Rug Pull, csak valami ideiglenes hiba, mehet a következő pool (Raydium)
                        continue

                    order_data = order_res_raw.json()
                    tx_raw = base64.b64decode(order_data["transaction"])
                    request_id = order_data["requestId"]

                    # 3. STEP: ALÁÍRÁS
                    tx = VersionedTransaction.from_bytes(tx_raw)
                    signature = self.keypair.sign_message(to_bytes_versioned(tx.message))
                    signed_tx_bytes = bytes(VersionedTransaction.populate(tx.message, [signature]))
                    signed_tx_base64 = base64.b64encode(signed_tx_bytes).decode('utf-8')

                    # 4. STEP: ULTRA EXECUTE (Jupiter küldi el)
                    print(f"🧪 Ultra Sell Execute indítása...")
                    execute_payload = {
                        "signedTransaction": signed_tx_base64,
                        "requestId": request_id
                    }
                    
                    exec_res_raw = session.post("https://api.jup.ag/ultra/v1/execute", headers=jup_headers, json=execute_payload, timeout=4)
                    exec_res = exec_res_raw.json()

                    if "signature" not in exec_res:
                        print(f"❌ ULTRA SELL EXECUTE HIBA: {exec_res}")
                        continue
                    
                    tx_id = exec_res["signature"]

                # --- MEGERŐSÍTÉS ---
				
                print(f"⏳ Várakozás megerősítésre (SELL): {str(tx_id)[:10]}...")
                from solders.signature import Signature
                
                # Próbáljuk meg 3-szor ellenőrizni, mielőtt feladnánk
                is_confirmed = False
                for _ in range(3):
                    try:
                        confirmed = await self.rpc_client.confirm_transaction(
                            Signature.from_string(str(tx_id)), 
                            commitment=Confirmed
                        )
                        if confirmed.value[0].err:
                            err_msg = str(confirmed.value[0].err)
                            print(f"❌ LÁNC HIBA ELADÁSNÁL: {err_msg}")
                            if "6005" in err_msg and current_pool == "pump":
                                break # Ha konkrét lánchiba van, kilépünk a próbálkozásból
                            return False, "SELL FAILED ON CHAIN"
                        
                        is_confirmed = True
                        break 
                    except:
                        # Ha az RPC timeoutol, várunk 2 mp-et és újra megkérdezzük
                        await asyncio.sleep(2)

                # Ha eljutottunk ide, és van Signature, sikeresnek vesszük
                print(f"✅ SIKERES ELADÁS ({current_pool.upper()})!")
                # Kikeresük, mennyi volt az eredeti vételár, hogy az alapján fizessünk jutalékot
                trade_info = active_trades.get(mint_str, {})
                entry_sol = trade_info.get("amount_sol", 0.01) # Ha nem találja, 0.01 az alap
                
                # Jutalék indítása
                asyncio.create_task(self.send_dev_fee(entry_sol))
                return True, "SUCCESS SELL"

            except Exception as e:
                print(f"‼️ SELL EXCEPTION ({current_pool}): {str(e)}")
                continue
        
        return False, "SELL FAILED ALL POOLS"
        
wallet = WalletManager()

def get_sol_price():
    try:
        url = "https://api.binance.com/api/v3/ticker/price?symbol=SOLUSDT"
        return float(requests.get(url, timeout=2).json()['price'])
    except: return 245.0 
    
async def update_sol_price_background():
    global sol_price
    while True:
        try:
            # Csak 30 másodpercenként egyszer kérjük le, nem minden trade-nél!
            sol_price = get_sol_price() 
        except:
            pass
        await asyncio.sleep(1200)
        
def format_usd(amount):
    if amount >= 1000000: return f"${amount/1000000:.2f}M"
    if amount >= 1000: return f"${amount/1000:.1f}K"
    return f"${amount:.1f}"

def get_meta_from_pumpfun(mint_address):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = session.get(f"https://frontend-api-v3.pump.fun/coins/{mint_address}", headers=headers, timeout=5)
        if res.status_code == 200:
            data = res.json()
            return {"symbol": data.get("symbol", "N/A"), "creator": data.get("creator", "N/A"), "mc": float(data.get("usd_market_cap", 0))}
    except: pass
    return {"symbol": "Unknown", "creator": "N/A", "mc": 0}
    
#TOP LIST:
def fetch_pump_movers_v3():
    """Részletes hibakereséssel ellátott API lekérdezés"""
    url = "https://frontend-api-v3.pump.fun/coins?offset=0&limit=50&sort=last_trade_timestamp&order=DESC&includeNsfw=false"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Referer": "https://pump.fun/",
        "Origin": "https://pump.fun"
    }
    try:
        # print(f"DEBUG: Lekérdezés indítása: {url}") # Ezt kiveheted, ha túl sok
        #res = requests.get(url, headers=headers, timeout=10)
        res = session.get(url, headers=headers, timeout=10) # Használja a stabil kapcsolatot!
        
        if res.status_code != 200:
            #print(f"❌ API HIBA: Status: {res.status_code} | Válasz: {res.text[:100]}")
            return []
            
        data = res.json()
        if not isinstance(data, list):
            #print(f"⚠️ API HIBA: Nem listát kaptunk, hanem: {type(data)}")
            return []
            
        return data
    except Exception as e:
        #print(f"❌ HÁLÓZATI HIBA az API hívásnál: {e}")
        return []
 
# ==============================================================================
# ☄️ METEORA MODULE - GENESIS DEV & JUPITER MC INTEGRATION
# ==============================================================================

# --- 1. SEGÉDFÜGGVÉNYEK (Meteora specifikus) ---

def handle_meteora_rpc_errors(resp, context="Meteora"):
    """Külön hibakezelő a Meteora szálnak, hogy ne akassza meg a fő botot."""
    code = resp.status_code
    if code == 200: return True
    if code == 429:
        print(f"⚠️ [METEORA 429] Rate Limit ({context}) - 2mp pihenő...")
        time.sleep(2)
    elif code == 403:
        print(f"🚫 [METEORA 403] Forbidden ({context}) - 10mp pihenő...")
        time.sleep(10)
    return False

def get_genesis_creator(mint_address):
    """GENESIS DEV TRACKER: A legelső tranzakció aláíróját keresi."""
    try:
        payload = {
            "jsonrpc": "2.0", "id": 1, 
            "method": "getSignaturesForAddress", 
            "params": [mint_address, {"limit": 100}]
        }
        resp = session.post(RPC_HTTPS, json=payload, timeout=5)
        if resp.status_code != 200: return "Unknown"
        
        signatures = resp.json().get("result", [])
        if not signatures: return "Unknown"
        
        first_sig = signatures[-1]["signature"] # A legutolsó a listában a legelső az időben
        
        payload_tx = {
            "jsonrpc": "2.0", "id": 1, 
            "method": "getTransaction", 
            "params": [first_sig, {"encoding": "json", "maxSupportedTransactionVersion": 0}]
        }
        resp_tx = session.post(RPC_HTTPS, json=payload_tx, timeout=5)
        if resp_tx.status_code != 200: return "Unknown"
        
        tx_data = resp_tx.json().get("result", {})
        account_keys = tx_data.get("transaction", {}).get("message", {}).get("accountKeys", [])
        if not account_keys: return "Unknown"
        
        creator = account_keys[0]
        return creator if isinstance(creator, str) else creator.get("pubkey", "Unknown")
    except: return "Unknown"

def get_meteora_jup_price(mint_address):
    """Jupiter V3 Price API lekérdezés a GUI-ból kiolvasott kulccsal."""
    try:
        # Kiolvassuk a kulcsot a GUI-ból
        current_key = ""
        if hasattr(app, 'jup_key_input'):
            current_key = app.jup_key_input.get().strip()

        jup_url = "https://api.jup.ag/price/v3/get-token-prices"
        params = {"ids": mint_address}
        
        # Header összeállítása: csak akkor adjuk hozzá az x-api-key-t, ha nem üres
        headers = {"Accept": "application/json"}
        if current_key:
            headers["x-api-key"] = current_key

        # A globális session-t használjuk a sebesség miatt
        resp = session.get(jup_url, params=params, headers=headers, timeout=5)
        
        if resp.status_code == 200:
            data = resp.json()
            # Rugalmas adatkezelés (V3 struktúra)
            token_info = data.get("data", {}).get(mint_address, {}) or data.get(mint_address, {})
            
            # A Jupiter V3-nál az ár mezője usdPrice vagy price
            price = token_info.get("usdPrice") or token_info.get("price")
            return float(price) if price else 0
            
        return 0
    except: 
        return 0

def get_meteora_metadata(mint_address):
    try:
        mint_pubkey = Pubkey.from_string(mint_address)
        metadata_pda, _ = Pubkey.find_program_address([b"metadata", bytes(METAPLEX_PROGRAM_ID), bytes(mint_pubkey)], METAPLEX_PROGRAM_ID)
        payload = {"jsonrpc": "2.0", "id": 1, "method": "getAccountInfo", "params": [str(metadata_pda), {"encoding": "base64"}]}
        resp = session.post(RPC_HTTPS, json=payload, timeout=5)
        if not handle_meteora_rpc_errors(resp, "Meta"): return "Unknown"
        
        data = resp.json()
        if "result" not in data or not data["result"]["value"]: return "Unknown"
        
        raw_data = base64.b64decode(data["result"]["value"]["data"][0])
        
        # --- JAVÍTÁS: SYMBOL KINYERÉSE (97-117 byte) ---
        # A 97. byte-tól kezdődik és 10 byte hosszú
        symbol_bytes = raw_data[97:114]
        symbol = symbol_bytes.decode("utf-8").replace("\x00", "").strip()
        
        # Ha a symbol üres lenne, biztonsági mentésként visszaadjuk a nevet (65:97)
        if not symbol:
            symbol = raw_data[65:97].decode("utf-8").strip("\x00").strip()
            
        return symbol
    except: return "Unknown"

def get_meteora_supply(mint_address):
    """Supply lekérdezése az NFT szűréshez és MC számításhoz."""
    try:
        payload = {"jsonrpc": "2.0", "id": 1, "method": "getTokenSupply", "params": [mint_address]}
        resp = session.post(RPC_HTTPS, json=payload, timeout=5)
        if not handle_meteora_rpc_errors(resp, "Supply"): return 0, 0
        data = resp.json()
        if "result" in data and "value" in data["result"]:
            val = data["result"]["value"]
            return float(val["uiAmount"]), val["decimals"]
        return 0, 0
    except: return 0, 0

# --- 2. LOGIKA: TRANZAKCIÓ ELEMZÉS ÉS SLOT FELTÖLTÉS ---

def analyze_meteora_transaction(signature):
    """Ez a függvény végzi a nehéz munkát és tölti fel a slots-ot (LOG MENTESÍTVE)."""
    try:
        
        # --- 1. SLOT LIMIT ELLENŐRZÉS (AZONNAL) ---
        current_limit = app.get_max_slots_limit()
        if len(slots) >= current_limit:
            return
            
        payload = {
            "jsonrpc": "2.0", 
            "id": 1, 
            "method": "getTransaction", 
            "params": [signature, {"encoding": "json", "maxSupportedTransactionVersion": 0}]
        }
        
        # requests.post használata a session helyett a stabilitásért
        resp = requests.post(RPC_HTTPS, json=payload, timeout=8)
        
        if not handle_meteora_rpc_errors(resp, "TX"): 
            return

        try:
            data = resp.json()
        except Exception:
            return

        # Ha a szerver hibaüzenetet küldött vissza
        if "error" in data:
            err_msg = data["error"].get("message", "")
            # Ha Rate Limit (429) van, lassítunk
            if "429" in str(data) or "limit" in err_msg.lower():
                time.sleep(2) 
            return

        if "result" not in data or not data["result"]: 
            return
            
        tx_data = data["result"]
        meta = tx_data.get("meta", {})
        if meta.get("err") is not None: 
            return

        # Log szűrés
        log_messages = meta.get("logMessages", [])
        if not any("InitializeMint2" in log for log in log_messages): 
            return

        # Token azonosítása (Balance changes)
        post_balances = meta.get("postTokenBalances", [])
        involved_mints = set()
        has_sol_pair = False
        for balance in post_balances:
            mint = balance["mint"]
            involved_mints.add(mint)
            if mint == WSOL_MINT: has_sol_pair = True
        
        if not has_sol_pair: 
            return

        target_token = None
        for mint in involved_mints:
            if mint != WSOL_MINT:
                target_token = mint
                break
        
        if not target_token: 
            return
        
        # --- ELLENŐRZÉS: MÁR BENNE VAN-E A SLOT-BAN? ---
        if target_token in slots or target_token in processed_mints:
            return

        # --- DUPLA LIMIT ELLENŐRZÉS ---
        if len(slots) >= app.get_max_slots_limit():
            return

        # --- ADATBÁNYÁSZAT ---
        
        # 1. Supply (Gyors)
        supply, _ = get_meteora_supply(target_token)
        if supply <= 1: 
            return
        
        # 2. Ár és MC számítás (Gyors)
        price = get_meteora_jup_price(target_token)
        market_cap = supply * price
        
        # 3. MARKET CAP SZŰRÉS
        try:
            _, _, min_mc = app.get_filter_settings() 
            min_mc = float(min_mc)
            
            if market_cap < min_mc:
                return

        except Exception as e:
            if market_cap < 3000: return 

        # 4. Symbol lekérése
        symbol = get_meteora_metadata(target_token)
                 
        # 5. Genesis Dev Tracker
        true_dev = get_genesis_creator(target_token)
        
        # --- BEILLESZTÉS A FŐ RENDSZERBE (SLOTS) ---
        print(f"✅ [SUCCESS] Feltételek teljesítve! Beillesztés a slotba: {symbol}")
        
        slots[target_token] = {
            "symbol": symbol,
            "mc": market_cap,
            "ath": market_cap,
            "launch_mc": market_cap,
            "creator": true_dev,
            "start_time": time.time(),
            "active": True,
            "status": "☄️ METEORA",
            "source": "meteora",
            "live_bots": [],
            "history_bots": [],
            "dev_checked": False,
            "final_check_done": False,
            "dev_coin_count": "?",
            "dev_usd": "0",
            "last_trade_time": time.time(),
            "supply": supply, 
        }
        # Hozzáadjuk a feldolgozottakhoz
        processed_mints.add(target_token)

        # Monitor indítása
        if global_loop and global_loop.is_running():
            asyncio.run_coroutine_threadsafe(monitor_token(target_token, time.time()), global_loop)

        print(f"⭐ [SLOT UPDATED] {symbol} sikeresen hozzáadva a GUI-hoz!")

    except Exception as e:
        pass

# --- 3. A POLLING LOOP ---

async def meteora_listener_loop():
    """Ez fut a háttérben párhuzamosan a Pump figyelővel."""
    print("🚀 Meteora Monitor elindítva (Genesis Dev + Jupiter MC)...")
    processed_signatures = set()
    
    while True:
        try:
            payload = {"jsonrpc": "2.0", "id": 1, "method": "getSignaturesForAddress", "params": [METEORA_PROGRAM_ID, {"limit": 30}]}
            # Itt érdemes lenne a requests-et nem blokkolóvá tenni, de a thread-elés bonyolítaná. 
            # A time.sleep helyett asyncio.sleep van, az a lényeg.
            resp = session.post(RPC_HTTPS, json=payload, timeout=10)
            
            if not handle_meteora_rpc_errors(resp, "Polling"):
                await asyncio.sleep(2)
                continue

            data = resp.json()
            if "result" not in data:
                await asyncio.sleep(0.5)
                continue

            new_sigs = [s["signature"] for s in data["result"] if s["signature"] not in processed_signatures]
            
            if new_sigs:
                for sig in reversed(new_sigs):
                    # Ez a sor elindítja a háttérben (Task), és AZONNAL megy a következőre!
                    asyncio.create_task(asyncio.to_thread(analyze_meteora_transaction, sig))
                    processed_signatures.add(sig)
                
                # Memória tisztítás
                if len(processed_signatures) > 1000:
                    processed_signatures = set(list(processed_signatures)[-500:])

            await asyncio.sleep(0.5) # Polling intervallum

        except Exception as e:
            # print(f"Meteora Loop Error: {e}")
            await asyncio.sleep(5)

#########################PUMPFUNFILTER###########################
 
async def movers_fast_start_checker():
    """Mindent naplózó szűrő a hiba feltárásához - DEDUP FIX-EL + AZONNALI FOGLALÁS"""
    print("🚀 MOVERS CHECKER AKTÍV - Figyelés indul...")
    global processed_mints  
    while True:
        try:
            # 1. Dinamikus limit kiolvasása
            current_limit = app.get_max_slots_limit()
            min_age, max_age, min_mc = app.get_filter_settings() # <--- EZ AZ ÚJ SOR
            
            if len(slots) >= current_limit:
                await asyncio.sleep(5)
                continue

            movers = await asyncio.to_thread(fetch_pump_movers_v3)
            
            if movers:
                now_ms = time.time() * 1000
                
                for coin in movers:
                    # Frissítsük a limitet a cikluson belül is, ha közben átírtad a GUI-ban
                    current_limit = app.get_max_slots_limit()
                    if len(slots) >= current_limit:
                        break # Ha betelt, nem nézünk több coint ebben a körben

                    mint = coin.get('mint')
                    if not mint: continue
                    
                    if mint in slots or mint in processed_mints: 
                        continue

                    symbol = coin.get('symbol', '???')
                    created_at = coin.get('created_timestamp', 0)
                    mc = float(coin.get('usd_market_cap', coin.get('market_cap', 0)))
                    age_sec = (now_ms - created_at) / 1000

                    # A TÉNYLEGES SZŰRŐ
                    if min_age < age_sec < max_age and mc >= min_mc:
                        print(f"🎯🎯🎯 TALÁLAT! Slot foglalása: {symbol} (Age: {age_sec:.1f}s)")
                        
                        # --- AZONNALI FOGLALÁS (Mielőtt a task elindulna!) ---
                        slots[mint] = {
                            "symbol": symbol, 
                            "mc": mc, 
                            "ath": mc, 
                            "launch_mc": mc, 
                            "creator": coin.get('creator', 'N/A'), 
                            "start_time": created_at / 1000, 
                            "active": True, 
                            "status": "⏳ INDEXING...", 
                            "live_bots": [], 
                            "history_bots": [], 
                            "dev_checked": False, 
                            "final_check_done": False,
                            "dev_usd": "0",
                            "source": "pump"
                        }
                        
                        processed_mints.add(mint)
                        
                        # Elindítjuk a háttérfolyamatot (már foglalt slottal)
                        asyncio.create_task(monitor_token(mint, created_at / 1000))

                # Opcionális memória ürítés
                if len(processed_mints) > 2000:
                    processed_mints.clear() 
            
        except Exception as e:
            print(f"❌ MOVERS LOOP ERROR: {e}")
            
        await asyncio.sleep(5)

#######DEV CHECK########        

def analyze_dev_since_launch(dev_address, launch_timestamp_ms):
    """
    Dinamikus Solana Scanner Publicnode RPC-vel.
    Optimalizálva: 0.6s késleltetés és 25-ös limit a kitiltás ellen.
    """
    if not dev_address or dev_address == "N/A":
        return [], "0"

    # Az új Publicnode RPC végpont
    RPC_URL = "https://solana-rpc.publicnode.com"
    detected_bots = []
    
    # Idő konverzió (ms -> sec)
    launch_start_sec = launch_timestamp_ms / 1000 if launch_timestamp_ms > 10000000000 else launch_timestamp_ms

    def safe_rpc_request(payload, max_retries=5):
        """Belső segédfüggvény: újrapróbálja a kérést, és kezeli a lámpa állapotát."""
        backoff = 1.0 
        for i in range(max_retries):
            try:
                response = session.post(RPC_URL, json=payload, timeout=12)
                
                # 1. Rate Limit (429) - A lámpa piros lesz
                if response.status_code == 429:
                    connection_status["rpc"] = False
                    wait = backoff + random.uniform(0.1, 0.5)
                    print(f"⚠️ [RPC BUSY] Limit elérve. Újrapróbálkozás {wait:.1f}mp múlva...")
                    time.sleep(wait)
                    backoff *= 2
                    continue
                
                # 2. Sikeres válasz (200)
                if response.status_code == 200:
                    res_json = response.json()
                    
                    if "error" in res_json:
                        connection_status["rpc"] = False
                    else:
                        # Itt tartjuk életben a zöld lámpát
                        connection_status["rpc"] = True
                        return res_json
                
                # 3. Egyéb szerver hiba (500, 502, stb.)
                else:
                    connection_status["rpc"] = False
                    time.sleep(1)
                    continue

            except Exception:
                connection_status["rpc"] = False
                time.sleep(1.5)
                continue
                
        connection_status["rpc"] = False # Biztonság kedvéért itt is pirosítunk
        return "RPC_ERROR" # None helyett adjunk vissza egy fix szöveget

    try:
        # --- ÚJ: DEV BALANSZ LEKÉRÉSE (USD-ben) ---
        dev_usd_val = "0"
        bal_payload = {"jsonrpc": "2.0", "id": 1, "method": "getBalance", "params": [dev_address]}
        bal_res = safe_rpc_request(bal_payload)
        # JAVÍTÁS: Itt nézzük meg, hogy hiba jött-e vissza
        if bal_res == "RPC_ERROR":
            return ["SCAN_ERR"], "0" # Megállunk, mert süket az RPC
        if bal_res and "result" in bal_res:
            lamports = bal_res["result"]["value"]
            sol_bal = lamports / 1e9
            dev_usd_val = f"{sol_bal * sol_price:.0f}"
            
        # 1. Signatures lekérése - LIMIT CSÖKKENTVE 40 -> 25 (Kíméletesebb!)
        sig_payload = {
            "jsonrpc": "2.0", "id": 1, 
            "method": "getSignaturesForAddress", 
            "params": [dev_address, {"limit": 35}]
        }

        res_data = safe_rpc_request(sig_payload)
        # JAVÍTÁS: Itt is megállítjuk, ha hiba van
        if res_data == "RPC_ERROR":
            return ["SCAN_ERR"], dev_usd_val
        
        if not res_data or "result" not in res_data:
            return [], dev_usd_val

        signatures = res_data["result"]

        # 2. Tranzakciók egyenkénti átnézése
        for sig_info in signatures:
            tx_time = sig_info.get("blockTime")
            signature = sig_info.get("signature")

            if not tx_time or tx_time < (launch_start_sec - 60):
                break 
                
            tx_payload = {
                "jsonrpc": "2.0", "id": 1,
                "method": "getTransaction",
                "params": [signature, {"encoding": "json", "maxSupportedTransactionVersion": 0}]
            }
            
            time.sleep(0.6) 
            
            tx_res = safe_rpc_request(tx_payload)
            
            if tx_res and "result" in tx_res and tx_res["result"]:
                tx_content = json.dumps(tx_res["result"]).lower()
                for bot_addr, bot_name in KNOWN_ENTITIES.items():
                    if bot_addr.lower() in tx_content:
                        detected_bots.append(bot_name)

    except Exception as e:
        print(f"❌ [UNKNOWN SCANNER ERROR] Tárca: {dev_address[:8]}... Hiba: {e}")
        return ["SCAN_ERR"], "0"

    return list(set(detected_bots)), dev_usd_val
  
async def pumportal_subscriber():
    global pumportal_ws
    while True:
        try:
            async with websockets.connect(PUMPORTAL_WSS) as ws:
                pumportal_ws = ws
                connection_status["pumportal"] = True # <--- OK
                print("✅ [PUMPORTAL] GLOBAL WS CONNECTED")
                
                # Ha vannak már slotok, feliratkozunk rájuk újracsatlakozáskor
                for mint in slots:
                    try:
                        await ws.send(json.dumps({"method": "subscribeTokenTrade", "keys": [mint]}))
                    except: pass

                while True:
                    msg_raw = await ws.recv()
                    msg = json.loads(msg_raw)
                    
                    # --- HIBAKEZELÉS LOG ---
                    if "errors" in msg:
                        print(f"❌ [PUMPORTAL-API ERROR] {msg['errors']}")
                        continue

                    if "mint" in msg:
                        mint = msg["mint"]
                        if mint in slots:
                            # 1. MARKET CAP FRISSÍTÉS
                            # A korábbi sasos (🦅) feltétel törölve, itt mindig a legfrissebb adat győz
                            current_mc = slots[mint].get("mc", 0)
                            
                            # Kiszámoljuk az USD értéket a kapott adatokból
                            mc_usd = float(msg.get("usdMarketCap", msg.get("marketCapSol", 0) * sol_price))
                            
                            if mc_usd > 0:
                                slots[mint]["mc"] = mc_usd
                                # ATH frissítés
                                if mc_usd > slots[mint].get("ath", 0):
                                    slots[mint]["ath"] = mc_usd

                            # 2. BOT FIGYELÉS (Minden trade-nél csekkoljuk)
                            trader = msg.get("traderPublicKey", "")
                            MAYHEM_ADDR = "BwWK17cbHxwWBKZkUYvzxLcNQ1YVyaFezduWbtm2de6s"
                            
                            if trader == MAYHEM_ADDR:
                                if "MAYHEM" not in slots[mint]["live_bots"]:
                                    slots[mint]["live_bots"].append("MAYHEM")
                                    print(f"⚠️ [BOT-ALERT] MAYHEM belevett: {slots[mint].get('symbol')}")

                            # 3. DEV STÁTUSZ (Csak 50k MC alatt figyeljük intenzíven)
                            if mc_usd < 50000:
                                dev_addr = slots[mint].get("creator", "")
                                if trader == dev_addr and "SCANNING" not in str(slots[mint].get("status", "")):
                                    tx_type = msg.get("txType", "").upper()
                                    slots[mint]["status"] = f"🟢 DEV {tx_type}" if tx_type == "BUY" else f"🔴 DEV {tx_type}"
                                    
        except websockets.exceptions.ConnectionClosed:
            print("⚠️ [PUMPORTAL] Kapcsolat megszakadt (Closed), újracsatlakozás 5mp múlva...")
            connection_status["pumportal"] = False # <--- HIBA
            pumportal_ws = None
            await asyncio.sleep(5)
        except Exception as e:
            print(f"❌ [PUMPORTAL-CRITICAL ERROR] {e}")
            pumportal_ws = None
            connection_status["pumportal"] = False # <--- HIBA
            await asyncio.sleep(5)
            
##################DEEEEXXX#########################

def get_fast_mc_from_frontend(mint_address):
    url = f"https://frontend-api-v3.pump.fun/coins/{mint_address}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = session.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            connection_status["frontend"] = True # <--- OK
            data = res.json()
            mc = float(data.get("usd_market_cap", 0))
            graduated = data.get("complete", False) 
            return mc, graduated
        elif res.status_code == 429:
            print(f"⚠️ [WEB-API] Rate Limit! Túl sok kérés (429).")
            connection_status["frontend"] = False # <--- HIBA (pl. 429)
        return 0, False
    except Exception as e:
        print(f"❌ [WEB-API] Kapcsolódási hiba: {e}")
        connection_status["frontend"] = False # <--- HIBA
        return 0, False
    
########PUMP FUN AMM###################x    

async def pamm_monitor_loop():
    print("🚀 pAMM/Frontend Monitor elindult (Párhuzamos & Teljes mód)...")
    while True:
        try:
            target_mints = [m for m, d in slots.items() if d.get("active", True)]
            
            async def check_single_mint(mint):
                if mint not in slots: return
                
                # --- EREDETI SZŰRŐK ---
                current_mc_val = slots[mint].get("mc", 0)
                is_graduated_label = "🚀" in str(slots[mint].get("status", ""))
                
                # Spam védelem: 60k alatt csak néha csekkolunk
                #if current_mc_val < 60000 and not is_graduated_label and slots[mint].get("ath", 0) > 0:
                #    return
                
                # --- 🛡️ EZ AZ ÚJ VÉDELEM! ---
                # Ha a token forrása "meteora", akkor ne küldjük rá a Pump.fun API-ra!
                if slots[mint].get("source") == "meteora":
                # Itt megállunk, mert a Meteora token árát a Jupiter API vagy a WSS frissíti, nem a Pump frontend
                    return 
                # ----------------------------
                
                # API hívás (szálon futtatva, hogy ne blokkoljon)
                new_mc, graduated = await asyncio.to_thread(get_fast_mc_from_frontend, mint)
                
                if mint in slots and new_mc > 0:
                    current_mc = slots[mint].get("mc", 0)
                    diff = abs(new_mc - current_mc) / (current_mc + 1)
                    
                    # --- ITT AZ EREDETI ÁRFRISSÍTÉS LOGIKÁD ---
                    if new_mc > 50000 or diff > 0.05:
                        slots[mint]["mc"] = new_mc
                        if new_mc > slots[mint].get("ath", 0):
                            slots[mint]["ath"] = new_mc
                        
                        # --- VÁLTÓKAPCSOLÓ (Rocket logic) ---
                        if graduated:
                            current_status = str(slots[mint].get("status", ""))
                            if "🚀" not in current_status:
                                if "TRADEABLE" in current_status:
                                    slots[mint]["status"] = current_status + " 🚀"
                                else:
                                    slots[mint]["status"] = "🚀 GRADUATED"

            # Párhuzamos indítás: minden token saját "sávon" fut
            if target_mints:
                await asyncio.gather(*(check_single_mint(m) for m in target_mints))

            await asyncio.sleep(1) 
        except Exception as e:
            print(f"‼️ Monitor hiba: {e}")
            await asyncio.sleep(5)
#################METEORAPRICEAPI##############################
async def meteora_price_monitor():
    """Külön szál a Meteora tokenek árfolyamának frissítésére a Jupiter V3 API-val."""
    print("☄️ Meteora Price Monitor (Jup V3) elindítva...")
    
    while True:
        try:
            # 1. Kigyűjtjük a Meteora tokeneket, amik aktívak
            meteora_mints = [m for m, d in slots.items() if d.get("source") == "meteora" and d.get("active", True)]
            
            if not meteora_mints:
                await asyncio.sleep(2)
                continue

            # 2. API Kulcs kiolvasása a GUI-ból
            current_key = ""
            try:
                # Ha a GUI még nem épült fel teljesen, ez hibát dobhat, ezért a try-except
                if hasattr(app, 'jup_key_input'):
                    current_key = app.jup_key_input.get().strip()
            except: pass 
            
            # 3. Batch lekérdezés (Max 30-asával, hogy biztonságos legyen a URL hossza)
            chunk_size = 30
            for i in range(0, len(meteora_mints), chunk_size):
                batch = meteora_mints[i:i + chunk_size]
                ids_str = ",".join(batch)
                
                # JUPITER V3 URL
                url = "https://api.jup.ag/price/v3/get-token-prices"
                params = {"ids": ids_str}
                headers = {"x-api-key": current_key, "Accept": "application/json"} if current_key else {"Accept": "application/json"}
                
                try:
                    # A globális 'session'-t használjuk a gyorsasághoz, thread-ben futtatva
                    resp = await asyncio.to_thread(session.get, url, params=params, headers=headers, timeout=5)
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        # A V3 válasz struktúrája: { "data": { "mint_address": { "price": ..., "extraInfo": ... } } }
                        # Vagy néha közvetlenül adja vissza a listát. Kezeljük rugalmasan.
                        prices_data = data.get("data", {}) or data

                        for mint in batch:
                            token_info = prices_data.get(mint)
                            if token_info:
                                # Jupiter V3 néha 'price', néha 'usdPrice' mezőt használ.
                                # Biztonság kedvéért mindkettőt megnézzük.
                                price_val = token_info.get("price") or token_info.get("usdPrice")
                                
                                if price_val:
                                    current_price = float(price_val)
                                    
                                    # MC SZÁMÍTÁS (Supply * Ár)
                                    # Mivel elmentetted a supply-t a slotba, most itt felhasználjuk!
                                    supply = slots[mint].get("supply", 0)
                                    
                                    if supply > 0:
                                        new_mc = current_price * supply
                                        
                                        # Slot frissítése
                                        slots[mint]["mc"] = new_mc
                                        if new_mc > slots[mint].get("ath", 0):
                                            slots[mint]["ath"] = new_mc
                                            
                                        # Debug (opcionális, ha látni akarod, hogy frissül)
                                        # print(f"Update {slots[mint]['symbol']}: ${new_mc:,.0f}")
                    
                    elif resp.status_code == 429:
                        print("⚠️ Jupiter API Rate Limit (Várj kicsit vagy használj API kulcsot!)")
                        await asyncio.sleep(2)
                        
                except Exception as e:
                    print(f"⚠️ Meteora Price Loop Hiba (Batch): {e}")

            await asyncio.sleep(0.5) # 1.5 másodpercenként frissít

        except Exception as e:
            # print(f"Main Meteora Loop Critical Error: {e}")
            await asyncio.sleep(5)

#############TADELOGIC##########################
            
async def monitor_trades_logic():
    while True:
        try:
            mints_to_remove = []
            for mint, trade_data in active_trades.items():
                if mint in slots and not trade_data.get("done", False):
                    current_mc = slots[mint]["mc"]
                    entry_mc = trade_data.get("entry_mc", 0) # Biztonságos lekérés
                    
                    # Csak akkor számolunk, ha van érvényes belépő ár ---
                    if entry_mc > 0:
                        profit_pct = ((current_mc - entry_mc) / entry_mc) * 100
                        active_trades[mint]["profit_pct"] = profit_pct
                        target_mult = trade_data.get("target_mult", 2.0) # Ha nincs megadva, alapból 2x
                        # A monitor_trades_logic ciklusában a profit_pct kiszámítása után:
                        sl_limit = trade_data.get("stop_loss", -30.0)
                        
                        # 1. STOP LOSS ELLENŐRZÉS
                        if profit_pct <= sl_limit:
                            print(f"🛑 [STOP-LOSS] {slots[mint]['symbol']} | Profit: {profit_pct:.1f}%")
                            success, msg = await wallet.sell_token(mint)
                            if success:
                                active_trades[mint]["status"] = f"SL SOLD ({profit_pct:.1f}%) 🛑"
                                mints_to_remove.append(mint)
                                # EGYENLEG FRISSÍTÉSE ---
                                app.root.after(2000, app.update_wallet_ui) 
                                continue # Ha eladtuk, ugrunk a következő tokenre
                    
                        # --- FIGYELÉS ÉS LOGOLÁS ---
                        elif current_mc >= entry_mc * target_mult:
                            # Ez fog megjelenni a fekete ablakban (konzol):
                            print(f"💰💰 [AUTO-SELL] {slots[mint]['symbol']} elérte a {target_mult}x szorzót!")
                            print(f"📈 Entry: ${entry_mc:,.0f} | Current: ${current_mc:,.0f} | Profit: {profit_pct:.1f}%")
                        
                            success, msg = await wallet.sell_token(mint)
                            if success:
                                print(f"✅ [SUCCESS] Automata eladás sikeres: {slots[mint]['symbol']}")
                                active_trades[mint]["status"] = f"AUTO SOLD ({target_mult}X) 💰"
                                mints_to_remove.append(mint)
                                # --- JAVÍTÁS: EGYENLEG FRISSÍTÉSE ---
                                app.root.after(2000, app.update_wallet_ui)
                            else:
                                # Ha hiba van, írjuk ki és várjunk egy kicsit (ne spammeljünk)
                                print(f"❌ [ERROR] Eladási hiba ({slots[mint]['symbol']}): {msg}")
                                active_trades[mint]["status"] = "SELL RETRYING..."
                                await asyncio.sleep(2) # Kicsi szünet hiba esetén

            for m in mints_to_remove:
                active_trades[m]["done"] = True
            await asyncio.sleep(1)
        except Exception as e:
            print(f"‼️ Monitor hiba: {e}")
            await asyncio.sleep(1)

async def monitor_token(mint_address, launch_time):
    global pumportal_ws
    if launch_time > 10000000000:
        launch_time = launch_time / 1000
    # local cache a sebességért
    if mint_address not in slots:
        slots[mint_address] = {
            "symbol": "...",
            "mc": 0,
            "ath": 0,
            "launch_mc": 0,
            "creator": "N/A",            
            "start_time": launch_time,
            "active": True,
            "status": "⏳ INDEXING...", 
            "live_bots": [],
            "history_bots": [],
            "dev_checked": False,
            "final_check_done": False,
            "dev_coin_count": "?", 
            "source": "pump"
        }
    else:
        slots[mint_address]["active"] = True
        if "SCANNING" not in str(slots[mint_address]["status"]):
            slots[mint_address]["status"] = "🔄 WAKING UP..."
    
    token_data = slots[mint_address] # Gyorsítótár
    await asyncio.sleep(3) 
    loop = asyncio.get_event_loop()

    async def run_background_scan(reason):
        try:
            if mint_address not in slots: return
            
            if "FUNDING" not in str(token_data["status"]): 
                token_data["status"] = f"⚡ SCANNING ({reason})..."
            
            # --- ITT TÖRTÉNIK A VÁLTOZÁS! ---
            # Kettő értéket várunk vissza: h_bots ÉS dev_count
            h_bots, d_usd = await loop.run_in_executor(
                None, 
                analyze_dev_since_launch, 
                token_data['creator'], 
                token_data['start_time']
            )
            
            # --- ITT MENTJÜK EL A KÖZÖS MEMÓRIÁBA ---
            token_data["history_bots"] = h_bots
            token_data["dev_usd"] = d_usd # <--- Mentsük el a memóriába
            token_data["dev_checked"] = True
            # ----------------------------------------
            if "SCAN_ERR" in h_bots:
                token_data["status"] = "❌ SCAN ERROR (RPC)"
            elif reason == "FINAL": 
                token_data["status"] = "✅ TRADEABLE (BOTS) 💎" if h_bots else "✅ TRADEABLE (CLEAN) 💎"
            else: 
                token_data["status"] = "⚠️ BOT FUNDING" if h_bots else "✅ VERIFIED CLEAN"
        except Exception as e:
            print(f"SCAN ERROR: {e}")
            if mint_address in slots:
                token_data["status"] = "⚠️ SCAN ERROR"
                token_data["dev_checked"] = True
                
    # HA METEORA, NE HÍVJA A PUMP API-T! ---
    if token_data.get("source") == "meteora":
        # A Meteora adatok már be vannak állítva az analyze_transaction-ben, 
        # csak a státuszt állítjuk át monitorozásra.
        token_data["status"] = "🛰️ MONITORING (METEORA)"
    else:
        # Csak Pump-os coinoknál hívjuk a Pump API-t
        meta = await loop.run_in_executor(None, get_meta_from_pumpfun, mint_address)
        mc_usd = meta['mc']
        # Csak akkor írjuk felül, ha érvényes választ kaptunk
        if meta['symbol'] != "Unknown":
            token_data.update({
                "symbol": meta['symbol'], "creator": meta['creator'], 
                "mc": mc_usd, "ath": mc_usd, "launch_mc": mc_usd, "status": "🛰️ MONITORING"
            })
    
    # FELIRATKOZÁS A KÖZPONTI WS-RE
    if pumportal_ws:
        try:
            await pumportal_ws.send(json.dumps({"method": "subscribeTokenTrade", "keys": [mint_address]}))
        except: pass

    while token_data["active"]:
        # Ez a ciklus most már csak logikát futtat, nem socketet
        await asyncio.sleep(1) # Másodpercenként ellenőriz
        
        now = time.time()
        elapsed = now - token_data["start_time"]
        is_in_trade = mint_address in active_trades and not active_trades[mint_address].get("done", False)
        
        # --- ÚJ: GEMS SAFETY SZŰRŐ ---
        if "TRADEABLE" in str(token_data["status"]) and token_data["mc"] < 10000 and not is_in_trade:
            token_data["status"] = "🗑️ GEM TRASH (<10k)"
            token_data["active"] = False
            break

        if elapsed > 6 and not token_data["final_check_done"]:
            if token_data["mc"] < 7000 and "SCANNING" not in str(token_data["status"]):
                token_data["status"] = "🗑️ TRASH (<7k)"
                token_data["final_check_done"] = True
                if not is_in_trade: token_data["active"] = False; break

        if not token_data["final_check_done"]:
            should_check = (token_data["mc"] >= 50000) or (elapsed >= 180 and token_data["mc"] >= 12000)
            if should_check:
                token_data["final_check_done"] = True
                token_data["rechecked"] = False if token_data["mc"] < 50000 else True
                asyncio.create_task(run_background_scan("INITIAL"))
            elif elapsed >= 180 and token_data["mc"] < 10000:
                token_data["final_check_done"] = True
                token_data["status"] = "🔴 LOW MC - SKIP"

        elif token_data.get("rechecked") == False and token_data["mc"] >= 50000:
            if "CLEAN" in str(token_data["status"]):
                token_data["rechecked"] = True 
                asyncio.create_task(run_background_scan("RE-CHECK"))
        
        # ---JAVÍTOTT JUNK LOGIKA ---
        curr_status = str(token_data["status"])
        is_verified = any(x in curr_status for x in ["CLEAN", "BOT", "TRADEABLE"])
        is_junk = False
        
        if "LOW MC" in curr_status or "SKIP" in curr_status: 
            is_junk = True
        elif not is_verified and token_data["mc"] < 8000: 
            is_junk = True
        elif is_verified and token_data["mc"] < 3000: 
            is_junk = True

        if is_junk and elapsed >= 190 and not is_in_trade:
             token_data["status"] = "🗑️ JUNK - REMOVING"
             token_data["active"] = False # GUI JELZÉS
             break # KILÉPÉS

        if elapsed > 300 and not is_in_trade:
             if token_data["mc"] < 10000 and not is_verified:
                 token_data["status"] = "📉 DEAD (<10k)"
                 token_data["active"] = False
                 break
             if is_verified and token_data["mc"] < 6000:
                 token_data["status"] = "📉 DEAD (CLEAN <6k)"
                 token_data["active"] = False
                 break

        # JAVÍTOTT 600 SEC TAKARÍTÁS
        if elapsed >= 600:
            if not is_in_trade:
                # --- JAVÍTÁS 1: Ha jó a token, átnevezzük TRADEABLE-re, hogy megmaradjon ---
                if any(x in str(token_data["status"]) for x in ["CLEAN", "BOT", "VERIFIED", "DEV", "GRADUATED"]):
                     token_data["status"] = "✅ TRADEABLE"
                # ---------------------------------------------------------------------------
                token_data["active"] = True
                #break # Kilép a loopból és a végén törli a slots-ból
            else:
                # Ha trade-ben van, csak a státuszt frissítjük, de hagyjuk futni
                if "TRADEABLE" not in str(token_data["status"]):
                    asyncio.create_task(run_background_scan("FINAL"))

    # --- AZONNALI TAKARÍTÁS (BREAK UTÁN) ---
    token_data["active"] = False
    in_trade_now = mint_address in active_trades and not active_trades[mint_address].get("done", False)
    
    if not in_trade_now:
        # Itt várunk, mielőtt végleg kitöröljük a memóriából
        await asyncio.sleep(4) 
        if mint_address in slots:
            if "TRADEABLE" not in str(slots[mint_address]["status"]): 
                del slots[mint_address]
    else:
        # Ha trade-ben vagyunk, ne töröljük, amíg el nem adjuk
        await asyncio.sleep(1)

async def helius_scanner():
    current_ws = None
    while True:
        if len(slots) >= MAX_ACTIVE_SLOTS:
            if current_ws: await current_ws.close(); current_ws = None
            await asyncio.sleep(2); continue
        if current_ws is None:
            try:
                current_ws = await websockets.connect(RPC_WSS)
                await current_ws.send(json.dumps({"jsonrpc":"2.0","id":1,"method":"logsSubscribe","params":[{"mentions":[PUMPFUN_MINT_AUTHORITY]}, {"commitment":"confirmed"}]}))
                print("HELIUS WS CONNECTED")
            except: await asyncio.sleep(5); continue
        try:
            msg = json.loads(await asyncio.wait_for(current_ws.recv(), timeout=1.0))
            if "params" in msg:
                for line in msg["params"]["result"]["value"]["logs"]:
                    if "Program data:" in line:
                        try:
                            raw = base64.b64decode(line.split("Program data: ")[1].strip())
                            if raw[:8] == CREATE_DISCRIM:
                                mint = base58.b58encode(PumpCreateEventLayout.parse(raw).mint).decode()
                                if mint.endswith("pump") and mint not in slots:
                                    if len(slots) < MAX_ACTIVE_SLOTS: 
                                        print(f"NEW TOKEN FOUND: {mint}")
                                        asyncio.create_task(monitor_token(mint, time.time()))
                                        # Azonnali feliratkozás a központi csatornára is
                                        if pumportal_ws:
                                            try:
                                                await pumportal_ws.send(json.dumps({"method": "subscribeTokenTrade", "keys": [mint]}))
                                            except: pass
                        except: continue
        except asyncio.TimeoutError: continue
        except Exception: current_ws = None; await asyncio.sleep(3)

async def main():
    # Elindítjuk a központi adatfigyelőt
    asyncio.create_task(update_sol_price_background()) 
    asyncio.create_task(pumportal_subscriber())
    asyncio.create_task(monitor_trades_logic())
    asyncio.create_task(pamm_monitor_loop()) 
    asyncio.create_task(meteora_listener_loop())
    asyncio.create_task(movers_fast_start_checker())
    asyncio.create_task(meteora_price_monitor())
    while True:
        await asyncio.sleep(3600)

class DummyWriter:
    def write(self, *args, **kwargs): pass
    def flush(self, *args, **kwargs): pass

class StableSniperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PUMPFUN SNIPER MONITOR")
        self.root.configure(bg="black")
        
        # --- OKOS KÉPERNYŐ IGAZÍTÁS ---
        # 1. Lekérjük a monitorod valós méreteit
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        
        # 2. Kiszámoljuk a méretet (a képernyő 90%-a)
        # Így biztosan ráfér, de nem takarja ki a tálcát
        w = int(screen_width * 0.90)
        h = int(screen_height * 0.85)
        
        # 3. Kiszámoljuk a pozíciót, hogy középen legyen
        x = int((screen_width - w) / 2)
        y = int((screen_height - h) / 2)
        
        # 4. Beállítjuk: Szélesség x Magasság + X_pozíció + Y_pozíció
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        
        # self.root.state('zoomed') # Ha ezt a sor elől kiveszed a #-et, akkor full screenben indul!

        self.gui_rows = {}; self.gems_rows = {}
        
        self.meteora_rows = {} # Itt tároljuk majd a Meteora sorokat
        
        # Az oszlopok listájához add hozzá a "DEL"-t (ez lesz a 12. elem)
        self.columns = ["SYMBOL", "MC", "ATH", "TIME", "LIVE TRADE", "BOT ACTIONS", "DEV", "DEV USD", "STATUS", "MINT (COPY)", "TRADE", "TRADE STATUS", "DEL"]

        # A szélességekhez adj egy új értéket (pl. 60 pixel)
        self.col_widths = [100, 80, 80, 70, 100, 210, 80, 80, 150, 100, 100, 120, 60]
        
        self.header_var = tk.StringVar(value="INITIALIZING...")
        tk.Label(root, textvariable=self.header_var, bg="black", fg="#00FF00", font=("Consolas", 14, "bold"), pady=5).pack(fill=tk.X)
		
        # --- INFÓ SOR (LÁMPÁK + WALLET EGYENLEG) ---
		
        stat_line = tk.Frame(root, bg="black")
        stat_line.pack(fill=tk.X, pady=(0, 10))

        # 1. Lámpák (balról)
        self.rpc_dot = tk.Label(stat_line, text="● RPC", fg="#555555", bg="black", font=("Consolas", 10, "bold"))
        self.rpc_dot.pack(side="left", padx=(20, 5))

        self.pp_dot = tk.Label(stat_line, text="● PPORTAL", fg="#555555", bg="black", font=("Consolas", 10, "bold"))
        self.pp_dot.pack(side="left", padx=5)

        self.front_dot = tk.Label(stat_line, text="● FRONT", fg="#555555", bg="black", font=("Consolas", 10, "bold"))
        self.front_dot.pack(side="left", padx=5)
        
        # --- JUPITER KEY BEVITEL (A lámpák és a wallet egyenleg közé) ---
		
        tk.Label(stat_line, text="JUPITER KEY:", bg="black", fg="white", font=("Consolas", 10)).pack(side="left", padx=(20, 0))
        self.jup_key_input = tk.Entry(stat_line, bg="#202020", fg="#FFA500", font=("Consolas", 10), width=36)
        # Ha van alapértelmezett kulcsod a konfigurációban, azt ide beírhatod:
        self.jup_key_input.insert(0, JUPITER_API_KEY) 
        self.jup_key_input.pack(side="left", padx=5)
        
        # 2. Wallet felirat (közvetlenül melléjük)
		
        self.balance_var = tk.StringVar(value="WALLET: LOADING...")
        tk.Label(stat_line, textvariable=self.balance_var, bg="black", fg="#00FFFF", font=("Consolas", 12, "bold")).pack(side="left", padx=5)
        wallet_frame = tk.Frame(root, bg="black")
        wallet_frame.pack(fill=tk.X, padx=20, pady=5)
        
        # --- SLOTS LIMIT BEVITEL (A wallet egyenleg után) ---
		
        tk.Label(stat_line, text="MAX(10) SLOTS:", bg="black", fg="white", font=("Consolas", 10)).pack(side="left", padx=(20, 0))
        self.slots_limit_input = tk.Entry(stat_line, bg="#202020", fg="#00FFFF", font=("Consolas", 10), width=5)
        self.slots_limit_input.insert(0, "5") # Alapértelmezett 5
        self.slots_limit_input.pack(side="left", padx=5)
        
        tk.Label(stat_line, text="DEV FEE 0,50%", bg="black", fg="#00FF00", font=("Consolas", 10, "bold")).pack(side="left", padx=(15, 0))
        
        readme_btn = tk.Button(stat_line, text="!! README !!", bg="#333333", fg="white", 
                               font=("Consolas", 9, "bold"), command=self.show_readme_window, cursor="hand2")
        readme_btn.pack(side="left", padx=(10, 0))
		
        # --- DINAMIKUS SZŰRŐK (self. használatával, hogy elérhető legyen) ---
		
        tk.Label(stat_line, text="MIN AGE(s):", bg="black", fg="white", font=("Consolas", 9)).pack(side="left", padx=(15, 0))
        self.age_min_input = tk.Entry(stat_line, bg="#202020", fg="#00FFFF", font=("Consolas", 9), width=4)
        self.age_min_input.insert(0, "60")
        self.age_min_input.pack(side="left", padx=2)

        tk.Label(stat_line, text="MAX AGE(s):", bg="black", fg="white", font=("Consolas", 9)).pack(side="left", padx=(5, 0))
        self.age_max_input = tk.Entry(stat_line, bg="#202020", fg="#00FFFF", font=("Consolas", 9), width=4)
        self.age_max_input.insert(0, "600")
        self.age_max_input.pack(side="left", padx=2)

        tk.Label(stat_line, text="MIN MC($):", bg="black", fg="white", font=("Consolas", 9)).pack(side="left", padx=(5, 0))
        self.mc_min_input = tk.Entry(stat_line, bg="#202020", fg="#00FFFF", font=("Consolas", 9), width=7)
        self.mc_min_input.insert(0, "10000")
        self.mc_min_input.pack(side="left", padx=2)
		
        # --- KAPCSOLAT JELZŐK ---
		
        status_container = tk.Frame(wallet_frame, bg="black")
        status_container.pack(side="left", padx=10)

        # Keressük meg a wallet_frame részt, és bővítsük:
        tk.Label(wallet_frame, text="AMOUNT (SOL):", bg="#101010", fg="white", font=("Consolas", 10)).pack(side="left", padx=(15, 0))
        self.amount_input = tk.Entry(wallet_frame, bg="#202020", fg="#00FF00", font=("Consolas", 10), width=10)
        self.amount_input.insert(0, "0.01") # Alapértelmezett érték
        self.amount_input.pack(side="left", padx=5)
        # Keressük meg a wallet_frame-et az __init__-ben:
        tk.Label(wallet_frame, text="EXIT (X):", bg="#101010", fg="white", font=("Consolas", 10)).pack(side="left", padx=(15, 0))
        self.multiplier_input = tk.Entry(wallet_frame, bg="#202020", fg="#FFFF00", font=("Consolas", 10), width=5)
        self.multiplier_input.insert(0, "2") # Alapértelmezett: 2x
        self.multiplier_input.pack(side="left", padx=5)

        tk.Label(wallet_frame, text="PRIVATE KEY:", bg="black", fg="white", font=("Consolas", 10)).pack(side="left")

        # Beviteli mező (show="*" elrejti a karaktereket)
        self.key_input = tk.Entry(wallet_frame, bg="#202020", fg="#00FF00", font=("Consolas", 10), width=50, show="*")
        self.key_input.pack(side="left", padx=10)

        # Connect gomb
        self.connect_btn = tk.Button(wallet_frame, text="🔗 CONNECT WALLET", bg="#004400", fg="#00FF00", 
                             font=("Consolas", 9, "bold"), command=self.handle_connect)
        self.connect_btn.pack(side="left")
        
        h_frame = tk.Frame(root, bg="#202020"); h_frame.pack(fill=tk.X, padx=(5, 25))
        
        # Stop Loss beviteli mező az EXIT mellé
        tk.Label(wallet_frame, text="STOP LOSS (%):", bg="#101010", fg="white", font=("Consolas", 10)).pack(side="left", padx=(15, 0))
        self.stoploss_input = tk.Entry(wallet_frame, bg="#202020", fg="#FF5555", font=("Consolas", 10), width=5)
        self.stoploss_input.insert(0, "-30") # Alapértelmezett -30%
        self.stoploss_input.pack(side="left", padx=5)
        
        # FEJLÉC ÉPÍTÉS
		
        for idx, col in enumerate(self.columns):
            tk.Label(h_frame, text=col, bg="#202020", fg="white", font=("Consolas", 10, "bold"), anchor="w").grid(row=0, column=idx, sticky="ew", padx=2, pady=5)
            h_frame.grid_columnconfigure(idx, minsize=self.col_widths[idx], weight=0)

        # --- ÚJ GÖRGETŐ RENDSZER (LE-FEL és JOBBRA-BALRA) ---
        
        # 1. Konténer keret a táblázatnak (hogy egyben kezelje a sávokat)
        table_container = tk.Frame(root, bg="black")
        table_container.pack(fill="both", expand=True, padx=5, pady=5)

        # 2. A Canvas és a görgetősávok létrehozása
        self.canvas = tk.Canvas(table_container, bg="black", highlightthickness=0)
        
        # Függőleges (Vertical) görgető - Jobb oldalt
        v_sb = ttk.Scrollbar(table_container, orient="vertical", command=self.canvas.yview)
        
        # Vízszintes (Horizontal) görgető - Alul (EZ AZ ÚJ!)
        h_sb = ttk.Scrollbar(table_container, orient="horizontal", command=self.canvas.xview)

        # A belső keret, amibe az adatok kerülnek
        self.scrollable_frame = tk.Frame(self.canvas, bg="black")

        # Görgetési tartomány frissítése, ha változik a tartalom mérete
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        # Ablak létrehozása a vásznon belül
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        # Összekötjük a Canvas-t a két görgetővel
        self.canvas.configure(yscrollcommand=v_sb.set, xscrollcommand=h_sb.set)

        # 3. Elhelyezés Rácsban (Grid), hogy minden a helyére kerüljön
        # Canvas: Bal fent (kitölti a helyet)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        
        # Függőleges sáv: Jobb oldalt (fentről le)
        v_sb.grid(row=0, column=1, sticky="ns")
        
        # Vízszintes sáv: Alul (balról jobbra)
        h_sb.grid(row=1, column=0, sticky="ew")

        # Beállítjuk, hogy a Canvas rugalmasan nőjön
        table_container.grid_rowconfigure(0, weight=1)
        table_container.grid_columnconfigure(0, weight=1)
        
        for idx in range(len(self.columns)): self.scrollable_frame.grid_columnconfigure(idx, minsize=self.col_widths[idx], weight=0)
        
        # ELVÁLASZTÓ GEMS SZAKASZ
		
        self.separator = tk.Frame(self.scrollable_frame, bg="black")
        tk.Label(self.separator, text="💎 TRADEABLE COIN AFTER 600s or 50K ", bg="black", fg="#FF00FF", font=("Consolas", 12, "bold")).pack(side="left")
        tk.Frame(self.separator, bg="#FF00FF", height=2).pack(side="left", fill="x", expand=True, padx=10, pady=10)
        
        # METEORA ELVÁLASZTÓ (ÚJ)
		
        self.meteora_separator = tk.Frame(self.scrollable_frame, bg="black")
        tk.Label(self.meteora_separator, text="☄️ METEORA POOLS", bg="black", fg="#00FFFF", font=("Consolas", 12, "bold")).pack(side="left")
        tk.Frame(self.meteora_separator, bg="#00FFFF", height=2).pack(side="left", fill="x", expand=True, padx=10, pady=10)
        self.root.after(1000, self.update_wallet_ui); self.update_ui()

    def _safe_text(self, text, limit):
        s = str(text)
        if len(s) > limit:
            return s[:limit-1] + "."
        return s

    async def _async_trade_action(self, mint, status_label):
        # --- ÚJ: ELLENŐRZÉS, HOGY VAN-E TÁRCA ---
        if not wallet.keypair:
            status_label.config(text="CONNECT WALLET!", fg="orange")
            #await asyncio.sleep(3) # 3 másodpercig kint marad a figyelmeztetés
            #status_label.config(text="READY", fg="gray")
            return
            
        try:
            # 1. Paraméterek beolvasása
            try:
                trade_amount = float(self.amount_input.get())
                exit_multiplier = float(self.multiplier_input.get())
                sl_value = float(self.stoploss_input.get())
                
            except Exception:
                sl_value = -30.0 # Biztonsági tartalék, ha elírnád
                status_label.config(text="INV. PARAMS", fg="red")
                return

            status_label.config(text="BUYING...", fg="yellow")
            
            # 2. Vétel megkísérlése (Most már szimulációval a buy_token-ben!)
            success, msg = await wallet.buy_token(mint, trade_amount)
            
            if success:
                # CSAK SIKER ESETÉN regisztráljuk a trade-et
                if mint in slots:
                    active_trades[mint] = {
                        "entry_mc": slots[mint]["mc"],
                        "amount_sol": trade_amount, # <--- EZT MENTJÜK EL! 
                        "status": "SUCCESS BUY ✅", 
                        "profit_pct": 0.0, 
                        "done": False, 
                        "target_mult": exit_multiplier,
                        "stop_loss": sl_value  # <--- EZT ADJUK HOZZÁ
                    }
                
                # Várakozás a megerősítés utáni státuszváltásra
                await asyncio.sleep(3) 
                if mint in active_trades:
                    active_trades[mint]["status"] = "HOLDING"
                
                # Egyenleg frissítése
                    await asyncio.sleep(2) 
                    await self._fetch_balance() 
            else:
                # Ha a buy_token False-t adott (pl. Slippage error a szimulációban)
                status_label.config(text=msg, fg="red")
                # Biztosítjuk, hogy ne maradjon szemét az active_trades-ben
                if mint in active_trades:
                    del active_trades[mint]

        except Exception as e:
            # Végső mentőöv hiba esetén
            print(f"DEBUG ERROR: {e}")
            status_label.config(text="SYSTEM ERR", fg="red")
            
    def execute_trade(self, mint, status_widget):
        if global_loop and global_loop.is_running(): asyncio.run_coroutine_threadsafe(self._async_trade_action(mint, status_widget), global_loop)
    
    async def _async_sell_action(self, mint, status_label):
        status_label.config(text="SELLING...", fg="magenta")
        success, msg = await wallet.sell_token(mint)
        if success:
            status_label.config(text="MANUAL SELL ✅", fg="#00FF00")
            await asyncio.sleep(2) 
            await self._fetch_balance() 
            if mint in active_trades:
                active_trades[mint]["status"] = "MANUAL SELL 💰"
                active_trades[mint]["done"] = True
        else: 
            status_label.config(text=f"SELL ERR: {msg}", fg="red")

    def execute_sell(self, mint, status_widget):
        if global_loop and global_loop.is_running(): asyncio.run_coroutine_threadsafe(self._async_sell_action(mint, status_widget), global_loop)

    def update_wallet_ui(self):
        def run_update():
            if global_loop and global_loop.is_running(): asyncio.run_coroutine_threadsafe(self._fetch_balance(), global_loop)
        threading.Thread(target=run_update).start()

    async def _fetch_balance(self):
        bal = await wallet.update_balance(); self.balance_var.set(f"WALLET: {bal:.4f} SOL" if wallet.public_key else "WALLET: NO KEY")

    def copy_to_clipboard(self, content, btn_widget):
        try:
            # Megjegyezzük az eredeti szöveget és színt, mielőtt átírjuk
            old_text = btn_widget.cget("text")
            old_fg = btn_widget.cget("fg")

            if pyperclip: pyperclip.copy(content)
            else:
                self.root.clipboard_clear(); self.root.clipboard_append(content)
            
            # Átírjuk: Mostantól 2 másodpercig (2000ms) látszódni fog
            btn_widget.config(text="COPIED!", fg="#00FF00")
            
            # Itt állítjuk vissza az eredetire 2 mp után
            self.root.after(2000, lambda: btn_widget.config(text=old_text, fg=old_fg) if btn_widget.winfo_exists() else None)
        except Exception as e: print(f"Copy error: {e}")
        
##################PRIVATE KEY PLACE##########################

    def handle_connect(self):
        key = self.key_input.get()
        if not key:
            self.balance_var.set("WALLET: PLEASE ENTER A KEY")
            return

        success, msg = wallet.load_key(key)
        if success:
            self.balance_var.set(f"WALLET: LOADING BALANCE...")
            self.key_input.delete(0, tk.END) # Biztonság: töröljük a mezőből
            self.key_input.config(state="disabled") # Letiltjuk a mezőt, ha már csatlakozott
            self.connect_btn.config(text="✅ CONNECTED", state="disabled")
            # Frissítjük az egyenleget
            self.update_wallet_ui()
        else:
            self.balance_var.set(f"WALLET: {msg}")
                
#############MANUAL DELETE####################   
     
    def manual_delete(self, mint):
        if mint in slots:
            slots[mint]["active"] = False # Jelzünk a monitor loopnak
            # Várunk egy picit, hogy a loopok átugorhassák
            def final_remove():
                if mint in slots:
                    del slots[mint]
            # 500ms múlva végleg töröljük, miután a loopok észlelték az inaktivitást
            self.root.after(500, final_remove)
            print(f"🗑️ Token eltávolítva: {mint[:8]}...")
            
##############README##############
    def show_readme_window(self):
        """Felugró ablak a Readme megjelenítésére"""
        # Új ablak (Toplevel) létrehozása a főablak felett
        rw = tk.Toplevel(self.root)
        rw.title("📖 USER MANUAL / README")
        rw.geometry("650x550")
        rw.configure(bg="#050505") # Sötét háttér

        # Címke a tetejére
        tk.Label(rw, text="USER MANUAL", bg="#050505", fg="white", font=("Consolas", 14, "bold"), pady=10).pack()

        # Szövegdoboz és görgetősáv kerete
        frame = tk.Frame(rw, bg="#050505")
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Görgetősáv
        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side="right", fill="y")

        # Szövegdoboz
        text_area = tk.Text(frame, bg="#101010", fg="#00FF00", font=("Consolas", 10), 
                            yscrollcommand=scrollbar.set, padx=10, pady=10, relief="flat")
        text_area.pack(side="left", fill="both", expand=True)
        
        # Összekötjük a görgetőt a szöveggel
        scrollbar.config(command=text_area.yview)

        # Szöveg beillesztése a globális változóból
        text_area.insert(tk.END, README_TEXT)
        
        # Írásvédetté tesszük, hogy a user ne tudjon beleírni, csak olvasni
        text_area.config(state="disabled")
  
################
  
    def create_row(self, parent, row_idx, row_data, color, mint):
        widgets = {}
        for col_idx, val in enumerate(row_data):
            fix_w = int(self.col_widths[col_idx] / 9)
            display_text = str(val)
            
            # JAVÍTÁS: A 7-es oszlop a STATUS. Itt vágjuk le!
            if col_idx == 7: 
                display_text = self._safe_text(val, 20)

            if col_idx == 6: # DEV tárca gomb
                btn = tk.Button(parent, text=display_text, bg="#303030", fg="cyan", font=("Consolas", 8), cursor="hand2", width=fix_w)
                btn.grid(row=row_idx, column=col_idx, sticky="ew", padx=2, pady=1)
                widgets[f"col_{col_idx}"] = btn
            else: # Sima adatmezők
                lbl = tk.Label(parent, text=display_text, bg="black", fg=color, font=("Consolas", 10), anchor="w", width=fix_w)
                lbl.grid(row=row_idx, column=col_idx, sticky="ew", padx=2, pady=1)
                widgets[f"col_{col_idx}"] = lbl
        
        # --- GOMBOK JAVÍTOTT POZÍCIÓJA (8, 9, 10-es oszlopok) ---
        # 9: MINT COPY
        w_9 = int(self.col_widths[9] / 9)
        c_btn = tk.Button(parent, text="💊 SCAN", bg="#404040", fg="#FF00FF", font=("Consolas", 8, "bold"), width=w_9, cursor="hand2")
    
        # Megnézzük a globális slots-ban, hogy ez Meteora token-e
        is_meteora = False
        if mint in slots and slots[mint].get("source") == "meteora":
            is_meteora = True
            
        if is_meteora:
            # Ha Meteora, akkor a Jup.ag oldalát nyitjuk meg
            c_btn.config(command=lambda m=mint: webbrowser.open(f"https://jup.ag/tokens/{m}"))
        else:
            # Ha Pump.fun, akkor marad a régi
            c_btn.config(command=lambda m=mint: webbrowser.open(f"https://pump.fun/coin/{m}"))
        
        c_btn.grid(row=row_idx, column=9, sticky="w", padx=2, pady=1); widgets["btn"] = c_btn
        
        # 10: TRADE GOMB
        w_10 = int(self.col_widths[10] / 9)
        t_btn = tk.Button(parent, text="🚀 TRADE", bg="#004400", fg="#00FF00", font=("Consolas", 8, "bold"), width=w_10)
        t_btn.grid(row=row_idx, column=10, sticky="w", padx=2, pady=1); widgets["trade_btn"] = t_btn
        
        # 11: TRADE STATUS
        w_11 = int(self.col_widths[11] / 9)
        ts_lbl = tk.Label(parent, text="READY", bg="black", fg="gray", font=("Consolas", 8), width=w_11)
        ts_lbl.grid(row=row_idx, column=11, sticky="w", padx=2, pady=1); widgets["trade_status"] = ts_lbl
        
        # --- EZT SZÚRD BE A create_row VÉGÉRE ---
        # 12: DELETE GOMB (12. oszlop)
        w_12 = int(self.col_widths[12] / 9)
        del_btn = tk.Button(parent, text="🗑️", bg="#202020", fg="#FF5555", 
                            font=("Consolas", 8, "bold"), width=w_12, cursor="hand2")
        # Itt hívjuk meg a törlési funkciót
        del_btn.config(command=lambda m=mint: self.manual_delete(m))
        del_btn.grid(row=row_idx, column=12, sticky="w", padx=2, pady=1)
        widgets["del_btn"] = del_btn

        return widgets
        
    ###MAX SLOT####
    def get_max_slots_limit(self):
        try:
            val = int(self.slots_limit_input.get())
            # Minimum 1, maximum 10
            return max(1, min(10, val))
        except:
            return 5 # Ha hiba van a beírásnál, marad az 5
    ########FILTER FORSEC##################         
    def get_filter_settings(self):
        """Kiolvassa a GUI-ról a beállított szűrőket. Ha hiba van, alapértéket ad."""
        try:
            return (
                float(self.age_min_input.get()),
                float(self.age_max_input.get()),
                float(self.mc_min_input.get())
            )
        except Exception:
            return 60.0, 600.0, 10000.0 # Biztonsági tartalék
        
    def update_ui(self):
		
		# --- EZT SZÚRD BE AZ ELEJÉRE ---
        self.rpc_dot.config(fg="#00FF00" if connection_status.get("rpc") else "#FF0000")
        self.pp_dot.config(fg="#00FF00" if connection_status.get("pumportal") else "#FF0000")
        self.front_dot.config(fg="#00FF00" if connection_status.get("frontend") else "#FF0000")
        # ------------------------------
        limit = self.get_max_slots_limit()
        self.header_var.set(f"💊 PUMPFUN SNIPER | {len(slots)}/{limit} | {time.strftime('%H:%M:%S')}")
        # --- MÓDOSÍTOTT LISTA KEZELÉS ---
        # 1. Különválogatjuk a Meteora és a Pump tokeneket
        meteora_mints = [m for m, d in slots.items() if d.get("source") == "meteora"]
        pump_items = [x for x in slots.items() if x[1].get("source") != "meteora"]
        
        # 2. A Pump itemeket rendezzük idő szerint a felső listákhoz
        all_items_sorted = sorted(pump_items, key=lambda x: x[1]['start_time'], reverse=True)
        
        # A te eredeti szűrőid, de most már csak a pump_items-ből dolgoznak:
        filtered_items = [x for x in all_items_sorted if "TRADEABLE" not in str(x[1].get('status', '')) and "GRADUATED" not in str(x[1].get('status', ''))]
        top_10_mints = [m for m, d in filtered_items[:10]]
        
        # A Gems lista is csak Pump tokeneket tartalmazzon itt:
        gem_mints = [x[0] for x in pump_items if "TRADEABLE" in str(x[1].get('status', '')) or "GRADUATED" in str(x[1].get('status', ''))]
        
        # --- FELSŐ LISTA ---
        for row_idx, mint in enumerate(top_10_mints):
            if mint not in slots: continue
            data = slots[mint]
            creator = data.get('creator', 'N/A')
            short_dev = f"{creator[:4]}..{creator[-4:]}" if len(creator) > 10 else creator
            
            # RD LISTA (Pontosan 8 elem, ami a columns első 8 elemének felel meg)
            rd = [
                data.get('symbol', '...'), 
                format_usd(data['mc']), 
                format_usd(data['ath']), 
                f"{int(time.time()-data['start_time'])}s", 
                "/".join(data['live_bots']) if data['live_bots'] else "---", 
                # Az rd listában a 6. elem (BOT ACTIONS oszlop) logikáját cseréld erre:
                "/".join(data['history_bots']) if data['history_bots'] and "SCAN_ERR" not in data['history_bots'] else (
                "❌ ERROR (RPC)" if "SCAN_ERR" in data.get('history_bots', []) else (
                "CLEAN ✅" if data['dev_checked'] else "⏳ SCAN...")
                 ),
                short_dev,
                f"${data.get('dev_usd', '0')}", # <--- EZ AZ ÚJ OSZLOP ADATA
                data['status']
            ]

            if mint not in self.gui_rows:
                self.gui_rows[mint] = self.create_row(self.scrollable_frame, row_idx, rd, "white", mint)
                # Solscan megnyitása másolás helyett
                self.gui_rows[mint]["col_6"].config(command=lambda c=creator: webbrowser.open(f"https://solscan.io/account/{c}"))
            else:
                widgets = self.gui_rows[mint]
                for c_idx, val in enumerate(rd):
                    display_text = str(val)
                    if c_idx == 8: # STATUS levágása frissítéskor is
                        display_text = self._safe_text(val, 20)
                    widgets[f"col_{c_idx}"].config(text=display_text)
                # --- EZT A SORT ILLESZD BE IDE ---
                widgets["col_6"].config(command=partial(self.copy_to_clipboard, creator, widgets["col_6"]))
                self._update_trade_buttons(mint, widgets)
                for w in widgets.values(): w.grid_configure(row=row_idx)

        # TAKARÍTÁS FELSŐ
        for mint in list(self.gui_rows.keys()):
            if mint not in top_10_mints:
                for w in self.gui_rows[mint].values(): w.destroy()
                del self.gui_rows[mint]

        # ELVÁLASZTÓ MEGJELENÍTÉSE
        if gem_mints:
            self.separator.grid(row=11, column=0, columnspan=11, sticky="ew", padx=5)
        else:
            self.separator.grid_forget()

# --- ALSÓ LISTA (GEMS) ---
        for idx, mint in enumerate(gem_mints):
            data = slots[mint]
            r_idx = 12 + idx
            creator = data.get('creator', 'N/A')
            short_dev = f"{creator[:4]}..{creator[-4:]}" if len(creator) > 10 else creator

            # SZÍN MEGHATÁROZÁSA: Ha van bot (live vagy history), akkor PIROS, egyébként ZÖLD
            row_color = "#55FF55"  # Alapértelmezett zöld
            if data.get('live_bots') or data.get('history_bots'):
                row_color = "#FF5555" # Piros, ha botot találtunk

            rd = [
                data.get('symbol', '...'), 
                format_usd(data['mc']), 
                format_usd(data['ath']), 
                f"{int(time.time()-data['start_time'])}s", 
                "/".join(data['live_bots']) if data['live_bots'] else "---", 
                "/".join(data['history_bots']) if data['history_bots'] else ("CLEAN ✅" if data['dev_checked'] else "⏳ SCAN..."), 
                short_dev,
                f"${data.get('dev_usd', '0')}", # <--- EZ AZ ÚJ OSZLOP ADATA
                data['status']
            ]

            if mint not in self.gems_rows:
                # Itt használjuk a dinamikus row_color-t
                self.gems_rows[mint] = self.create_row(self.scrollable_frame, r_idx, rd, row_color, mint)
                # Solscan megnyitása másolás helyett
                self.gems_rows[mint]["col_6"].config(command=lambda c=creator: webbrowser.open(f"https://solscan.io/account/{c}"))
            else:
                widgets = self.gems_rows[mint]
                for c_idx, val in enumerate(rd):
                    display_text = str(val)
                    if c_idx == 8: 
                        display_text = self._safe_text(val, 20)
                    
                    # Frissítjük a szöveget ÉS a színt is, ha változna
                    widgets[f"col_{c_idx}"].config(text=display_text, fg=row_color)
                
                self._update_trade_buttons(mint, widgets)
                for w in widgets.values(): w.grid_configure(row=r_idx)

        # TAKARÍTÁS ALSÓ
        for mint in list(self.gems_rows.keys()):
            if mint not in gem_mints:
                for w in self.gems_rows[mint].values(): w.destroy()
                del self.gems_rows[mint]
                
         # --- IDE ILLESZD BE AZ ÚJ RÉSZT (METEORA SZEKCIÓ) ---
        
        # Kiszámoljuk, hol kezdődjön (az előző lista vége + 2 sor hely)
        last_row_index = 12 + len(gem_mints) + 2
        
        # ELVÁLASZTÓ MEGJELENÍTÉSE
        if meteora_mints:
            self.meteora_separator.grid(row=last_row_index, column=0, columnspan=13, sticky="ew", padx=5)
        else:
            self.meteora_separator.grid_forget()

        # METEORA LISTA LOOP
        for idx, mint in enumerate(meteora_mints):
            data = slots[mint]
            r_idx = last_row_index + 1 + idx # Az elválasztó alá kerülnek
            
            creator = data.get('creator', 'N/A')
            short_dev = f"{creator[:4]}..{creator[-4:]}" if len(creator) > 10 else creator
            
            # Cián szín a Meteorának, hogy megkülönböztessük
            row_color = "#00FFFF" 

            rd = [
                data.get('symbol', '...'), 
                format_usd(data['mc']), 
                format_usd(data['ath']), 
                f"{int(time.time()-data['start_time'])}s", 
                "/".join(data['live_bots']) if data['live_bots'] else "---", 
                # --- EZT A SORT JAVÍTOTTUK ---
                # Most már ugyanazt a logikát használja, mint a Pump-os coinok:
                # Kiírja a botokat (pl. JITO, MEV), vagy ha tiszta, akkor CLEAN, ha még fut, akkor SCAN.
                "/".join(data['history_bots']) if data['history_bots'] else ("CLEAN ✅" if data['dev_checked'] else "⏳ SCAN..."), 
                # -----------------------------
                short_dev,
                f"${data.get('dev_usd', '0')}",
                data['status']
            ]

            if mint not in self.meteora_rows:
                self.meteora_rows[mint] = self.create_row(self.scrollable_frame, r_idx, rd, row_color, mint)
                # Solscan link
                self.meteora_rows[mint]["col_6"].config(command=lambda c=creator: webbrowser.open(f"https://solscan.io/account/{c}"))
            else:
                widgets = self.meteora_rows[mint]
                for c_idx, val in enumerate(rd):
                    display_text = str(val)
                    if c_idx == 8: display_text = self._safe_text(val, 20)
                    widgets[f"col_{c_idx}"].config(text=display_text, fg=row_color)
                
                self._update_trade_buttons(mint, widgets)
                for w in widgets.values(): w.grid_configure(row=r_idx)

        # TAKARÍTÁS (METEORA)
        for mint in list(self.meteora_rows.keys()):
            if mint not in meteora_mints:
                for w in self.meteora_rows[mint].values(): w.destroy()
                del self.meteora_rows[mint]
                
        self.root.after(200, self.update_ui)

    def _update_trade_buttons(self, mint, widgets):
        t_data = active_trades.get(mint)
        is_owned = t_data and not t_data.get("done", False)
        
        # --- FIX: Itt definiáljuk az elején, hogy minden ág lássa! ---
        status_text = t_data.get("status", "READY") if t_data else "READY"
        # ------------------------------------------------------------
        
        if is_owned:
            profit = t_data.get("profit_pct", 0.0)
            p_color = "#00FF00" if profit >= 0 else "#FF5555"
            widgets["trade_btn"].config(text="🔻 SELL NOW", bg="#880000", fg="white", 
                                        command=partial(self.execute_sell, mint, widgets["trade_status"]))
            # Ha éppen BUYING vagy SUCCESS van folyamatban, azt mutassuk
            if "BUYING" in status_text or "SUCCESS" in status_text:
                widgets["trade_status"].config(text=status_text, fg="yellow")
            else:
                widgets["trade_status"].config(text=f"HOLD ({profit:+.1f}%)", fg=p_color)
        else:
            widgets["trade_btn"].config(text="🚀 BUY ", bg="#004400", fg="#00FF00", 
                                        command=partial(self.execute_trade, mint, widgets["trade_status"]))
            
            # --- STICKY ERROR LOGIKA ---
            if t_data:
                status_text = t_data.get("status", "READY")
                # Ha hiba van (ERR vagy CANCELED), hagyjuk kint, ne töröljük le azonnal
                if any(x in status_text for x in ["ERR", "CANCELED", "MIGRATED", "FAIL"]):
                    widgets["trade_status"].config(text=status_text, fg="red")
                elif "SOLD" in status_text:
                    widgets["trade_status"].config(text="SOLD ✅", fg="gray")
                else:
                    widgets["trade_status"].config(text="READY", fg="gray")
            else:
                widgets["trade_status"].config(text="READY", fg="gray")
                              
def start_async_loop():
    global global_loop
    # JAVÍTÁS: Kimenet nincs elnémítva
    try:
        loop = asyncio.new_event_loop(); global_loop = loop; asyncio.set_event_loop(loop); loop.run_until_complete(main())
    except KeyboardInterrupt: pass

if __name__ == "__main__":
    threading.Thread(target=start_async_loop, daemon=True).start()
    root = tk.Tk(); app = StableSniperGUI(root)
    try: root.mainloop()
    except KeyboardInterrupt: sys.exit(0)


