
from agent import Agent


def main():
    print("Payment Collection Agent")
    print("Type 'quit' or 'exit' to end")
    print()

    agent = Agent()
    opening = agent.next("Hi")
    print(f"Agent: {opening['message']}")
    print()

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSession ended.")
            break

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit"):
            print("Agent: Thank you. Goodbye!")
            break

        response = agent.next(user_input)
        print()
        print(f"Agent: {response['message']}")
        print()

        if agent.state.stage == "done":
            break


if __name__ == "__main__":
    main()
