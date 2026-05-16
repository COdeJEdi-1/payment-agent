
# Design Document — Payment Collection AI Agent

## Architecture Overview

The agent is structured as a set of single-responsibility modules that the main Agent class orchestrates:

    User Input
        |
        v
    agent.py (Agent.next)
        |
        |-- extractor.py   Extract structured data from messy natural language
        |-- verifier.py    Strict identity verification logic
        |-- tools.py       API calls to lookup and payment endpoints
        |-- state.py       Full conversation state held in memory
        |
        v
    Agent Response

Each call to Agent.next() represents one turn. The agent reads the current stage from ConversationState, processes the input, updates state, and returns a response. No external memory or database is used — all state lives in the ConversationState object for the duration of the session.

## Module Breakdown

### agent.py
The central orchestrator. Contains the Agent class with a single public method next(user_input) that returns a dict with a message key. Internally routes to stage-specific handlers: _handle_verify, _handle_amount, _handle_card, _do_payment. Each handler reads and mutates ConversationState.

### state.py
Defines three dataclasses: AccountData (API response), CardData (card fields collected across turns), and ConversationState (full session memory). Stage constants are defined as a class with string values. Separating state into a dedicated module prevents it from being scattered across business logic.

### tools.py
Two functions: lookup_account and process_payment. Each makes one HTTP POST request to the provided API, handles all status codes, and raises clear exceptions on network failures. No business logic lives here — just clean API calls.

### verifier.py
Pure Python verification logic with no LLM dependency. Implements the exact rules from the spec: name must match exactly (case sensitive, strip whitespace only), plus at least one secondary factor (DOB, Aadhaar last 4, or pincode) must match. Returns a dict with verified and reason fields so the caller can respond precisely to each failure mode.

### extractor.py
Uses Groq (Llama 3.3-70b) to extract structured data from free-form user input. Each turn makes one API call extracting all possible fields at once. The LLM returns structured text which is then validated in Python (date parsing with datetime.strptime, digit length checks). This is the only module with an LLM dependency.

### run.py
A simple CLI loop for interactive testing. Calls Agent.next() in a loop and prints responses. Stops when the agent reaches Stage.DONE.

### eval.py
14 automated test cases covering happy paths, verification failures, payment failures, and edge cases. Each test runs a full conversation and checks that each agent response contains an expected keyword. Reports per-test and overall pass rates.

## Key Design Decisions

### LLM for extraction, Python for logic
The LLM is used only for one thing: extracting structured data from messy natural language. All business logic — verification, stage transitions, retry counting, payment validation — is deterministic Python. This makes the agent predictable and easy to test. If the LLM extracts the wrong thing, the Python logic catches it with validation.

### Stage machine over open-ended conversation
The agent uses a strict stage machine (GREET, LOOKUP, VERIFY, SHOW_BALANCE, COLLECT_CARD, PROCESS_PAYMENT, DONE) rather than a free-form LLM conversation. This guarantees the flow is always followed in order, sensitive data is never skipped over, and verification always happens before payment. It also makes the agent fully deterministic and testable.

### Separate retry counters for name and secondary factor
An early version used a single verify_attempts counter for both name mismatches and secondary factor mismatches. This was unfair to users. The final version uses separate counters (verify_attempts for name, secondary_attempts for secondary factor), giving users a fair number of attempts at each step independently.

### Strict name matching
The spec requires no fuzzy matching. The extractor is explicitly prompted to return the name exactly as the user typed it, preserving case. The verifier then does an exact string comparison after stripping whitespace only. This means nithin jain correctly fails against Nithin Jain.

### Card data cleared after payment
Raw card data is cleared from ConversationState immediately after the payment API call regardless of success or failure. This minimises the time sensitive card data lives in memory.

### Retryable vs terminal payment errors
Not all payment failures are equal. Invalid card number, CVV, and expiry are user-fixable — the agent resets only the failing field and asks the user to try again. Insufficient balance routes back to the amount collection step. Unknown errors close the session cleanly.

### Python-side date validation
After the LLM extracts a date string, Python validates it with datetime.strptime before accepting it. This catches cases where the LLM returns an invalid date like Feb 29 on a non-leap year, which would otherwise silently fail verification.

## Tradeoffs

### Groq free tier rate limits
The free tier has per-minute token limits that make running the full eval suite in one pass occasionally difficult. This is a deployment constraint not a code issue. In production this would be solved by using a paid API tier or a self-hosted model.

### LLM non-determinism
Groq with temperature=0 is highly consistent but not guaranteed to be identical across runs. Edge cases like ambiguous names or unusual date formats may occasionally be extracted incorrectly. The Python-side validation catches the most critical errors.

### No conversation history sent to LLM
Each extraction prompt contains only the current user message, not the full conversation history. This keeps prompts short and fast but means the LLM cannot use context from earlier turns. The ConversationState handles context instead — once a field is stored it is never re-asked.

### Session is not resumable
ConversationState lives in memory for the duration of one Agent instance. If the process restarts, the session is lost. In production this would be stored in a database keyed by session ID.

## What I Would Improve With More Time

1. Persistent session storage so conversations survive process restarts
2. A paid LLM tier to eliminate rate limit issues in automated eval
3. Confidence scoring on LLM extractions — if the model is uncertain, ask the user to clarify
4. Webhook or async payment processing for slow API responses
5. Structured logging of all turns for debugging and audit
6. A web interface instead of CLI for easier demonstration
7. Multi-language support for regional Indian languages
