# Security

## Reporting issues

Do not open a public issue for suspected vulnerabilities. Describe the problem privately and include reproduction steps that do not require live credentials.

## What this project does not do

Opportunity Engine collects **public** opportunity data. It does not:

- bypass CAPTCHAs, authentication, paywalls or bot protection
- rotate proxies to defeat website restrictions
- store or log passwords, API keys, tokens or `Authorization` headers
- require SMTP or webhook credentials for local operation

## Secrets

- Copy `.env.example` to `.env`. Never commit `.env`.
- Database URLs, SMTP passwords and webhook URLs are loaded via `pydantic-settings`.
- Structured logs redact keys listed in `SENSITIVE_LOG_KEYS`.
- Optional email/webhook providers stay disabled until explicitly configured.

## Production considerations

- Run behind TLS. Do not expose PostgreSQL to the public internet.
- Replace `SECRET_KEY`.
- Prefer a dedicated database role with least privilege.
- Set `APP_DEBUG=false` and `LOG_LEVEL=INFO` or `WARNING`.
- Restrict outbound HTTP to an allow-list of source hosts.
- Keep `RESPECT_ROBOTS_TXT=true` unless you have written permission to ignore it.
- Treat generated reports as potentially sensitive commercial data.
- Use migrations (`alembic upgrade head`) rather than `create_all` in production.

## Dependency and supply chain

Pin versions with `uv.lock`. GitHub Actions runs lint, typecheck and tests on every push.
