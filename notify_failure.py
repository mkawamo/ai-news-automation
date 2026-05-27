import os
import smtplib
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage

from dotenv import load_dotenv


JST = timezone(timedelta(hours=9))


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def build_email() -> EmailMessage:
    mail_from = require_env("MAIL_FROM")
    mail_to = require_env("MAIL_TO")
    now = datetime.now(JST)

    message = EmailMessage()
    message["From"] = mail_from
    message["To"] = mail_to
    message["Subject"] = os.getenv(
        "FAILURE_MAIL_SUBJECT",
        f"AIニュース送信失敗（{now:%Y-%m-%d}）",
    )
    message.set_content("メール送信に失敗しました。手動実行してください")
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
    send_email(build_email())
    print("Failure notification email sent.")


if __name__ == "__main__":
    main()
