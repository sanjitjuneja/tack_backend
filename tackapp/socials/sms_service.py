from twilio.rest import Client
from django.conf import settings


class TwilioClient:
    def __init__(self):
        self.account_sid = settings.TWILIO_ACCOUNT_SID
        self.auth_token = settings.TWILIO_AUTH_TOKEN
        self.client = Client(self.account_sid, self.auth_token)
        self.text_signup = ("Your phone number verify Code is: {sms_code}. "
                            "If you did not make this recovery attempt, contact us immediately.")
        self.text_recovery = ("Your Tack recovery code is: {sms_code}. If you did not "
                              "make this recovery attempt, contact us immediately.")

    def send_signup_message(self, phone_number: str, sms_code: str):
        """Function to sending SMS for subsequent verifying"""

        message = self.client.messages.create(
            messaging_service_sid=settings.MESSAGING_SERVICE_SID,
            body=self.text_signup.format(sms_code=sms_code),
            to=f"{phone_number}",
        )
        return message.sid

    def send_recovery_message(self, phone_number: str, sms_code: str):
        """Function to sending SMS for password recovery"""

        message = self.client.messages.create(
            messaging_service_sid=settings.MESSAGING_SERVICE_SID,
            body=self.text_signup.format(sms_code=sms_code),
            to=f"{phone_number}",
        )
        return message.sid


twilio_client = TwilioClient()
