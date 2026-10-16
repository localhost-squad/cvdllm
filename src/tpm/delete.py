#!/usr/bin/env python3
from tpm2_pytss import ESAPI, ESYS_TR
from tpm2_pytss.TSS2_Exception import TSS2_Exception
from dotenv import load_dotenv
import os

def evict_tpm_handle(nvram_address: str, tcti: str):
    addr = int(nvram_address, 0)

    with ESAPI(tcti) as ectx:
        try:
            handle = ectx.tr_from_tpmpublic(addr)
            ectx.evict_control(ESYS_TR.RH_OWNER, handle, addr)
            return f"Handle {nvram_address} successfully cleared from TPM NVRAM."
        except TSS2_Exception as e:
            if e.rc == 0x18b:  # TPM_RC_HANDLE
                return f"Handle {nvram_address} does not exist (already cleared)."
            else:
                raise

if __name__ == "__main__":
    load_dotenv()
    addr = os.getenv("TPM_NVRAM_ADDRESS")
    tcti = os.getenv("TPM2TOOLS_TCTI")
    print(f"Evicting TPM persistent handle: {addr}...")
    print(evict_tpm_handle(addr, tcti))