from notifications.twilio_sms_sender import TwilioSMSSender


def test_twilio_sms_sender(monkeypatch):
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "sid")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token")
    monkeypatch.setenv("TWILIO_FROM_PHONE", "+10000000000")

    sender = TwilioSMSSender()
    assert sender.send_sms("+15555555555", "test") is True


def test_twilio_sms_sender_number_fallback(monkeypatch):
    """Legacy TWILIO_FROM_NUMBER env var should still work."""
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "sid")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token")
    monkeypatch.delenv("TWILIO_FROM_PHONE", raising=False)
    monkeypatch.setenv("TWILIO_FROM_NUMBER", "+12223334444")

    sender = TwilioSMSSender()
    assert sender.from_number == "+12223334444"
