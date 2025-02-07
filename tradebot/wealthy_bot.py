import os
import time
import requests
import base64
from solana.rpc.api import Client
from solders.transaction import Transaction
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from dotenv import load_dotenv
from token_config import TOKEN_SETTINGS, TokenConfig

# Load environment variables
load_dotenv()

# Initialize Solana connection
solana_client = Client(os.getenv("SOLANA_RPC_URL"))

# Load wallet
private_key_base64 = os.getenv("PRIVATE_KEY")

# Decode the base64 private key into bytes
private_key_bytes = base64.b64decode(private_key_base64)

# Debugging print: Check length of private key
print(f"Private key length: {len(private_key_bytes)} bytes")

# Ensure the private key is 64 bytes
if len(private_key_bytes) != 64:
    raise ValueError("Invalid private key length: must be 64 bytes")

# Create the Keypair from the bytes
wallet = Keypair.from_bytes(private_key_bytes)

# Trade state tracking
active_trades = {}

# Fetch token price from Jupiter Price API
def fetch_token_price(token_mint: str) -> float:
    try:
        url = f"https://price.jup.ag/v6/price?ids={token_mint}"
        response = requests.get(url)
        response.raise_for_status()  # Will raise an exception for HTTP errors
        data = response.json()
        return float(data["data"][token_mint]["price"])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching token price for {token_mint}: {e}")
        return 0  # Return 0 or a fallback value
    except KeyError as e:
        print(f"Unexpected response structure: {e}")
        return 0  # Return 0 or a fallback value

# Check if trading is allowed (cooldown and max trades)
def should_trade(token: TokenConfig, current_price: float) -> bool:
    last_trade = active_trades.get(token.mint_address, {}).get("last_trade", 0)
    cooldown_ms = token.cooldown_minutes * 60 * 1000
    active_trade_count = active_trades.get(token.mint_address, {}).get("count", 0)

    return (
        (time.time() * 1000 - last_trade) > cooldown_ms
        and current_price <= token.stop_purchase_above
        and active_trade_count < token.max_concurrent_trades
    )

# Execute a swap using Jupiter V6 Swap API
def execute_swap(token: TokenConfig, is_bearish: bool = False):
    input_mint = token.mint_address if is_bearish else "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"  # USDC
    output_mint = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v" if is_bearish else token.mint_address
    amount = int(token.avg_purchase_amount * (1e9 if not is_bearish else 1e6))  # SOL or USDC decimals

    # Fetch quote
    quote_url = f"https://quote-api.jup.ag/v6/quote?inputMint={input_mint}&outputMint={output_mint}&amount={amount}&slippageBps=100"  # 1% slippage
    quote_response = requests.get(quote_url).json()

    if "error" in quote_response:
        print(f"Error fetching quote: {quote_response['error']}")
        return

    # Execute swap
    swap_url = "https://quote-api.jup.ag/v6/swap"
    swap_response = requests.post(
        swap_url,
        json={
            "quoteResponse": quote_response,
            "userPublicKey": str(wallet.public_key),
        },
    ).json()

    if "swapTransaction" in swap_response:
        # Sign and send transaction
        try:
            transaction = Transaction.deserialize(bytes.fromhex(swap_response["swapTransaction"]))
            transaction.sign(wallet)
            solana_client.send_transaction(transaction)
            print(f"Trade executed for {token.name} (Bearish: {is_bearish})")
        except Exception as e:
            print(f"Error signing or sending transaction: {e}")

        # Update trade state
        active_trades[token.mint_address] = {
            "last_trade": time.time() * 1000,
            "count": active_trades.get(token.mint_address, {}).get("count", 0) + 1,
        }

# Main trading loop
def monitor_markets():
    while True:
        for token in TOKEN_SETTINGS:
            try:
                price = fetch_token_price(token.mint_address)
                if should_trade(token, price):
                    if token.direction in ["bear", "both"]:
                        execute_swap(token, is_bearish=True)
                    if token.direction in ["bull", "both"]:
                        execute_swap(token, is_bearish=False)
            except Exception as e:
                print(f"Error processing {token.name}: {e}")
        time.sleep(30)  # Run every 30 seconds

# Start the bot
if __name__ == "__main__":
    monitor_markets()
