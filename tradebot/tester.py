import base64

private_key_base64 = "0x1b757236d82c8d801e9187a8e4d1f2f074bd986f0288d237835f3a6f2a3cc7b3"
try:
    private_key_bytes = base64.b64decode(private_key_base64)
    print(f"Decoded private key length: {len(private_key_bytes)} bytes")
except Exception as e:
    print(f"Error decoding base64 private key: {e}")
