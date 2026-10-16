Use **swtpm** (software TPM emulator). Your Python scripts stay the same — only the TCTI changes.

### 1. Install swtpm

**Fedora / RHEL**
```bash
sudo dnf install swtpm swtpm-tools
```

**Ubuntu / Debian**
```bash
sudo apt install swtpm swtpm-tools
```

**Nix**
```bash
nix-shell -p swtpm
```

### 2. Start the software TPM

```bash
mkdir -p /tmp/myvtpm
swtpm socket \
  --tpmstate dir=/tmp/myvtpm \
  --tpm2 \
  --ctrl type=tcp,port=2322 \
  --server type=tcp,port=2321 \
  --flags not-need-init
```

Leave that running in one terminal.

### 3. Point your `.env` at it

```env
# tpm config
TPM_NVRAM_ADDRESS=0x81010002
TPM2TOOLS_TCTI=swtpm:host=127.0.0.1,port=2321
```

(or just `swtpm:port=2321`)

### 4. Startup the TPM once

```bash
export TPM2TOOLS_TCTI=swtpm:port=2321
tpm2_startup -c
```

### 5. Use your scripts as usual

```bash
python run/create_tpm.py
python run/read_tpm.py
python run/sign.py 2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824
# etc.
```

### Reset the software TPM

```bash
swtpm_ioctl -i --tcp :2322
```

That’s it. No hardware TPM required.