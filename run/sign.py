#!/usr/bin/env python3
from tpm2_pytss import ESAPI, TPM2B_DIGEST, TPMT_SIG_SCHEME, TPM2_ALG
from dotenv import load_dotenv
import os
import sys
import base64

def sign_hash(nvram_address: str, tcti: str, hash_hex: str):
    addr = int(nvram_address, 0)
    digest = bytes.fromhex(hash_hex)

    with ESAPI(tcti) as ectx:
        handle = ectx.tr_from_tpmpublic(addr)

        scheme = TPMT_SIG_SCHEME(scheme=TPM2_ALG.RSASSA)
        scheme.details.any.hashAlg = TPM2_ALG.SHA256

        signature = ectx.sign(
            handle,
            TPM2B_DIGEST(digest),
            scheme,
            None,  # validation
        )

        sig_bytes = bytes(signature.signature.rsassa.sig)
        return base64.b64encode(sig_bytes).decode()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <64_char_hex_hash>", file=sys.stderr)
        sys.exit(1)

    load_dotenv()
    addr = os.getenv("TPM_NVRAM_ADDRESS")
    tcti = os.getenv("TPM2TOOLS_TCTI")
    print(sign_hash(addr, tcti, sys.argv[1]))

# usage
# python run/sign.py 2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824