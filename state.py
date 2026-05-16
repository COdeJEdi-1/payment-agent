
from dataclasses import dataclass, field
from typing import Optional


class Stage:
    GREET           = "greet"
    LOOKUP          = "lookup"
    VERIFY          = "verify"
    SHOW_BALANCE    = "show_balance"
    COLLECT_CARD    = "collect_card"
    PROCESS_PAYMENT = "process_payment"
    DONE            = "done"


@dataclass
class AccountData:
    account_id: str
    full_name: str
    dob: str
    aadhaar_last4: str
    pincode: str
    balance: float


@dataclass
class CardData:
    cardholder_name: Optional[str] = None
    card_number: Optional[str] = None
    cvv: Optional[str] = None
    expiry_month: Optional[int] = None
    expiry_year: Optional[int] = None


@dataclass
class ConversationState:
    stage: str = Stage.GREET

    account_id: Optional[str] = None
    account_data: Optional[AccountData] = None

    provided_name: Optional[str] = None
    provided_dob: Optional[str] = None
    provided_aadhaar: Optional[str] = None
    provided_pincode: Optional[str] = None
    is_verified: bool = False

    verify_attempts: int = 0
    secondary_attempts: int = 0
    MAX_VERIFY_ATTEMPTS: int = 3
    MAX_SECONDARY_ATTEMPTS: int = 3

    payment_amount: Optional[float] = None
    card_data: CardData = field(default_factory=CardData)
    transaction_id: Optional[str] = None
    payment_error: Optional[str] = None
