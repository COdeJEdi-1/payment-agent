
# Payment Collection AI Agent

A conversational AI agent that handles end-to-end payment collection flows. The agent guides users through account lookup, identity verification, and card payment processing via natural conversation.

## Project Structure

    payment_agent/
    ├── agent.py          # Main Agent class — entry point for all conversations
    ├── state.py          # Conversation state definitions and stage constants
    ├── tools.py          # API calls — account lookup and payment processing
    ├── verifier.py       # Identity verification logic
    ├── extractor.py      # NLP extraction using Groq (Llama 3.3)
    ├── run.py            # Interactive CLI to chat with the agent
    ├── eval.py           # Automated evaluation with 14 test cases
    └── requirements.txt  # Python dependencies

## Setup

### 1. Clone the repository

    git clone <your-repo-url>
    cd payment_agent

### 2. Install dependencies

    pip install -r requirements.txt

### 3. Set your Groq API key

Create a .env file in the project root:

    GROQ_API_KEY=your-groq-api-key-here

Get a free API key at: https://console.groq.com

### 4. Run the agent interactively

    python run.py

### 5. Run the evaluation suite

    python eval.py

Note: The eval suite runs 14 tests sequentially. On Groq free tier you may hit rate limits. If this happens wait a few minutes and run again.

## How It Works

The agent follows a strict 8-step flow:

1. Greet the user and ask for account ID
2. Look up the account via API
3. Collect and verify identity — name plus one secondary factor
4. Show outstanding balance
5. Collect payment amount
6. Collect card details
7. Process payment via API
8. Confirm outcome with full payment summary

## Identity Verification

Verification requires full name exact match (case sensitive) plus at least one of: date of birth, last 4 digits of Aadhaar, or pincode.

Users get 3 attempts for name verification and 3 attempts for secondary factor verification before the session is closed for security.

Sensitive data (DOB, Aadhaar, pincode) is never shown back to the user at any point.

## Handling Messy Input

The agent uses Groq Llama 3.3-70b to extract structured data from natural language:

    User says                                           Agent understands
    "yeah my account is ACC 1001 i think"              ACC1001
    "you can call me Raja but full name is             Rajarajeswari Balasubramaniam
     Rajarajeswari Balasubramaniam"
    "I was born 14th may 1990"                         1990-05-14
    "card 4532 0151 1283 0366 expires dec 2027         full card details extracted
     cvv one two three"

## Test Accounts

    Account ID   Name                              Balance
    ACC1001      Nithin Jain                       1250.75
    ACC1002      Rajarajeswari Balasubramaniam     540.00
    ACC1003      Priya Agarwal                     0.00
    ACC1004      Rahul Mehta (leap year DOB)       3200.50

## Sample Conversations

See sample_conversations.md for full conversation examples covering success, failure, and edge cases.

## Evaluation

The eval suite covers 14 test cases including happy paths, verification failures, payment failures, and edge cases.

Run with:

    python eval.py

Result: 82/82 checks passed (100%)

Note on rate limits: Groq free tier has per-minute token limits. If the full eval hits rate limits, wait a few minutes and rerun.
