#!/usr/bin/env python3
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric.utils import Prehashed
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.exceptions import InvalidSignature
from dotenv import load_dotenv
import os
import sys
import base64

def verify_signature(hash_hex: str, sig_b64: str, public_key_b64: str) -> str:
    digest = bytes.fromhex(hash_hex)
    signature = base64.b64decode(sig_b64)
    pem = base64.b64decode(public_key_b64)

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

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <64_char_hex_hash> <signature_b64>", file=sys.stderr)
        sys.exit(1)

    load_dotenv()
    pub_key = os.getenv("TPM_PUBLIC_KEY")
    if not pub_key:
        print("ERROR: TPM_PUBLIC_KEY is not set in .env!", file=sys.stderr)
        sys.exit(1)

    print(verify_signature(sys.argv[1], sys.argv[2], pub_key))

# usage
# uv run python -m tpm.verify  2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824 XCvCG3hLdkRDku5Z1dtpzlQ7MdGLRcDH4obvgGxFUlifFmWMRTmQE71+wIbml+2n987yuj3moLgd8MD9btSjeTreCtcchpvuNj97IrLgwugmuMd5PYU0iA0h4NuG1DvzHW4pKdTaXLDhRZGqbOOOHgBNiFAtw0F7GoP1wivErmwnD4dlpE82OOHV1PXB/zNbrLcwwVxkwF/PnRvQ7dtg88mL69YWFmPjukym+8e3wlINQQyXGjAPn3dzXH5ysiHGg1bG4aHBWnvFPxscq73aYdKCiVFbYZ2U7dIHdt2LryaJaZQjwC1oHJuXaycVkc4VTrb1VDAlTliCJvpqul7jYA==