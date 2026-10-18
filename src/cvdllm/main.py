import sys
import os
import hashlib
import json
from datetime import datetime, timezone
from dotenv import load_dotenv
load_dotenv()
from huggingface_hub import hf_hub_download
from huggingface_hub.utils import LocalEntryNotFoundError
from llama_cpp import Llama

from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.text import Text

from tpm.sign_hash import sign_hash
from tpm.verify_signature import verify_signature
from tpm.read_public import read_tpm_public

REPO_ID = os.getenv("REPO_ID")
FILENAME = os.getenv("MODELNAME")
context_length = int(os.getenv("context_length"))
console = Console()

def get_model_path() -> str:
    repo_id = os.getenv("REPO_ID")
    filename = os.getenv("MODELNAME")
    
    try:
        return hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            local_files_only=True,
        )
    except (LocalEntryNotFoundError, Exception):
        return hf_hub_download(
            repo_id=repo_id,
            filename=filename,
        )

def make_bubble(text: str, title: str, style: str) -> Panel:
    return Panel(
        text,
        title=title,
        border_style=style,
        padding=(0, 1),
        width=min(70, console.width - 4),
    )

def main() -> None:
    # Load TPM environment variables from .env
    load_dotenv()
    nvram_address = os.getenv("TPM_NVRAM_ADDRESS")
    tcti = os.getenv("TPM2TOOLS_TCTI")
    # pub_key = os.getenv("TPM_PUBLIC_KEY")
    pub_key = read_tpm_public(nvram_address, tcti)
    
    console.clear()
    
    # --- PRINT PUBLIC KEY RAW (NO PANEL) FOR EASY COPYING ---
    if pub_key:
        console.print("[bold cyan]TPM Public Key:[/]")
        console.print(pub_key)
    else:
        console.print("[bold red]Warning: TPM_PUBLIC_KEY not found in .env[/]")
    console.print()
    
    with console.status("[bold cyan]Loading model locally...", spinner="dots"):
        model_path = get_model_path()

    with console.status("[bold yellow]Initializing Single-Thread CPU Engine...", spinner="bouncingBar"):
        llm = Llama(
            model_path=model_path,
            n_threads=1,
            use_mlock=True,
            n_ctx=context_length,
            flash_attn=True,  # Enables Flash Attention for single-core optimization
            verbose=False,
        )

    console.print(Panel(
        Text("Deterministic Chat • Type 'quit' or 'exit' to stop", justify="center"),
        style="bold blue"
    ))
    console.print()

    messages = [
        {"role": "system", "content": "You are a helpful, concise AI assistant."}
    ]

    while True:
        try:
            user_input = console.input("[bold green]❯ [/]").strip()
            
            if user_input.lower() in ["quit", "exit"]:
                console.print("[bold red]Exiting...[/]")
                break
            if not user_input:
                continue

            # Erase the input line
            console.file.write("\033[1A\033[2K")
            console.file.flush()

            # User message - LEFT
            console.print(make_bubble(user_input, "You", "green"))
            console.print()

            messages.append({"role": "user", "content": user_input})

            stream = llm.create_chat_completion(
                messages=messages,
                max_tokens=256,
                temperature=0.0,
                seed=1337,
                stream=True,
            )

            response_text = ""
            
            with Live(
                make_bubble("", "Assistant", "cyan"),
                refresh_per_second=15,
                console=console
            ) as live:
                for chunk in stream:
                    delta = chunk["choices"][0].get("delta", {})
                    if "content" in delta:
                        response_text += delta["content"]
                        live.update(make_bubble(response_text, "Assistant", "cyan"))

            # --- VERIFICATION PAYLOAD GENERATION ---

            timestamp = datetime.now(timezone.utc).isoformat()
            payload = {
                "response": response_text,
                "timestamp": timestamp
            }

            payload_json_str = json.dumps(payload, indent=2)
            text_hash = hashlib.sha256(payload_json_str.encode("utf-8")).hexdigest()

            # Generate TPM signature
            signature = sign_hash(nvram_address, tcti, text_hash)
            
            # Verify signature
            verification_status = verify_signature(text_hash, signature, pub_key)

            # Display
            console.print("[dim]─── Verification Payload ───[/]")
            console.print("[dim]Raw JSON for external hashing:[/]")
            console.print(f"[yellow]{payload_json_str}[/]")
            
            console.print(f"\n[dim]SHA-256:[/]\n[cyan]{text_hash}[/]")
            console.print(f"\n[dim]TPM Signature:[/]\n[magenta]{signature}[/]")
            
            status_color = "bold green" if verification_status == "true" else "bold red"
            console.print(f"\n[dim]Verification Status:[/]\n[{status_color}]{verification_status.upper()}[/]\n")

            messages.append({"role": "assistant", "content": response_text})

        except (KeyboardInterrupt, EOFError):
            console.print("\n[bold red]Generation interrupted or input stream closed. Exiting...[/]")
            break

if __name__ == "__main__":
    main()