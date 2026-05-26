import os
import smtplib
import time
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types


JST = timezone(timedelta(hours=9))
DEFAULT_MODEL = "gemini-2.5-flash"
FALLBACK_MODEL = "gemini-2.0-flash"
MAX_GEMINI_ATTEMPTS = 3
REQUIRED_ENV_VARS = (
    "GEMINI_API_KEY",
    "SMTP_HOST",
    "SMTP_USER",
    "SMTP_PASSWORD",
    "MAIL_FROM",
    "MAIL_TO",
)


def validate_required_env() -> None:
    missing = [name for name in REQUIRED_ENV_VARS if not os.getenv(name)]
    if missing:
        joined = ", ".join(missing)
        raise RuntimeError(
            "Missing required environment variables: "
            f"{joined}. Add them as GitHub Actions repository secrets."
        )


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def build_prompt() -> str:
    now = datetime.now(JST)
    since = now - timedelta(hours=24)
    return f"""
あなたはAI業界ニュースの調査担当です。Google Search groundingを使い、最新Web情報を確認してください。

調査対象:
- ChatGPT
- Gemini
- Claude

調査期間:
- {since:%Y-%m-%d %H:%M} JST から {now:%Y-%m-%d %H:%M} JST までの過去24時間以内

調査条件:
- 公式発表、公式ブログ、リリースノート、開発者ドキュメント、公式SNSを優先する
- SNS、Hacker News、Reddit、開発者コミュニティ、主要AIメディアでの評判や反応も確認する
- 過去24時間以内と確認できない情報は含めない
- 大きな更新や十分な評判情報がない場合は、その旨を明記する
- 推測で断定しない

出力形式:
件名候補: AIニュース日次まとめ（YYYY-MM-DD）

ChatGPT
1. アップデート:
2. 評判:
3. 出典:

Gemini
1. アップデート:
2. 評判:
3. 出典:

Claude
1. アップデート:
2. 評判:
3. 出典:

各サービスは必ず日本語3行にしてください。出典行にはURLを1〜3件入れてください。
"""


def parse_model_list() -> list[str]:
    configured = os.getenv("GEMINI_MODEL", DEFAULT_MODEL)
    models = [model.strip() for model in configured.split(",") if model.strip()]
    if FALLBACK_MODEL not in models:
        models.append(FALLBACK_MODEL)
    return models


def generate_with_model(client: genai.Client, model: str, prompt: str) -> str:
    grounding_tool = types.Tool(google_search=types.GoogleSearch())
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[grounding_tool],
            temperature=0.2,
        ),
    )

    text = getattr(response, "text", None)
    if not text:
        raise RuntimeError(f"Gemini returned an empty response with model: {model}")
    return text.strip()


def is_retryable_gemini_error(exc: Exception) -> bool:
    status_code = getattr(exc, "status_code", None)
    if status_code in {429, 500, 502, 503, 504}:
        return True

    message = str(exc).lower()
    return any(token in message for token in ("unavailable", "overloaded", "rate limit"))


def generate_news() -> str:
    api_key = require_env("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    prompt = build_prompt()
    last_error: Exception | None = None

    for model in parse_model_list():
        for attempt in range(1, MAX_GEMINI_ATTEMPTS + 1):
            try:
                print(f"Generating news with {model} (attempt {attempt}/{MAX_GEMINI_ATTEMPTS})...")
                return generate_with_model(client, model, prompt)
            except errors.APIError as exc:
                last_error = exc
                if not is_retryable_gemini_error(exc) or attempt == MAX_GEMINI_ATTEMPTS:
                    print(f"Gemini model {model} failed: {exc}")
                    break

                delay_seconds = 20 * attempt
                print(
                    f"Gemini model {model} is temporarily unavailable; "
                    f"retrying in {delay_seconds} seconds."
                )
                time.sleep(delay_seconds)

    raise RuntimeError("Gemini news generation failed after retries and fallback model.") from last_error


def build_email(body: str) -> EmailMessage:
    mail_from = require_env("MAIL_FROM")
    mail_to = require_env("MAIL_TO")
    subject = os.getenv(
        "MAIL_SUBJECT",
        f"AIニュース日次まとめ（{datetime.now(JST):%Y-%m-%d}）",
    )

    message = EmailMessage()
    message["From"] = mail_from
    message["To"] = mail_to
    message["Subject"] = subject
    message.set_content(body)
    return message


def send_email(message: EmailMessage) -> None:
    host = require_env("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = require_env("SMTP_USER")
    password = require_env("SMTP_PASSWORD")
    use_ssl = os.getenv("SMTP_USE_SSL", "false").lower() in {"1", "true", "yes"}
    use_tls = os.getenv("SMTP_USE_TLS", "true").lower() in {"1", "true", "yes"}

    if use_ssl:
        with smtplib.SMTP_SSL(host, port) as smtp:
            smtp.login(user, password)
            smtp.send_message(message)
        return

    with smtplib.SMTP(host, port) as smtp:
        if use_tls:
            smtp.starttls()
        smtp.login(user, password)
        smtp.send_message(message)


def main() -> None:
    load_dotenv()
    validate_required_env()
    body = generate_news()
    message = build_email(body)
    send_email(message)
    print("Daily AI news email sent.")


if __name__ == "__main__":
    main()
