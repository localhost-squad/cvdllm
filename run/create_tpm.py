#!/usr/bin/env python3
from tpm2_pytss import ESAPI, ESYS_TR, TPM2B_SENSITIVE_CREATE
from tpm2_pytss.TSS2_Exception import TSS2_Exception
from dotenv import load_dotenv
import os

def provision_tpm_rsa_key(nvram_address: str, tcti: str):
    addr = int(nvram_address, 0)

    with ESAPI(tcti) as ectx:
        # Create primary under owner hierarchy
        primary_handle, _, _, _, _ = ectx.create_primary(
            TPM2B_SENSITIVE_CREATE(),
            "rsa2048:aes128cfb",
        )

        # Create RSA key under the primary
        private, public, _, _, _ = ectx.create(
            primary_handle,
            TPM2B_SENSITIVE_CREATE(),
            "rsa",
        )

        # Load the key
        key_handle = ectx.load(primary_handle, private, public)

        # Persist it
        try:
            ectx.evict_control(ESYS_TR.RH_OWNER, key_handle, addr)
            msg = f"Key successfully persisted to {nvram_address}"
        except TSS2_Exception as e:
            if e.rc == 0x14c:  # TPM_RC_NV_DEFINED
                msg = f"Handle {nvram_address} already exists."
            else:
                raise
        finally:
            # Cleanup transient handles
            ectx.flush_context(key_handle)
            ectx.flush_context(primary_handle)

        return msg

if __name__ == "__main__":
    load_dotenv()
    addr = os.getenv("TPM_NVRAM_ADDRESS")
    tcti = os.getenv("TPM2TOOLS_TCTI")
    print(f"Provisioning TPM RSA key to NVRAM handle: {addr}...")
    print(provision_tpm_rsa_key(addr, tcti))