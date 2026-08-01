FROM gr0wvolution/webfluid:beta

# Ocean dependencies
RUN pip install --no-cache-dir \
    pydantic[email] pyotp segno webauthn \
    stripe cryptography async-lru