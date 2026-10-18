





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


