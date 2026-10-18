# Determinism Test
```bash
[sudha@0xnryn-laptop0:~/fyproject]$ uv run python -m cvdllm.determinism_test
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

[sudha@0xnryn-laptop0:~/fyproject]$ 
```

# Cryptographic Verification
### Input:
```bash
uv run cvdllm
```
### Output:
```bash
TPM Public Key:
LS0tLS1CRUdJTiBQVUJMSUMgS0VZLS0tLS0KTUlJQklqQU5CZ2txaGtpRzl3MEJBUUVGQUFPQ0FROEFNSUlCQ2dLQ0FRRUE0cXpEd2dGZkNlQ0FQaTcvYS9KRwo5SDBvMUhlUFhqUXdVSEhpUThlRXdtVEEwe
CtWSTFuV2JHMkl3c1NEcTBtU2FraDBvOFA0TUpDOHpRSExDWFpDCjRubzQ3YmFtcVhwNmpzV21iQnJDQ2F6TFZLdHd1eUtyQVh1bWxkQVRKMW4zL2RCMDhqZFh2VTJEYWhhZWVvTXQKUjRKbW9sZ0czazZvbl
RrQUROSHpHWXV6dEdaZXNKRGthUlY5clhQcEpJVE9GZjAxV0tvMGxSeHhyS0RvSjdlNgo5MnFpVGRlWEM0b0xKSnpiNWVpU0IzSEhNYWJoeS82a21JakZES2NGYkdCTGI5dHdLZlo5QloyRHVZcWtNNWRPCjF
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
  "response": "Cryptography verification is crucial for ensuring the security and integrity of machine learning (ML) systems, preventing unauthorized access 
and data breaches.",
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

❯ 
```





# read the key
tpm2_readpublic -c 0x81010002 -f der -T device:/dev/tpmrm0 | base64 -w 0

# delete the key
tpm2_evictcontrol -C o -c 0x81010002 -T device:/dev/tpmrm0

# sign a hash using the tpm
echo -n "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824" | xxd -r -p | tpm2_sign -c 0x81010002 -g sha256 -o /dev/stdout -T device:/dev/tpmrm0 2>/dev/null | base64 -w 0

# read the current persistant addresses
tpm2_getcap handles-persistent

tpm2_getcap handles-persistent -T device:/dev/tpmrm0

hash a pay load
```bash
cat | sha256sum | awk '{print "\n\n ➔ " $1}'
```

verify the signature
```bash
uv run uv run python -m tpm.verify  2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824 XCvCG3hLdkRDku5Z1dtpzlQ7MdGLRcDH4obvgGxFUlifFmWMRTmQE71+wIbml+2n987yuj3moLgd8MD9btSjeTreCtcchpvuNj97IrLgwugmuMd5PYU0iA0h4NuG1DvzHW4pKdTaXLDhRZGqbOOOHgBNiFAtw0F7GoP1wivErmwnD4dlpE82OOHV1PXB/zNbrLcwwVxkwF/PnRvQ7dtg88mL69YWFmPjukym+8e3wlINQQyXGjAPn3dzXH5ysiHGg1bG4aHBWnvFPxscq73aYdKCiVFbYZ2U7dIHdt2LryaJaZQjwC1oHJuXaycVkc4VTrb1VDAlTliCJvpqul7jYA==
```


