FROM gr0wvolution/webfluid:beta

# Ocean dependencies
COPY constraints.txt /tmp/site-constraints.txt
RUN pip install --no-cache-dir --upgrade -r /tmp/site-constraints.txt \
    pydantic[email] pyotp segno webauthn \
    async-lru stripe reportlab
