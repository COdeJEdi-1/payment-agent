

import sys
for mod in ['agent', 'extractor', 'verifier', 'tools', 'state']:
    if mod in sys.modules:
        del sys.modules[mod]

from agent import Agent


def run_conversation(turns, test_name):
    agent = Agent()
    passed = 0
    failed = 0

    print(f"\n{test_name}")
    print(f"{'-' * len(test_name)}")

    for i, (user_input, expected_keyword) in enumerate(turns):
        response = agent.next(user_input)["message"]

        if expected_keyword is None:
            ok = True
        else:
            ok = expected_keyword.lower() in response.lower()

        if ok:
            passed += 1
        else:
            failed += 1
            print(f"  [turn {i+1}] FAIL — expected '{expected_keyword}' in response")
            print(f"    user: {user_input}")
            print(f"    agent: {response[:100]}{'...' if len(response) > 100 else ''}")

    total = passed + failed
    score = round((passed / total) * 100, 1) if total > 0 else 0
    print(f"  passed {passed}/{total}")
    return {"test": test_name, "passed": passed, "failed": failed, "score": score}


def test_happy_path():
    return run_conversation([
        ("Hi there",                                                   "account"),
        ("yeah my account is ACC1001 I think",                         "found"),
        ("my name is Nithin Jain",                                     "date of birth"),
        ("I was born on 14th May 1990",                                "verified"),
        ("just clear the full amount",                                  "card"),
        ("card is 4532 0151 1283 0366 expires December 2027 cvv 123", "successful"),
    ], "Happy path — full payment with messy inputs")


def test_happy_path_aadhaar():
    return run_conversation([
        ("Hi",                                                          "account"),
        ("ACC1001",                                                     "found"),
        ("Nithin Jain",                                                 "date of birth"),
        ("last four of my aadhaar is 4321",                            "verified"),
        ("500",                                                         "card"),
        ("card is 4532 0151 1283 0366 expires December 2027 cvv 123", "successful"),
    ], "Happy path — verify with Aadhaar")


def test_happy_path_pincode():
    return run_conversation([
        ("Hi",                                                          "account"),
        ("ACC1001",                                                     "found"),
        ("Nithin Jain",                                                 "date of birth"),
        ("my pincode is 400001",                                        "verified"),
        ("pay 500",                                                     "card"),
        ("4532 0151 1283 0366 12/2027 cvv 123",                        "successful"),
    ], "Happy path — verify with pincode")


def test_partial_payment():
    return run_conversation([
        ("Hi",                                                          "account"),
        ("ACC1001",                                                     "found"),
        ("Nithin Jain",                                                 "date of birth"),
        ("1990-05-14",                                                  "verified"),
        ("can I pay 500 for now?",                                      "500"),
        ("card is 4532 0151 1283 0366 expires December 2027 cvv 123", "successful"),
    ], "Partial payment")


def test_verification_name_fail_then_pass():
    return run_conversation([
        ("Hi",                                                          "account"),
        ("ACC1001",                                                     "found"),
        ("nithin jain",                                                 "does not match"),
        ("Nithin Jain",                                                 "date of birth"),
        ("4321",                                                        "verified"),
        ("pay full amount",                                             "card"),
        ("4532 0151 1283 0366 expires December 2027 cvv 123",          "successful"),
    ], "Verification — wrong name then correct")


def test_verification_exhausted():
    return run_conversation([
        ("Hi",              "account"),
        ("ACC1001",         "found"),
        ("Wrong Person",    "not able"),
        ("Another Wrong",   "not able"),
        ("Still Wrong",     "closed"),
    ], "Verification — all attempts exhausted")


def test_secondary_factor_fail_then_pass():
    return run_conversation([
        ("Hi",                                                          "account"),
        ("ACC1001",                                                     "found"),
        ("Nithin Jain",                                                 "date of birth"),
        ("1990-01-01",                                                  "do not match"),
        ("my aadhaar is 4321",                                         "verified"),
        ("pay full",                                                    "card"),
        ("4532 0151 1283 0366 expires December 2027 cvv 123",          "successful"),
    ], "Verification — wrong secondary factor then correct")


def test_invalid_account():
    return run_conversation([
        ("Hi",              "account"),
        ("ACC9999",         "couldn't find"),
        ("ACC1001",         "found"),
        ("Nithin Jain",     "date of birth"),
    ], "Invalid account ID")


def test_zero_balance():
    return run_conversation([
        ("Hi",              "account"),
        ("ACC1003",         "found"),
        ("Priya Agarwal",   "date of birth"),
        ("10th August 1992","0.00"),
    ], "Zero balance account")


def test_long_name():
    return run_conversation([
        ("Hi",                                                          "account"),
        ("ACC1002",                                                     "found"),
        ("Rajarajeswari Balasubramaniam",                               "date of birth"),
        ("aadhaar last 4 is 9876",                                     "verified"),
        ("clear full amount",                                           "card"),
        ("4532 0151 1283 0366 expires December 2027 cvv 123",          "successful"),
    ], "Long Indian name (ACC1002)")


def test_amount_exceeds_balance():
    return run_conversation([
        ("Hi",              "account"),
        ("ACC1001",         "found"),
        ("Nithin Jain",     "date of birth"),
        ("1990-05-14",      "verified"),
        ("pay 99999",       "exceeds"),
        ("pay 500",         "card"),
        ("4532 0151 1283 0366 expires December 2027 cvv 123",          "successful"),
    ], "Amount exceeds balance")


def test_card_details_across_turns():
    return run_conversation([
        ("Hi",                                                          "account"),
        ("ACC1001",                                                     "found"),
        ("Nithin Jain",                                                 "date of birth"),
        ("1990-05-14",                                                  "verified"),
        ("pay 500",                                                     "card"),
        ("card number is 4532 0151 1283 0366",                         "still need"),
        ("expires December 2027 cvv 123",                              "successful"),
    ], "Card details provided across multiple turns")


def test_leap_year_dob():
    return run_conversation([
        ("Hi",              "account"),
        ("ACC1004",         "found"),
        ("Rahul Mehta",     "date of birth"),
        ("29th Feb 1988",   "verified"),
        ("pay 1000",        "card"),
        ("4532 0151 1283 0366 expires December 2027 cvv 123",          "successful"),
    ], "Edge case — leap year date of birth (ACC1004)")


def test_session_closed_after_done():
    return run_conversation([
        ("Hi",              "account"),
        ("ACC1003",         "found"),
        ("Priya Agarwal",   "date of birth"),
        ("1992-08-10",      "0.00"),
        ("hello again",     "ended"),
    ], "Session closed after conversation ends")


def test_payment_invalid_card():
    return run_conversation([
        ("Hi",                                                              "account"),
        ("ACC1001",                                                         "found"),
        ("Nithin Jain",                                                     "date of birth"),
        ("1990-05-14",                                                      "verified"),
        ("pay 500",                                                         "card"),
        ("card 1234567890123456 expires december 2027 cvv 123",            "valid"),
        ("4532 0151 1283 0366 expires december 2027 cvv 123",              "successful"),
    ], "Payment failure — invalid card then retry")


def test_payment_invalid_cvv():
    return run_conversation([
        ("Hi",                                                              "account"),
        ("ACC1001",                                                         "found"),
        ("Nithin Jain",                                                     "date of birth"),
        ("1990-05-14",                                                      "verified"),
        ("pay 500",                                                         "card"),
        ("card 4532 0151 1283 0366 expires december 2027 cvv 999",        "cvv"),
        ("cvv is 123",                                                      "successful"),
    ], "Payment failure — invalid CVV then retry")


def test_payment_invalid_expiry():
    return run_conversation([
        ("Hi",                                                              "account"),
        ("ACC1001",                                                         "found"),
        ("Nithin Jain",                                                     "date of birth"),
        ("1990-05-14",                                                      "verified"),
        ("pay 500",                                                         "card"),
        ("card 4532 0151 1283 0366 expires january 2020 cvv 123",         "expiry"),
        ("expiry december 2027",                                            "successful"),
    ], "Payment failure — expired card then retry")


def test_secondary_factor_exhausted():
    return run_conversation([
        ("Hi",              "account"),
        ("ACC1001",         "found"),
        ("Nithin Jain",     "date of birth"),
        ("1990-01-01",      "do not match"),
        ("9999",            "do not match"),
        ("999999",          "closed"),
    ], "Verification — secondary factor all attempts exhausted")


def test_leap_year_nearby_date():
    return run_conversation([
        ("Hi",              "account"),
        ("ACC1004",         "found"),
        ("Rahul Mehta",     "date of birth"),
        ("28th Feb 1988",   "do not match"),
        ("29th Feb 1988",   "verified"),
        ("pay 1000",        "card"),
        ("4532 0151 1283 0366 expires december 2027 cvv 123", "successful"),
    ], "Edge case — nearby leap year date fails, correct date passes")


def run_all():
    tests = [
        test_happy_path,
        test_happy_path_aadhaar,
        test_happy_path_pincode,
        test_partial_payment,
        test_verification_name_fail_then_pass,
        test_verification_exhausted,
        test_secondary_factor_fail_then_pass,
        test_invalid_account,
        test_zero_balance,
        test_long_name,
        test_amount_exceeds_balance,
        test_card_details_across_turns,
        test_leap_year_dob,
        test_session_closed_after_done,
        test_payment_invalid_card,
        test_payment_invalid_cvv,
        test_payment_invalid_expiry,
        test_secondary_factor_exhausted,
        test_leap_year_nearby_date,
    ]

    all_results = []
    for test_fn in tests:
        try:
            result = test_fn()
            all_results.append(result)
        except Exception as e:
            print(f"\n{test_fn.__name__} — crashed: {str(e)}")
            all_results.append({
                "test": test_fn.__name__,
                "passed": 0,
                "failed": 1,
                "score": 0
            })

    total_passed = sum(r["passed"] for r in all_results)
    total_checks = sum(r["passed"] + r["failed"] for r in all_results)
    overall = round((total_passed / total_checks) * 100, 1) if total_checks > 0 else 0

    print(f"\n\nSummary")
    print(f"-------")
    for r in all_results:
        status = "ok" if r["failed"] == 0 else "fail"
        print(f"  [{status}] {r['test']} — {r['passed']}/{r['passed']+r['failed']}")

    print(f"\n  overall: {total_passed}/{total_checks} checks passed ({overall}%)")


if __name__ == "__main__":
    run_all()
