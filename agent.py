
from state import ConversationState, Stage, CardData
from tools import lookup_account, process_payment
from verifier import verify_identity
from extractor import (
    extract_account_id, extract_full_name, extract_dob,
    extract_aadhaar_last4, extract_pincode,
    extract_payment_amount, extract_card_details,
    looks_like_name_attempt
)

RETRYABLE_ERRORS = {"invalid_card", "invalid_cvv", "invalid_expiry"}


class Agent:
    def __init__(self):
        self.state = ConversationState()

    def next(self, user_input: str) -> dict:
        user_input = user_input.strip()
        try:
            response = self._handle(user_input)
        except Exception as e:
            response = f"Sorry, something went wrong on our end. Please try again. (Error: {str(e)})"
        return {"message": response}

    def _handle(self, user_input: str) -> str:
        s = self.state

        if s.stage == Stage.DONE:
            return "This conversation has ended. Please start a new session if you need further assistance."

        if s.stage == Stage.GREET:
            account_id = extract_account_id(user_input)
            if account_id:
                s.account_id = account_id
                s.stage = Stage.LOOKUP
                lookup_response = self._do_lookup()
                return "Hello! Welcome to the payment collection service.\n\n" + lookup_response
            s.stage = Stage.LOOKUP
            return (
                "Hello! Welcome to the payment collection service. "
                "Could you please share your account ID to get started?"
            )

        if s.stage == Stage.LOOKUP:
            account_id = extract_account_id(user_input)
            if not account_id:
                return (
                    "I couldn't find an account ID in your message. "
                    "Could you please share your account ID? (e.g. ACC1001)"
                )
            s.account_id = account_id
            return self._do_lookup()

        if s.stage == Stage.VERIFY:
            return self._handle_verify(user_input)

        if s.stage == Stage.SHOW_BALANCE:
            return self._handle_amount(user_input)

        if s.stage == Stage.COLLECT_CARD:
            return self._handle_card(user_input)

        if s.stage == Stage.PROCESS_PAYMENT:
            return self._do_payment()

        return "I'm not sure how to handle that. Could you please try again?"

    def _do_lookup(self) -> str:
        s = self.state
        try:
            account = lookup_account(s.account_id)
        except Exception as e:
            s.stage = Stage.LOOKUP
            return (
                "We're having trouble reaching our servers. "
                "Please try again. Could you re-enter your account ID?"
            )

        if account is None:
            saved_id = s.account_id
            s.account_id = None
            return (
                f"We couldn't find an account with ID '{saved_id}'. "
                "Please double-check your account ID and try again."
            )

        s.account_data = account
        s.stage = Stage.VERIFY
        return (
            "Got it! I found your account. "
            "For security purposes, I need to verify your identity. "
            "Could you please share your full name as it appears on your account?"
        )

    def _handle_verify(self, user_input: str) -> str:
        s = self.state

        extracted_name = extract_full_name(user_input)
        extracted_dob = extract_dob(user_input)
        extracted_aadhaar = extract_aadhaar_last4(user_input)
        extracted_pincode = extract_pincode(user_input)

        if s.provided_name is None:

            if extracted_name is None:
                if looks_like_name_attempt(user_input):
                    s.verify_attempts += 1
                    remaining = s.MAX_VERIFY_ATTEMPTS - s.verify_attempts
                    if remaining <= 0:
                        s.stage = Stage.DONE
                        return (
                            "I'm sorry, but we've been unable to verify your identity "
                            "after multiple attempts. For security reasons, this session "
                            "has been closed. Please contact customer support for assistance."
                        )
                    return (
                        "I was not able to catch your full name clearly. "
                        "Could you please share your full name exactly as it appears on your account? "
                        f"({remaining} attempt(s) remaining)"
                    )
                else:
                    return (
                        "Could you please share your full name "
                        "as it appears on your account?"
                    )

            name_check = verify_identity(s.account_data, extracted_name)
            if name_check["reason"] == "name_mismatch":
                s.verify_attempts += 1
                remaining = s.MAX_VERIFY_ATTEMPTS - s.verify_attempts
                if remaining <= 0:
                    s.stage = Stage.DONE
                    return (
                        "I'm sorry, but we've been unable to verify your identity "
                        "after multiple attempts. For security reasons, this session "
                        "has been closed. Please contact customer support for assistance."
                    )
                return (
                    "The name you provided does not match our records. "
                    "Please provide your full name exactly as it appears on your account. "
                    f"({remaining} attempt(s) remaining)"
                )

            s.provided_name = extracted_name

        if extracted_dob and s.provided_dob is None:
            s.provided_dob = extracted_dob
        if extracted_aadhaar and s.provided_aadhaar is None:
            s.provided_aadhaar = extracted_aadhaar
        if extracted_pincode and s.provided_pincode is None:
            s.provided_pincode = extracted_pincode

        if s.provided_dob is None and s.provided_aadhaar is None and s.provided_pincode is None:
            return (
                "Thank you. To complete verification, could you please "
                "provide one of the following: your date of birth, "
                "last 4 digits of your Aadhaar, or your pincode?"
            )

        result = verify_identity(
            s.account_data,
            s.provided_name,
            provided_dob=s.provided_dob,
            provided_aadhaar=s.provided_aadhaar,
            provided_pincode=s.provided_pincode
        )

        if result["verified"]:
            s.is_verified = True
            s.stage = Stage.SHOW_BALANCE
            balance = s.account_data.balance
            if balance == 0:
                s.stage = Stage.DONE
                return (
                    "Identity verified. Your current outstanding balance is Rs. 0.00. "
                    "You have no pending dues at this time. Have a great day!"
                )
            return (
                f"Identity verified. Your outstanding balance is Rs. {balance:,.2f}. "
                "How much would you like to pay? You can pay the full amount or a partial amount."
            )

        s.secondary_attempts += 1
        remaining = s.MAX_SECONDARY_ATTEMPTS - s.secondary_attempts

        if remaining <= 0:
            s.stage = Stage.DONE
            return (
                "I'm sorry, but we've been unable to verify your identity "
                "after multiple attempts. For security reasons, this session "
                "has been closed. Please contact customer support for assistance."
            )

        s.provided_dob = None
        s.provided_aadhaar = None
        s.provided_pincode = None

        return (
            "The details you provided do not match our records. "
            "Please try again with your date of birth, "
            "last 4 digits of Aadhaar, or pincode. "
            f"({remaining} attempt(s) remaining)"
        )

    def _handle_amount(self, user_input: str) -> str:
        s = self.state
        balance = s.account_data.balance
        amount = extract_payment_amount(user_input, balance)

        if amount is None:
            return (
                f"I couldn't understand the amount. "
                f"Your outstanding balance is Rs. {balance:,.2f}. "
                "How much would you like to pay?"
            )
        if amount <= 0:
            return (
                "The payment amount must be greater than zero. "
                "How much would you like to pay?"
            )
        if amount != round(amount, 2):
            return (
                "Please enter an amount with at most 2 decimal places. "
                "How much would you like to pay?"
            )
        if amount > balance:
            return (
                f"The amount Rs. {amount:,.2f} exceeds your outstanding "
                f"balance of Rs. {balance:,.2f}. "
                "Please enter an amount equal to or less than your balance."
            )

        s.payment_amount = amount
        s.stage = Stage.COLLECT_CARD
        return (
            f"Got it, Rs. {amount:,.2f} it is.\n\n"
            "Please share your card details:\n"
            "- Card number\n"
            "- Expiry date (month and year)\n"
            "- CVV\n"
            "- Name on card (if different from account name)"
        )

    def _handle_card(self, user_input: str) -> str:
        s = self.state
        card = s.card_data
        extracted = extract_card_details(user_input)

        if extracted.get("card_number"):
            card.card_number = extracted["card_number"]
        if extracted.get("expiry_month"):
            card.expiry_month = extracted["expiry_month"]
        if extracted.get("expiry_year"):
            card.expiry_year = extracted["expiry_year"]
        if extracted.get("cvv"):
            card.cvv = extracted["cvv"]
        if extracted.get("cardholder_name"):
            card.cardholder_name = extracted["cardholder_name"]

        if not card.cardholder_name:
            card.cardholder_name = s.account_data.full_name

        missing = []
        if not card.card_number:
            missing.append("card number")
        if not card.expiry_month or not card.expiry_year:
            missing.append("expiry date (month and year)")
        if not card.cvv:
            missing.append("CVV")

        if missing:
            return (
                f"Thanks! I still need your {', '.join(missing)}. "
                "Could you please provide that?"
            )

        s.stage = Stage.PROCESS_PAYMENT
        return self._do_payment()

    def _do_payment(self) -> str:
        s = self.state
        card = s.card_data

        card_payload = {
            "cardholder_name": card.cardholder_name,
            "card_number": card.card_number,
            "cvv": card.cvv,
            "expiry_month": card.expiry_month,
            "expiry_year": card.expiry_year
        }

        try:
            result = process_payment(s.account_id, s.payment_amount, card_payload)
        except Exception as e:
            s.stage = Stage.DONE
            return (
                "We encountered an error processing your payment. "
                f"Please try again later. ({str(e)})"
            )

        s.card_data = CardData()

        if result["success"]:
            s.transaction_id = result["transaction_id"]
            s.stage = Stage.DONE
            return (
                f"Your payment of Rs. {s.payment_amount:,.2f} has been processed successfully.\n\n"
                f"Account: {s.account_id}\n"
                f"Amount: Rs. {s.payment_amount:,.2f}\n"
                f"Transaction ID: {result['transaction_id']}\n\n"
                "Please save your transaction ID for your records. "
                "Thank you for your payment."
            )

        error_code = result.get("error_code", "unknown_error")

        if error_code in RETRYABLE_ERRORS:
            s.stage = Stage.COLLECT_CARD
            if error_code == "invalid_card":
                s.card_data = CardData()
                return (
                    "The card number you entered does not appear to be valid. "
                    "Please check and try again.\n\n"
                    "Please share your card details again:\n"
                    "- Card number\n"
                    "- Expiry date\n"
                    "- CVV"
                )
            elif error_code == "invalid_cvv":
                s.card_data.cvv = None
                return (
                    "The CVV you entered does not match. "
                    "Please check the 3-digit code on the back of your card "
                    "and try again."
                )
            elif error_code == "invalid_expiry":
                s.card_data.expiry_month = None
                s.card_data.expiry_year = None
                return (
                    "The expiry date you entered is invalid or the card has expired. "
                    "Please provide a valid expiry date."
                )

        if error_code == "insufficient_balance":
            s.stage = Stage.SHOW_BALANCE
            s.payment_amount = None
            return (
                f"The payment could not go through as the amount exceeds "
                f"your current balance of Rs. {s.account_data.balance:,.2f}. "
                "Please enter a lower amount to continue."
            )

        s.stage = Stage.DONE
        terminal_messages = {
            "invalid_amount": (
                "The payment amount is invalid. "
                "Please start a new session and try again."
            ),
        }
        return terminal_messages.get(
            error_code,
            f"We were unable to process your payment ({error_code}). "
            "Please contact customer support for assistance."
        )
