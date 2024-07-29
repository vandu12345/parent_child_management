import os
import smtplib
from datetime import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from celery import Celery

import CONSTANTS

celery_worker = Celery(
    "worker",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
)

celery_worker.conf.update(task_routes={"task.*": {"queue": "email"}})


@celery_worker.task(name="task_activation_email")
def send_activation_email(email: str, token: str):
    """
    Send Activation mail
    """
    msg = MIMEMultipart()
    msg["From"] = CONSTANTS.FROM_ADMIN_EMAIL
    msg["To"] = email
    msg["Subject"] = "Activate your account"

    # If it's a local development then we can use localhost, if it's cloud then
    # we need to provide the url or ip wherever it's hosted
    link = f"{CONSTANTS.HOST_SERVER}/activate?token={token}"
    # TODO: For more beautification need to use jinja
    body = f"""\
            <html>
            <body style="font-family: Arial, sans-serif; color: #333; background-color: #f9f9f9; padding: 20px;">
                <div style="max-width: 600px; margin: auto; background-color: #fff; padding: 20px; border-radius: 10px; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);">
                <h2 style="color: #0044cc;">Activate Your Account</h2>
                <p>Hi,</p>
                <p>Thank you for registering. Please click the button below to activate your account:</p>
                <p style="text-align: center;">
                    <a href="{link}" style="display: inline-block; padding: 10px 20px; font-size: 16px; color: #fff; background-color: #28a745; border-radius: 5px; text-decoration: none;">Activate Account</a>
                </p>
                <p>If the button above doesn't work, please copy and paste the following link into your web browser:</p>
                <p><a href="{link}">{link}</a></p>
                <p>Thanks,<br>
                <strong>Cloudify Team</strong></p>
                <hr style="border: none; border-top: 1px solid #eee;">
                <p style="font-size: 0.9em; color: #999;">This is an automated message. Please do not reply.</p>
                </div>
            </body>
            </html>
            """

    msg.attach(MIMEText(body, "html"))
    with smtplib.SMTP(
        os.getenv("EMAIL_HOST", "0.0.0.0"), os.getenv("EMAIL_PORT", 25)
    ) as server:
        # server.starttls()
        server.sendmail(CONSTANTS.FROM_ADMIN_EMAIL, email, msg.as_string())


@celery_worker.task(name="task_newchild_email")
def send_email_to_admin(parent_id, children_name):
    """_summary_

    Args:
        parent_id (_type_): _description_
        children (_type_): _description_
    """
    # TODO: Add sleep 300
    time.sleep(10)
    msg = MIMEMultipart()
    msg["To"] = CONSTANTS.RECEIVER_ADMIN_EMAIL
    msg["Subject"] = (
        f"New Children added with name : {children_name} by parent id: {parent_id}"
    )

    # TODO: Implement admin panel
    # TODO: For more beautification need to use jinja
    body = """\
        <html>
        <body style="font-family: Arial, sans-serif; color: #333; background-color: #f9f9f9; padding: 20px;">
            <div style="max-width: 600px; margin: auto; background-color: #fff; padding: 20px; border-radius: 10px; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);">
            <h2 style="color: #0044cc;">New Child Added Notification</h2>
            <p>Hi Admin,</p>
            <p>  We are pleased to inform you that a new child has been added by a parent.</p>
            <p style="color: #555;">  You can view the details in your admin panel.</p>
            <p>Thanks,<br>
            <strong>  Cloudify Team</strong></p>
            <hr style="border: none; border-top: 1px solid #eee;">
            <p style="font-size: 0.9em; color: #999;">This is an automated message. Please do not reply.</p>
            </div>
        </body>
        </html>
        """
    msg.attach(MIMEText(body, "html"))

    with smtplib.SMTP(
        os.getenv("EMAIL_HOST", "localhost"), os.getenv("EMAIL_PORT", 25)
    ) as server:
        # server.starttls()
        server.sendmail(
            CONSTANTS.FROM_ADMIN_EMAIL, CONSTANTS.RECEIVER_ADMIN_EMAIL, msg.as_string()
        )
