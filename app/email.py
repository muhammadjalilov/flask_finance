import os
import smtplib
import ssl
import time
from random import randint

from celery import Celery

from app.models import User

celery = Celery(__name__)
celery.conf.broker_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379")
celery.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379")


def send_email(reciever_email, text):
    from dotenv import load_dotenv
    load_dotenv()
    port = 465  # For SSL

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
        email = os.getenv("USER_EMAIL")
        password = os.getenv("USER_PASSWORD")
        server.login(email, password)
        server.sendmail(email, [reciever_email, ], text)


@celery.task(name="forgot_password")
def send_notification_code(code, email):
    text = f"""
        Your confirmation code {code} for change password.
        If you do not want to change, just ignore it!
    """
    send_email(reciever_email=email, text=text)
    return True
