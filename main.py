from res import *

def main():
    print("Welcome to the K8s Mock Exam with syntax check for kubectl & kubeadm!\n")

    for i, qa in enumerate(Q_AND_A, start=1):
        print(f"Question {i}:")
        print(qa["question"])

        user_cmds = get_user_commands_with_syntax_check()
        final_answer = "\n".join(user_cmds)

        print("\n=== Checking Your Answer ===")
        found, missing = check_against_checklist(final_answer, qa["checklist"])
        if missing:
            print("You might be missing these key parts:")
            for m in missing:
                print(f"  - {m}")
        else:
            print("Looks like you included all the key parts we expect!")

        # If question has special handling (like Q10), run it
        if qa.get("special_handling") == "q10":
            special_mock_output_q10(final_answer)

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
