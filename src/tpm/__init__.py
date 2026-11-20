# src/tpm/__init__.py
def __getattr__(name: str):
    if name == "verify_signature":
        from .verify_signature import verify_signature
        return verify_signature
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")