import re
import logging

AADHAAR_REGEX = re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b")
PHONE_REGEX = re.compile(r"\b(?:\+91[\-\s]?)?[6-9]\d{9}\b")
EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")

class PIIRedactionFilter(logging.Filter):
    """Logging filter that scrubs Indian Aadhaar numbers, phone numbers, and emails from log output."""
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = self.redact(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: self.redact(v) if isinstance(v, str) else v for k, v in record.args.items()}
            elif isinstance(record.args, (list, tuple)):
                record.args = tuple(self.redact(arg) if isinstance(arg, str) else arg for arg in record.args)
        return True

    @classmethod
    def redact(cls, text: str) -> str:
        if not isinstance(text, str):
            return text
        text = AADHAAR_REGEX.sub("[REDACTED_AADHAAR]", text)
        text = PHONE_REGEX.sub("[REDACTED_PHONE]", text)
        text = EMAIL_REGEX.sub("[REDACTED_EMAIL]", text)
        return text
