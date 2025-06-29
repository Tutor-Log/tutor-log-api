from enum import Enum

# Enums for better type safety
class GenderEnum(str, Enum):
    MALE = "M"
    FEMALE = "F"
    OTHER = "Other"

class EventTypeEnum(str, Enum):
    ONCE = "once"
    REPEAT = "repeat"

class RepeatPatternEnum(str, Enum):
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM_DAYS = "custom_days"

class PaymentModeEnum(str, Enum):
    CASH = "cash"
    UPI = "upi"
    BANK_TRANSFER = "bank_transfer"
    CARD = "card"
    CHEQUE = "cheque"
