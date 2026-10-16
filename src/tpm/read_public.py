#!/usr/bin/env python3
from tpm2_pytss import ESAPI
from dotenv import load_dotenv
import os
import base64

def read_tpm_public(nvram_address: str, tcti: str):
    with ESAPI(tcti) as ectx:
        handle = ectx.tr_from_tpmpublic(int(nvram_address, 0))
        pub, _, _ = ectx.read_public(handle)
        pem = pub.publicArea.to_pem()
        public = base64.b64encode(pem).decode()
        ectx.tr_close(handle)
        return public

if __name__ == "__main__":
    load_dotenv()
    addr = os.getenv("TPM_NVRAM_ADDRESS")
    tcti = os.getenv("TPM2TOOLS_TCTI")
    print(read_tpm_public(addr, tcti))