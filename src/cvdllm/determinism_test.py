import os
import hashlib
from dotenv import load_dotenv
from huggingface_hub import hf_hub_download
from huggingface_hub.utils import LocalEntryNotFoundError
from llama_cpp import Llama

# Load environment variables from .env first
load_dotenv()

# Retrieve all configuration and input parameters from the environment
REPO_ID = os.getenv("REPO_ID")
FILENAME = os.getenv("MODELNAME")
CONTEXT_LENGTH = int(os.getenv("context_length", "8192"))
QUESTION = os.getenv("QUESTION", "In one concise sentence, what is a CPU register?")
RUNS = int(os.getenv("RUNS", "5"))


def get_model_path() -> str:
    """Attempts local cache retrieval first to avoid HF API calls."""
    try:
        return hf_hub_download(
            repo_id=REPO_ID,
            filename=FILENAME,
            local_files_only=True,
        )
    except (LocalEntryNotFoundError, Exception):
        return hf_hub_download(
            repo_id=REPO_ID,
            filename=FILENAME,
        )


def main() -> None:
    if not REPO_ID or not FILENAME:
        print("Error: REPO_ID or MODELNAME not found in environment variables or .env file.")
        return

    print(f"Loading model ({FILENAME}) from repo ({REPO_ID})...")
    model_path = get_model_path()

    # Initialize single-threaded engine for deterministic execution
    llm = Llama(
        model_path=model_path,
        n_threads=1,            # 1 core eliminates thread-ordering noise
        use_mlock=True,         # Lock weights in RAM
        n_ctx=CONTEXT_LENGTH,   # Loaded dynamically from environment
        verbose=False,
    )

    messages = [
        {"role": "system", "content": "You are a concise technical expert."},
        {"role": "user", "content": QUESTION},
    ]

    print(f"\nPrompt: '{QUESTION}'")
    print(f"Executing {RUNS} sequential inference runs...\n" + "=" * 70)

    hashes = []

    for i in range(1, RUNS + 1):
        # Enforce greedy decoding (temperature=0.0) and fixed seed
        response = llm.create_chat_completion(
            messages=messages,
            max_tokens=40,    # Cap output token count
            temperature=0.0,  # Argmax selection
            seed=1337,        # Fixed PRNG state
        )

        content = response["choices"][0]["message"]["content"].strip()
        sha256_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        hashes.append(sha256_hash)

        print(f"Run {i:02d} | SHA-256: {sha256_hash}")
        print(f"       Output:  \"{content}\"\n")

    print("=" * 70)
    # Verification assertion
    if len(set(hashes)) == 1:
        print(f"VERIFICATION SUCCESS: All {RUNS} runs produced 100% identical outputs!")
    else:
        print(f"VERIFICATION FAILURE: Output drift detected across {len(set(hashes))} unique hashes.")


if __name__ == "__main__":
    main()