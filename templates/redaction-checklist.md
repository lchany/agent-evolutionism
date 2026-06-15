# Redaction Checklist

Before committing Experience Vault records, verify:

- [ ] No password values are present.
- [ ] No API keys are present.
- [ ] No private keys are present.
- [ ] No bearer tokens are present.
- [ ] No raw auth files are present.
- [ ] No dense sensitive logs are copied verbatim.
- [ ] Hosts, users, and paths are generalized when needed.
- [ ] Sensitive values use placeholders such as `<PASSWORD>`, `<API_KEY>`, `<TOKEN>`, `<PRIVATE_KEY>`, or `<REMOTE_HOST>`.

