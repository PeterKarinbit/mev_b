from eth_account import Account
import secrets

# Generate a strong private key
priv = secrets.token_hex(32)
private_key = "0x" + priv
acct = Account.from_key(private_key)

# save to .env
with open("mev_bot/.env", "w") as f:
    f.write(f"BOT_ADDRESS={acct.address}\n")
    f.write(f"BOT_PRIVATE_KEY={private_key}\n")

print(f"WALLET_GENERATED_SUCCESSFULLY")
print(f"ADDRESS: {acct.address}")
