#!/usr/bin/env python3
import os
import sys
import base64
from pathlib import Path
from dotenv import load_dotenv
from tpm2_pytss import ESAPI
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

env_path = Path(__file__).parent.parent / ".env"
if not env_path.exists():
    print(f"ERROR: .env file missing at {env_path}", file=sys.stderr)
    sys.exit(1)

load_dotenv(env_path)

nvram_addr = int(os.getenv("TPM_NVRAM_ADDRESS", "0x81010002"), 16)
tcti_str = os.getenv("TPM2TOOLS_TCTI", "device:/dev/tpmrm0")

with ESAPI(tcti=tcti_str) as ectx:
    key_tr = ectx.tr_from_tpm2_handle(nvram_addr)
    pub_area, _, _ = ectx.read_public(key_tr)

    n = int.from_bytes(pub_area.publicArea.unique.rsa, byteorder="big")
    e = pub_area.publicArea.parameters.rsaDetail.exponent
    if e == 0:
        e = 65537

    pub_key = rsa.RSAPublicNumbers(e, n).public_key()
    der_bytes = pub_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    print(base64.b64encode(der_bytes).decode("utf-8"))