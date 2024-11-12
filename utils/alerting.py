"""Module for alerting in case something noticeable goes wrong
"""
import os
import time
import logging
from google.cloud import firestore
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

logger = logging.getLogger(__name__)

def send_notification(error):
    firestore_client = firestore.Client()
    NOTIFICATION_COOLDOWN = os.environ.get('NOTIFICATION_COOLDOWN', 10800)
    LAST_NOTIFICATION_DOC = os.environ.get(
        'LAST_NOTIFICATION_DOC', 'pull-cue-playout-last-notification'
    )

    current_time = int(time.time())
    last_notification_key = 'last_notification'

    # Reference to the Firestore document
    doc_ref = firestore_client.collection('notifications').document(LAST_NOTIFICATION_DOC)
    doc = doc_ref.get()

    # Check if the cooldown period has passed
    if doc.exists:
        last_sent_time = doc.to_dict().get(last_notification_key, 0)
    else:
        last_sent_time = 0

    if current_time - last_sent_time >= NOTIFICATION_COOLDOWN:
        # Send the email notification
        send_email(error_message)

        # Update the last notification time in Firestore
        doc_ref.set({last_notification_key: current_time})
    else:
        # Cooldown period not yet passed; skip sending email
        logger.info('Cooldown period not yet passed. Skipping email notification.')


def send_email(error_message):
    SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')  # Securely store and access the API key
    EMAIL_FROM = 'your-email@example.com'
    EMAIL_TO = 'your-email@example.com'
    EMAIL_SUBJECT = 'Cloud Function Error Notification'

    message = Mail(
        from_email=EMAIL_FROM,
        to_emails=EMAIL_TO,
        subject=EMAIL_SUBJECT,
        plain_text_content=f'An error occurred in your Cloud Function:\n\n{error_message}'
    )

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        logging.info(f'Email sent: {response.status_code}')
    except Exception as e:
        logging.error(f'Error sending email: {e}')