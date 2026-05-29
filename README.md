# AI News Automation

Gemini API with Google Search grounding is used to summarize the last 24 hours of updates and reputation signals for ChatGPT, Gemini, and Claude in Japanese, then send the summary by email.

## Files

- `main.py`: Generates the news summary and sends email.
- `notify_failure.py`: Sends a fixed failure notification after the final scheduled retry fails.
- `requirements.txt`: Python dependencies.
- `.env.example`: Local environment variable template.
- `.github/workflows/daily_news.yml`: Supports external `workflow_dispatch` and GitHub schedule fallback.

## Schedule

Recommended operation is a two-layer trigger setup:

1. Primary trigger: cron-job.org calls GitHub `workflow_dispatch` at 06:05 JST.
2. Fallback trigger: GitHub schedule runs every 5 minutes from 06:10 to 07:55 JST.

The GitHub fallback cron is:

```text
10-55/5 21 * * *
*/5 22 * * *
```

GitHub scheduled workflows can be delayed or dropped during high-load periods. The external cron trigger gives the workflow a separate way to start. If cron-job.org fails or is delayed, the GitHub schedule fallback keeps retrying.

The workflow stores a daily success marker after a successful send. Later triggers on the same JST date restore that marker and skip sending, preventing duplicate daily emails even if both services fire.

If the final scheduled slot at 07:55 JST also fails and no success marker exists, the workflow sends this failure notification email:

```text
メール送信に失敗しました。手動実行してください
```

If neither cron-job.org nor GitHub schedule starts the workflow, no in-workflow email can be sent because the code never runs. If SMTP itself is unavailable or the SMTP credentials are invalid, the failure notification email can also fail because it uses the same SMTP settings.

Manual runs include a `force_send` option. Leave it `false` for normal testing, or set it to `true` only when you intentionally want to resend even after today's success marker exists.

## External cron setup

Use cron-job.org as the primary trigger. It is a free HTTP cron service and can send custom HTTP POST requests with headers and a JSON body.

Create a fine-grained GitHub personal access token with access only to this repository and `Actions: Read and write` permission. Store it only in cron-job.org.

Configure the cron job as an HTTP POST:

```text
URL: https://api.github.com/repos/mkawamo/ai-news-automation/actions/workflows/daily_news.yml/dispatches
Method: POST
Schedule: daily at 06:05 JST
```

Headers:

```text
Accept: application/vnd.github+json
Authorization: Bearer YOUR_FINE_GRAINED_GITHUB_TOKEN
X-GitHub-Api-Version: 2022-11-28
Content-Type: application/json
```

Body:

```json
{"ref":"main","inputs":{"force_send":"false"}}
```

Alternative services:

- `Google Cloud Scheduler`: 3 free jobs per billing account, but requires a Google Cloud billing account.
- `UptimeRobot`: Useful for monitoring and alerts, but less ideal than cron-job.org as the primary GitHub workflow trigger.

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
