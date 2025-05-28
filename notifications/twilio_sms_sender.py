from twilio.rest import Client
import os
from core.logging import log

class TwilioSMSSender:
    """Simple wrapper around the Twilio REST client for SMS."""

    def __init__(self, account_sid=None, auth_token=None, from_number=None):
        self.account_sid = account_sid or os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = auth_token or os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = from_number or os.getenv("TWILIO_FROM_NUMBER")
        self.client = Client(self.account_sid, self.auth_token)

    def send_sms(self, to_number: str, message: str) -> bool:
        """Send an SMS message via Twilio."""
        try:
            if not all([self.account_sid, self.auth_token, self.from_number, to_number]):
                log.error("Missing Twilio SMS configuration", source="TwilioSMSSender")
                return False

            msg = self.client.messages.create(body=message, from_=self.from_number, to=to_number)
            log.info(
                "✅ SMS sent",
                source="TwilioSMSSender",
                payload={"sid": getattr(msg, "sid", None)}
            )
            return True
        except Exception as e:
            log.error(f"❌ Failed to send SMS: {e}", source="TwilioSMSSender")
            return False

