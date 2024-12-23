from res import *
import readline
import os
import atexit


def main():
    # Enable persistent command history across runs
    history_file = os.path.expanduser("~/.k8s_mock_exam_history")

    # Load history if the file exists
    try:
        readline.read_history_file(history_file)
    except FileNotFoundError:
        pass  # No history file yet, ignore error

    # Save history on exit
    atexit.register(readline.write_history_file, history_file)

    # Enable advanced CLI features like arrow key navigation, shortcuts
    readline.parse_and_bind("tab: complete")  # Tab for auto-completion (if applicable)
    readline.parse_and_bind(
        "set editing-mode emacs"
    )  # Default line editing (bash-like)

    print(
        "Welcome to the K8s Mock Exam with syntax check for kubectl, kubeadm, and bash!"
    )
    print(
        "Type commands one at a time. Press Enter on a blank line to finish each question."
    )

    for i, qa in enumerate(Q_AND_A, start=1):
        print(f"\nQuestion {i}:")
        print(qa["question"])

        # Handle commands for this question (with immediate feedback if needed)
        user_cmds = get_user_commands_with_syntax_check(
            question_id=qa.get("special_handling")
        )
        final_answer = "\n".join(user_cmds)

        print("\n=== Checking Your Answer ===")

        # Compare the user's answers against expected checklist
        found, missing = check_against_checklist(final_answer, qa["checklist"])
        if missing:
            print("You might be missing these key parts:")
            for m in missing:
                print(f"  - {m}")
        else:
            print("Looks like you included all the key parts we expect!")

        # Handle special cases, e.g., Q10 (mock outputs for missing pipes/filters)
        if qa.get("special_handling") == "q10":
            special_mock_output_q10(final_answer)

        # Display reference answer for comparison
        print("\n--- Reference Answer (for comparison) ---")
        print(qa["reference"])

        if qa.get("notes"):
            print("\nNotes:")
            for note in qa["notes"]:
                print(f"  - {note}")

        print("-" * 70, "\n")

    print("All questions done! Good luck with your Kubernetes journey.\n")


if __name__ == "__main__":
    main()
