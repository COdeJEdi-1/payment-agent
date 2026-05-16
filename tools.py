
import requests
from state import AccountData

BASE_URL = "https://se-payment-verification-api.service.external.usea2.aws.prodigaltech.com"


def lookup_account(account_id: str):
    try:
        response = requests.post(
            f"{BASE_URL}/api/lookup-account",
            json={"account_id": account_id},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            return AccountData(
                account_id=data["account_id"],
                full_name=data["full_name"],
                dob=data["dob"],
                aadhaar_last4=data["aadhaar_last4"],
                pincode=data["pincode"],
                balance=data["balance"]
            )
        elif response.status_code == 404:
            return None
        else:
            raise Exception(f"Unexpected API error: {response.status_code}")
    except requests.exceptions.Timeout:
        raise Exception("The server took too long to respond. Please try again.")
    except requests.exceptions.ConnectionError:
        raise Exception("Could not connect to the server. Please try again.")


def process_payment(account_id: str, amount: float, card: dict):
    payload = {
        "account_id": account_id,
        "amount": amount,
        "payment_method": {
            "type": "card",
            "card": card
        }
    }
    try:
        response = requests.post(
            f"{BASE_URL}/api/process-payment",
            json=payload,
            timeout=10
        )
        data = response.json()
        if response.status_code == 200 and data.get("success"):
            return {"success": True, "transaction_id": data["transaction_id"]}
        else:
            return {"success": False, "error_code": data.get("error_code", "unknown_error")}
    except requests.exceptions.Timeout:
        raise Exception("Payment server timed out. Please try again.")
    except requests.exceptions.ConnectionError:
        raise Exception("Could not connect to payment server. Please try again.")
