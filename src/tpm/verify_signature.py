#!/usr/bin/env python3
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric.utils import Prehashed
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.exceptions import InvalidSignature
from dotenv import load_dotenv
import os
import sys
import base64
import binascii
from .read_public import read_tpm_public

def verify_signature(hash_hex: str, sig_b64: str, public_key_b64: str) -> str:
    # Strip any newlines, spaces, or tabs introduced by terminal line-wrapping
    clean_sig_b64 = "".join(sig_b64.split())
    clean_hash_hex = hash_hex.strip()

    try:
        digest = bytes.fromhex(clean_hash_hex)
        signature = base64.b64decode(clean_sig_b64, validate=True)
        pem = base64.b64decode(public_key_b64)
    except (ValueError, binascii.Error):
        return "false"

    pub = serialization.load_pem_public_key(pem)

    try:
        pub.verify(
            signature,
            digest,
            padding.PKCS1v15(),
            Prehashed(hashes.SHA256()),
        )
        return "true"
    except InvalidSignature:
        return "false"

def main():
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <64_char_hex_hash> <signature_b64>", file=sys.stderr)
        sys.exit(1)

    load_dotenv()
    nvram_address = os.getenv("TPM_NVRAM_ADDRESS")
    tcti = os.getenv("TPM2TOOLS_TCTI")
    pub_key = read_tpm_public(nvram_address, tcti)
    if not pub_key:
        print("ERROR: TPM_PUBLIC_KEY is not set in .env!", file=sys.stderr)
        sys.exit(1)

    # Join all remaining arguments in case unquoted line breaks split the signature
    raw_sig = "".join(sys.argv[2:])
    print(verify_signature(sys.argv[1], raw_sig, pub_key))

if __name__ == "__main__":
    main()