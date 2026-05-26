# AI News Automation

Gemini API with Google Search grounding is used to summarize the last 24 hours of updates and reputation signals for ChatGPT, Gemini, and Claude in Japanese, then send the summary by email.

## Files

- `main.py`: Generates the news summary and sends email.
- `requirements.txt`: Python dependencies.
- `.env.example`: Local environment variable template.
- `.github/workflows/daily_news.yml`: Runs every day at 07:00 JST.

## GitHub Actions setup

Add these repository secrets in `Settings -> Secrets and variables -> Actions`:

```text
GEMINI_API_KEY
SMTP_HOST
SMTP_USER
SMTP_PASSWORD
MAIL_FROM
MAIL_TO
```

Optional secrets:

```text
SMTP_PORT
SMTP_USE_TLS
SMTP_USE_SSL
```

Defaults are:

```text
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USE_SSL=false
```

Optional repository variables:

```text
GEMINI_MODEL=gemini-2.5-flash
MAIL_SUBJECT=AIニュース日次まとめ
```

## Troubleshooting

If a workflow run fails with `Missing required environment variable: GEMINI_API_KEY` or `Missing GitHub Secret`, the required repository secrets are not registered or their names do not exactly match.

Open this repository page and add the missing values:

```text
Settings -> Secrets and variables -> Actions -> Repository secrets
```

Secret names are case-sensitive. For example, `GEMINI_API_KEY` is valid, but `Gemini_API_KEY` is not.

## Local run

```bash
cp .env.example .env
pip install -r requirements.txt
python main.py
```

The workflow can also be started manually from the Actions tab with `workflow_dispatch`.
