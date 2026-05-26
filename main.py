import os
import smtplib
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage

from dotenv import load_dotenv
from google import genai
from google.genai import types


JST = timezone(timedelta(hours=9))
DEFAULT_MODEL = "gemini-2.5-flash"
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


def generate_news() -> str:
    api_key = require_env("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL", DEFAULT_MODEL)

    client = genai.Client(api_key=api_key)
    grounding_tool = types.Tool(google_search=types.GoogleSearch())
    response = client.models.generate_content(
        model=model,
        contents=build_prompt(),
        config=types.GenerateContentConfig(
            tools=[grounding_tool],
            temperature=0.2,
        ),
    )

    text = getattr(response, "text", None)
    if not text:
        raise RuntimeError("Gemini returned an empty response.")
    return text.strip()


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
