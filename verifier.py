
from state import AccountData


def verify_identity(account: AccountData, provided_name: str,
                    provided_dob: str = None,
                    provided_aadhaar: str = None,
                    provided_pincode: str = None) -> dict:

    if provided_name is None:
        return {"verified": False, "reason": "name_missing"}

    if provided_name.strip() != account.full_name.strip():
        return {"verified": False, "reason": "name_mismatch"}

    if provided_dob is not None:
        if provided_dob.strip() == account.dob.strip():
            return {"verified": True, "reason": "name_and_dob"}

    if provided_aadhaar is not None:
        if provided_aadhaar.strip() == account.aadhaar_last4.strip():
            return {"verified": True, "reason": "name_and_aadhaar"}

    if provided_pincode is not None:
        if provided_pincode.strip() == account.pincode.strip():
            return {"verified": True, "reason": "name_and_pincode"}

    if provided_dob is None and provided_aadhaar is None and provided_pincode is None:
        return {"verified": False, "reason": "secondary_missing"}

    return {"verified": False, "reason": "secondary_mismatch"}
