
import os
import json
from datetime import datetime
from groq import Groq

client = Groq(api_key=os.environ["GROQ_API_KEY"])


def _ask_groq(prompt: str) -> str:
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return response.choices[0].message.content.strip()


def extract_account_id(text: str) -> str | None:
    prompt = f"""
Extract the account ID from this text. Account IDs start with ACC followed by digits (like ACC1001, ACC1002).
Ignore spaces, punctuation, case differences — normalize to uppercase with no spaces.
Text: "{text}"
Reply with ONLY the account ID (e.g. ACC1001) or null if none found.
No explanation, no punctuation, just the ID or null.
"""
    result = _ask_groq(prompt).strip()
    if result.lower() == "null" or result == "":
        return None
    return result.upper().replace(" ", "")


def extract_full_name(text: str) -> str | None:
    prompt = f"""
Extract the person's full name from this text.
People may say "my name is X", "I am X", "you can call me Y but my full name is X".
Always return the FULL name, not a nickname.

CRITICAL RULES:
- Return the name EXACTLY as the user wrote it. Do NOT fix capitalization or formatting.
- If the user says "my name is nithin jain" return "nithin jain" not "Nithin Jain"
- Return ONLY the name itself, never include words like "my name is", "I am", "it is", "its"
- Only return null if there is clearly no name at all in the text

Text: "{text}"
Reply with ONLY the name exactly as written by the user, or null if no name found.
No explanation, just the name or null.
"""
    result = _ask_groq(prompt).strip()
    if result.lower() == "null" or result == "":
        return None
    return result


def extract_dob(text: str) -> str | None:
    prompt = f"""
Extract the date of birth from this text and convert it to YYYY-MM-DD format.
Handle all formats: "14th May 1990", "May 14 1990", "14-05-1990", "DOB is May 14, 90" etc.
For 2-digit years assume 1900s (so 90 = 1990).
Validate the date is real (e.g. Feb 29 only valid on leap years).
Text: "{text}"
Reply with ONLY the date in YYYY-MM-DD format or null if invalid or not found.
No explanation, just the date or null.
"""
    result = _ask_groq(prompt).strip()
    if result.lower() == "null" or result == "":
        return None
    try:
        datetime.strptime(result, "%Y-%m-%d")
        return result
    except ValueError:
        return None


def extract_aadhaar_last4(text: str) -> str | None:
    prompt = f"""
Extract the last 4 digits of the Aadhaar number from this text.
People may say "last four of my Aadhaar is 4321", "Aadhaar ends with 9876".
Text: "{text}"
Reply with ONLY the 4 digits or null if not found.
No explanation, just 4 digits or null.
"""
    result = _ask_groq(prompt).strip()
    if result.lower() == "null" or result == "" or not result.isdigit() or len(result) != 4:
        return None
    return result


def extract_pincode(text: str) -> str | None:
    prompt = f"""
Extract the 6-digit Indian pincode from this text.
People may say "pincode is 400001" or "it's 4 0 0 0 0 1" (digit by digit).
Remove all spaces between digits.
Text: "{text}"
Reply with ONLY the 6 digits or null if not found.
No explanation, just 6 digits or null.
"""
    result = _ask_groq(prompt).strip().replace(" ", "")
    if result.lower() == "null" or result == "" or not result.isdigit() or len(result) != 6:
        return None
    return result


def extract_payment_amount(text: str, balance: float) -> float | None:
    prompt = f"""
Extract the payment amount from this text. Outstanding balance is {balance}.
- "pay 500" → 500.0
- "a thousand rupees" → 1000.0
- "clear the full amount" / "pay all" / "pay everything" → {balance}
- "500 for now" → 500.0
Text: "{text}"
Reply with ONLY the numeric amount or null if not found. No currency symbol.
No explanation, just the number or null.
"""
    result = _ask_groq(prompt).strip()
    if result.lower() == "null" or result == "":
        return None
    try:
        return round(float(result), 2)
    except:
        return None


def extract_card_details(text: str) -> dict:
    prompt = f"""
Extract card payment details from this text.
- Card numbers may have spaces: "4532 0151 1283 0366" → "4532015112830366"
- Expiry: "December 2027" or "12/27" → month=12, year=2027
- CVV spoken: "one two three" → "123"
Text: "{text}"
Reply with ONLY this JSON (null for anything not found):
{{
  "card_number": "digits only no spaces",
  "expiry_month": integer or null,
  "expiry_year": 4-digit integer or null,
  "cvv": "digits only" or null,
  "cardholder_name": "name" or null
}}
No explanation, just the JSON.
"""
    result = _ask_groq(prompt).strip()
    result = result.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(result)
    except:
        return {
            "card_number": None,
            "expiry_month": None,
            "expiry_year": None,
            "cvv": None,
            "cardholder_name": None
        }


def looks_like_name_attempt(text: str) -> bool:
    prompt = f"""
Does this text look like someone is trying to provide their name, even if it's wrong or incomplete?
Examples that ARE name attempts: "Wrong Person", "John", "my name is xyz", "it's kumar"
Examples that are NOT name attempts: "I don't know", "what?", "help me", "skip this"

Text: "{text}"
Reply with ONLY yes or no.
"""
    result = _ask_groq(prompt).strip().lower()
    return result == "yes"
