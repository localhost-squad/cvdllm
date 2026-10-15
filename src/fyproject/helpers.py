import subprocess
import tempfile
import os
import base64
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes, serialization

def get_tpm_public_key_text(handle: str = "0x81010002") -> str:
    """Extracts the public key as a single-line Base64 text string."""
    with tempfile.TemporaryDirectory() as tmpdir:
        der_path = os.path.join(tmpdir, "public.der")
        cmd = [
            "tpm2_readpublic",
            "-c", handle,
            "-f", "der",
            "-o", der_path,
            "-T", "device:/dev/tpmrm0"
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        with open(der_path, "rb") as f:
            # Returns a clean single text string like "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8A..."
            return base64.b64encode(f.read()).decode("utf-8")


def verify_tpm_signature_text(hash_bytes: bytes, signature_bytes: bytes, public_key_b64: str) -> int:
    """Verifies signature using the Base64 public key text string.
    
    Returns 1 if VALID, 0 if INVALID.
    """
    try:
        # Decode the Base64 text back into raw DER bytes
        der_bytes = base64.b64decode(public_key_b64)
        public_key = serialization.load_der_public_key(der_bytes)
        
        public_key.verify(
            signature_bytes,
            hash_bytes,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        return 1
    except Exception:
        return 0