## Cryptographically Verifiable Deterministic LLM

Traditional AI models are non-deterministic black boxes that lack audit trails and provenance. The **Cryptographically Verifiable Deterministic LLM (`cvdllm`)** solves this by bridging strict hardware-enforced determinism with hardware-backed cryptographic signing. By enforcing single-threaded CPU execution, zero temperature, and a fixed seed, the system guarantees a byte-for-byte identical output and SHA-256 hash across every run. Each response is bundled into a timestamped payload and securely signed using a physical or emulated **Trusted Platform Module (TPM 2.0)**. The result is absolute accountability: anyone can use the payload, signature, and public key to independently verify the exact integrity and authenticity of the AI's output down to the bit size.

---

## Architecture and Workflows

### 1. System Architecture Overview

The architecture separates inference execution, payload formatting, hardware-isolated cryptographic operations, and external verification into distinct modules.

```mermaid
flowchart TD
    subgraph Client["Client Interface"]
        CLI["CLI Interactive Chat / Determinism Test\n(cvdllm.main / determinism_test)"]
    end

    subgraph Determinism["Deterministic Inference Layer"]
        Constraints["Execution Controls:\nSingle-thread CPU (n_threads=1)\nGreedy decoding (temperature=0.0)\nFixed seed (seed=1337)\nLocked memory (mlock=True)"]
        Engine["llama.cpp Inference Engine\n(Qwen2.5-0.5B-Instruct-GGUF)"]
        OutputText["Deterministic Text Output"]
    end

    subgraph PayloadLayer["Payload and Hashing Layer"]
        Payload["Canonical JSON Payload\n{response, timestamp}"]
        Hasher["SHA-256 Hash Digest Engine"]
    end

    subgraph TPMLayer["Hardware Security Module (TPM 2.0)"]
        NVRAM["Persistent NVRAM Handle\n(0x81010002)"]
        Key["RSA-2048 Private Signing Key\n(Hardware Isolated)"]
        SignEngine["TPM RSASSA Signing Engine\n(tpm2-pytss / ESAPI)"]
    end

    subgraph VerificationLayer["Independent Verification Layer"]
        PubKey["TPM Public Key\n(PEM / Base64)"]
        Verifier["Signature Verification\n(cryptography.hazmat)"]
    end

    CLI -->|"Prompt Input"| Engine
    Constraints -.-> Engine
    Engine -->|"Token Stream"| OutputText
    OutputText -->|"Assemble JSON"| Payload
    Payload -->|"UTF-8 Bytes"| Hasher
    Hasher -->|"32-Byte Hash Digest"| SignEngine
    NVRAM --> Key
    Key --> SignEngine
    SignEngine -->|"Digital Signature (Base64)"| CLI
    Payload -.->|"JSON Data"| Verifier
    SignEngine -.->|"Signature"| Verifier
    PubKey -.->|"Public Key"| Verifier
    Verifier -->|"Status (True / False)"| CLI
```

### 2. End-to-End Inference and Signing Pipeline

The following sequence traces the request flow from user input through deterministic inference, canonical payload creation, hardware TPM signing, and immediate verification.

```mermaid
sequenceDiagram
    autonumber
    actor User as User / Client
    participant App as Application (main.py)
    participant Engine as llama.cpp CPU Engine
    participant TPM as TPM 2.0 (tpm2-pytss)
    participant Verifier as Verifier (verify_signature.py)

    User->>App: Submit Prompt
    App->>Engine: Run Inference (temperature=0.0, seed=1337, threads=1)
    Engine-->>App: Deterministic Response Text
    App->>App: Format Canonical JSON Payload (response + ISO UTC timestamp)
    App->>App: Compute SHA-256 Hash of Payload
    App->>TPM: sign_hash(nvram_address, tcti, digest)
    Note over TPM: Sign digest with non-exportable RSA-2048 key in hardware
    TPM-->>App: Base64-encoded RSASSA Signature
    App->>Verifier: verify_signature(digest, signature, public_key)
    Verifier-->>App: Verification Status (True / False)
    App-->>User: Output Response, Payload JSON, SHA-256, Signature, and Status
```

### 3. Cryptographic Verification Workflow

Independent parties can verify response integrity and hardware provenance without needing access to the TPM private key.

```mermaid
flowchart TD
    subgraph Inputs["Verification Inputs"]
        JSON["Canonical JSON Payload\n{response, timestamp}"]
        SIG["TPM Digital Signature\n(Base64 Encoded)"]
        PUB["TPM Public Key\n(PEM / Base64 Encoded)"]
    end

    subgraph Processing["Verification Operations"]
        H["1. Recompute SHA-256 Digest\nfrom Raw Payload UTF-8"]
        D["2. Base64 Decode Signature Bytes"]
        K["3. Load Public Key (RSAPublicKey)"]
        V{"4. Verify Signature\n(PKCS#1 v1.5 with Prehashed SHA-256)"}
    end

    subgraph Outcome["Verification Result"]
        Valid["TRUE\nIntegrity Confirmed and Origin Verified"]
        Invalid["FALSE\nData Altered or Invalid Signature"]
    end

    JSON --> H
    SIG --> D
    PUB --> K
    H -->|"Digest"| V
    D -->|"Signature Bytes"| V
    K -->|"Public Key"| V
    V -->|"Valid Match"| Valid
    V -->|"Mismatch / Error"| Invalid
```

### 4. TPM Key Lifecycle Management

Key generation, persistence into TPM NVRAM, public key export, and slot teardown follow the workflow below.

```mermaid
flowchart LR
    subgraph Provisioning["Key Provisioning (tpm.create)"]
        direction TB
        A1["Connect via TCTI\n(/dev/tpmrm0 or swtpm)"] --> A2["Create Primary Key\n(Owner Hierarchy)"]
        A2 --> A3["Generate RSA-2048 Key"]
        A3 --> A4["Evict Control to NVRAM\n(Persist at Handle 0x81010002)"]
        A4 --> A5["Flush Transient Contexts"]
    end

    subgraph Storage["TPM NVRAM"]
        Slot["Persistent Handle\n(0x81010002)"]
    end

    subgraph Operations["Runtime Operations"]
        direction TB
        B1["Read Public Key\n(tpm.read_public)"]
        B2["Sign Digest\n(tpm.sign_hash)"]
    end

    subgraph Deletion["Teardown (tpm.delete)"]
        C1["Evict Control\n(Release NVRAM Handle)"]
    end

    A4 --> Slot
    Slot --> B1
    Slot --> B2
    Slot --> C1
```

---

### Step 1: Install Package Manager & Tools (Nix)

If you are using Nix as your package manager to fetch system dependencies like `tpm2-tools`, `openssl`, and `git`:

```bash
# Install Nix (Single-user installation)
sh <(curl -L https://nixos.org/nix/install) --no-daemon

# Load Nix environment (if prompted)
. ~/.nix-profile/etc/profile.d/nix.sh

# Install required system tools via Nix or your system package manager (apt/pacman)
nix-env -iA nixpkgs.tpm2-tools nixpkgs.openssl nixpkgs.xxd nixpkgs.python3
```

---

### Step 2: Set Up User Permissions to TPM (`tss`)

To allow your user account to communicate with the hardware TPM device (`/dev/tpmrm0`) without always needing `sudo`, add your user to the system's TPM group (`tss` or `tpms`):

```bash
# Add current user to the tss group
sudo usermod -aG tss $USER

# Apply group changes immediately in your current shell session
newgrp tss

# Verify you have read/write access to the TPM resource manager
ls -la /dev/tpmrm0
```

> [!NOTE]
> If physical TPM hardware is not available, you can use the software TPM emulator (`swtpm`). Refer to the setup guide in [docs/swtpm.md](docs/swtpm.md).

---

### Step 3: Select and Verify TPM Persistent Handle

Choose a persistent memory slot/address (e.g., `0x81010002`) to store your cryptographic signing key inside the TPM.

* **Provision an RSA signing key into TPM NVRAM:**
```bash
uv run python -m tpm.create
```

* **Check existing persistent handles:**
```bash
tpm2_getcap handles-persistent -T device:/dev/tpmrm0
```

* **Read the public key at your selected address (DER format encoded in Base64):**
```bash
tpm2_readpublic -c 0x81010002 -f der -T device:/dev/tpmrm0 | base64 -w 0
```

* **Alternatively, read the PEM public key using the project script:**
```bash
uv run python -m tpm.read_public
```

* **To clear or evict the handle from NVRAM:**
```bash
uv run python -m tpm.delete
```

---

### Step 4: Run the Determinism Test

Verify that your local CPU inference engine (`llama-cpp-python` with single-thread CPU constraints and seed locking) produces 100% identical outputs and SHA-256 hashes across sequential runs.

**Command:**

```bash
uv run python -m cvdllm.determinism_test
```

**Result:**

```text
Loading model (qwen2.5-0.5b-instruct-q4_k_m.gguf) from repo (Qwen/Qwen2.5-0.5B-Instruct-GGUF)...

Prompt: 'In one concise sentence, what is a CPU register?'
Executing 5 sequential inference runs...
======================================================================
Run 01 | SHA-256: 9eb58e47c4b0a4accc0068fb88c3d4ef1eafa028fcd869baff18ee8c01ee70c1
       Output:  "A CPU register is a memory location that holds data temporarily while a program is executing."

Run 02 | SHA-256: 9eb58e47c4b0a4accc0068fb88c3d4ef1eafa028fcd869baff18ee8c01ee70c1
       Output:  "A CPU register is a memory location that holds data temporarily while a program is executing."

Run 03 | SHA-256: 9eb58e47c4b0a4accc0068fb88c3d4ef1eafa028fcd869baff18ee8c01ee70c1
       Output:  "A CPU register is a memory location that holds data temporarily while a program is executing."

Run 04 | SHA-256: 9eb58e47c4b0a4accc0068fb88c3d4ef1eafa028fcd869baff18ee8c01ee70c1
       Output:  "A CPU register is a memory location that holds data temporarily while a program is executing."

Run 05 | SHA-256: 9eb58e47c4b0a4accc0068fb88c3d4ef1eafa028fcd869baff18ee8c01ee70c1
       Output:  "A CPU register is a memory location that holds data temporarily while a program is executing."

======================================================================
VERIFICATION SUCCESS: All 5 runs produced 100% identical outputs!
```

---

### Step 5: Run Cryptographic Verification Chat (`cvdllm`)

Launch the interactive tool to chat with the model, generate hardware-backed cryptographic signatures via the TPM, and verify them.

**Command:**

```bash
uv run cvdllm
```

**Result:**

```text
TPM Public Key:
LS0tLS1CRUdJTiBQVUJMSUMgS0VZLS0tLS0KTUlJQklqQU5CZ2txaGtpRzl3MEJBUUVGQUFPQ0FROEFNSUlCQ2dLQ0FRRUE0cXpEd2dGZkNlQ0FQaTcvYS9KRwo5SDBvMUhlUFhqUXdVSEhpUThlRXdtVEEwe
CtWSTFuV2JHMkl3c1NEcTBtU2FraDBvOFA0TUpDOHpRSExDWFpDCjRubzQ3YmFtcVhwNmpzV21iQnJDQ2F6TFZLdHd1eUtyQVh1bWxkQVRKMW4zL2RCMDhqZFh2VTJEYWhhZWVvTXQKUjRKbW9sZ0czazZvbl
RrQUROSHpHWXV6dEdaZXNKRGthUlY5clhQcEpJVE9GZjAxV0tvMGxSeHhyS0RvJjdlNgo5MnFpVGRlWEM0b0xKSnpiNWVpU0IzSEhNYWJoeS82a21JakZES2NGYkdCTGI5dHdLZlo5QloyRHVZcWtNNWRPCjF
WbzhmdXhWaFdGcjR2QjE0REVJY1d2VlRrMG9WallLemYrd1R6MG1NdnYxQVErQWtQd042L1JMUTJxL1FHYTYKbFFJREFRQUIKLS0tLS1FTkQgUFVCTElDIEtFWS0tLS0tCg==

╭───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│                                                    Deterministic Chat • Type 'quit' or 'exit' to stop                                                     │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

╭─────────────────────────────── You ────────────────────────────────╮
│ explain the importance of cryptographic verification in llms in    │
│ one sentence                                                       │
╰────────────────────────────────────────────────────────────────────╯

╭──────────────────────────── Assistant ─────────────────────────────╮
│ Cryptography verification is crucial for ensuring the security and │
│ integrity of machine learning (ML) systems, preventing             │
│ unauthorized access and data breaches.                             │
╰────────────────────────────────────────────────────────────────────╯
─── Verification Payload ───
Raw JSON for external hashing:
{
  "response": "Cryptography verification is crucial for ensuring the security and integrity of machine learning (ML) systems, preventing unauthorized access and data breaches.",
  "timestamp": "2026-10-18T14:59:49.200461+00:00"
}

SHA-256:
f4c13e15dfa14aa54effb69d84e104006dafb18ca1f6be5e34c9494fcbf40002

TPM Signature:
0oPtN+ExdsF2q4JeMbfN5yCk0Y/fE2NwQuw1cOmBkTjNIQZoaRRk/AIe+kiPr0OcNK4DKjop7TiA2GXqJ8RUCIWi5S2q2q0aebgDaZDN3WAGf5P1N2UhfE5WS2BFaJSeGa6vCg7rLE8EnN8ZNhzfl2h+x9xNA
MkXNrg9qsPeCuw0QdNQXQG2NOJX5tmt7TW8ZKXd8plP0JrFOf+i5hNNqp1Y8jnHd4aXRxKF6Ki5Wk5PMDWpJjzyBQpLHoNlfdZzVUc7cXHxGTuXh5xUA4cmE+Tw3gsOc8w6YJcIiwG9lcsj8qRmwuoiXJSUSP
Vom9N1Ic+X5VAIwylXGXkKYYp8bQ==

Verification Status:
TRUE
```

---

### Built-in Verification (Python)

Inside `cvdllm`, verification is handled automatically by calling the verify module. You can also run the verification script directly from the command line:

```bash
uv run python -m tpm.verify_signature <SHA256_HASH> <BASE64_SIGNATURE>
```

Example:

```bash
uv run python -m tpm.verify_signature 2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824 <BASE64_SIGNATURE>
```

---

### Project Structure

```text
cvdllm/
├── docs/
│   └── swtpm.md              # Software TPM configuration guide
├── src/
│   ├── cvdllm/
│   │   ├── __init__.py
│   │   ├── determinism_test.py # Determinism validation across runs
│   │   └── main.py             # Interactive deterministic chat with TPM signing
│   └── tpm/
│       ├── __init__.py
│       ├── create.py           # Provision persistent RSA key in TPM NVRAM
│       ├── delete.py           # Evict handle from TPM NVRAM
│       ├── read_public.py      # Read TPM public key in PEM format
│       ├── sign_hash.py        # Sign SHA-256 hash digest via TPM RSASSA
│       └── verify_signature.py # Cryptographic signature verification
├── .env                        # TPM handle, device path, and model configuration
├── flake.nix                   # Nix devshell configuration
└── pyproject.toml              # Build specifications and dependencies
```

---

```bibtex
@software{cvdllm_2026,
  authors      = {Sudhanshu Atalkar, Zain Syed, Vedant Ghate, Parth Bhuskade and Dr. S. R. Gupta},
  college      = {Prof. Ram Meghe Institute of Technology and Research.},
  title        = {cvdllm: Cryptographically Verifiable Deterministic LLM},
  month        = oct,
  year         = {2026},
  publisher    = {Zenodo},
  version      = {v0.0.3},
  doi          = {10.5281/zenodo.23455300},
  url          = {[https://doi.org/10.5281/zenodo.23455300](https://doi.org/10.5281/zenodo.23455300)},
}
```

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23455300.svg)](https://doi.org/10.5281/zenodo.23455300)
