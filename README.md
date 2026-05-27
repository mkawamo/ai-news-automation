# AI News Automation

Gemini API with Google Search grounding is used to summarize the last 24 hours of updates and reputation signals for ChatGPT, Gemini, and Claude in Japanese, then send the summary by email.

## Files

- `main.py`: Generates the news summary and sends email.
- `requirements.txt`: Python dependencies.
- `.env.example`: Local environment variable template.
- `.github/workflows/daily_news.yml`: Runs every day between 07:10 and 07:55 JST until one send succeeds.

## Schedule

The workflow has four scheduled trigger slots every morning:

```text
07:10 JST
07:25 JST
07:40 JST
07:55 JST
```

In UTC cron, these are:

```text
10 22 * * *
25 22 * * *
40 22 * * *
55 22 * * *
```

GitHub scheduled workflows can be delayed or dropped during high-load periods. Multiple trigger slots reduce the chance that a single dropped schedule prevents the daily email.

The workflow stores a daily success marker after a successful send. Later slots on the same JST date restore that marker and skip sending, preventing duplicate daily emails.

Manual runs include a `force_send` option. Leave it `false` for normal testing, or set it to `true` only when you intentionally want to resend even after today's success marker exists.

## Model

The default model is `gemini-3.5-flash`. If the model is temporarily unavailable, the script retries and then falls back to `gemini-2.5-flash` and `gemini-2.0-flash`.

To override the model list, add a repository variable named `GEMINI_MODEL`. Multiple models can be comma-separated:

```text
GEMINI_MODEL=gemini-3.5-flash,gemini-2.5-flash,gemini-2.0-flash
```

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
GEMINI_MODEL=gemini-3.5-flash
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
