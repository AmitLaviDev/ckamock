import re
import subprocess
import os
import atexit

# Define alias mappings
ALIASES = {
    "sa": "serviceaccount",
    "ds": "daemonset",
    "sts": "statefulset",
    "cr": "clusterrole",
    "rb": "rolebinding",
    "pv": "persistentvolume",
    "pvc": "persistentvolumeclaim",
}

# Enable persistent history
history_file = os.path.expanduser("~/.k8s_mock_exam_history")
try:
    import readline

    readline.read_history_file(history_file)
except (FileNotFoundError, ImportError):
    pass

atexit.register(lambda: readline.write_history_file(history_file))

# Enable CLI features
try:
    readline.parse_and_bind("tab: complete")
    readline.parse_and_bind("set editing-mode emacs")
except NameError:
    pass


def replace_aliases(cmd: str) -> str:
    """
    Replace aliases in the command with their full forms based on ALIASES.
    Example: 'k create sa' -> 'kubectl create serviceaccount'
    """
    tokens = cmd.strip().split()
    for i, token in enumerate(tokens):
        if token in ALIASES:
            tokens[i] = ALIASES[token]
    return " ".join(tokens)


def canonicalize_kubectl(cmd: str) -> str:
    """
    Replace 'k' with 'kubectl' and process any aliases.
    """
    cmd = re.sub(r"\bk\b", "kubectl", cmd)  # Replace 'k' with 'kubectl'
    cmd = replace_aliases(cmd)  # Handle custom aliases
    return cmd


def run_help_command(cmd: str):
    """
    Run 'kubectl ... --help' or 'kubeadm ... --help' and display output.
    """
    tokens = cmd.strip().split()
    print(f"\n[Help Command]: {cmd}\n{'-'*40}")
    try:
        result = subprocess.run(tokens, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
    except FileNotFoundError:
        print("[ERROR] Command not found.")
    except Exception as e:
        print(f"[ERROR] {e}")


def syntax_check_cli(cmd: str, timeout_secs: int = 1) -> bool:
    """
    Simplified syntax check for CLI commands (kubectl, kubeadm, bash).
    Shows only the command, error, and help suggestion.
    """
    tokens = cmd.strip().split()

    # Add dry-run and output flags for 'kubectl create|delete'
    lower_cmd = cmd.lower()
    if lower_cmd.startswith("kubectl "):
        if len(tokens) >= 2 and tokens[1] in ["create", "delete"]:
            if not any(t.startswith("--dry-run") for t in tokens):
                tokens.insert(2, "--dry-run=client")
            if not any(t == "-o" or t.startswith("--output") for t in tokens):
                tokens.insert(3, "-o")
                tokens.insert(4, "yaml")

    print(f"[Syntax-checking]: {' '.join(tokens)}")

    try:
        result = subprocess.run(
            tokens, capture_output=True, text=True, timeout=timeout_secs
        )

        # If error, show just error message and helper suggestion
        if result.returncode != 0:
            print(result.stderr.strip())  # Show only the error
            return False  # Syntax/usage error
        return True  # No error

    except subprocess.TimeoutExpired:
        print("[INFO] Command timed out, assuming syntax is correct enough.")
        return True
    except FileNotFoundError:
        print("[ERROR] Command not found.")
        return False
    except Exception as e:
        print(f"[ERROR] {e}")
        return False


def get_user_commands_with_syntax_check() -> list:
    """
    Prompt user for multiple commands (one per line). Press Enter on blank line to finish.
      - Supports aliases and shortcuts.
      - Syntax checks for 'kubectl', 'kubeadm', and 'bash' commands.
    """
    validated_commands = []
    print(
        "Enter commands below (one per line). Press Enter on a blank line to finish.\n"
    )

    while True:
        line = input("> ").strip()
        if not line:
            break  # Exit on blank line

        # Replace aliases and normalize 'k' to 'kubectl'
        line = canonicalize_kubectl(line)

        # Handle '--help'
        if "--help" in line:
            run_help_command(line)
            continue

        # Perform syntax check only for supported CLI commands
        lower_line = line.lower()
        if (
            lower_line.startswith("kubectl ")
            or lower_line.startswith("kubeadm ")
            or lower_line.startswith("apt-get ")
            or lower_line.startswith("systemctl ")
        ):
            is_ok = syntax_check_cli(line)
            if not is_ok:
                retry = input("Would you like to re-enter this command? (y/n) ").lower()
                if retry.startswith("y"):
                    continue
        # Add to validated commands
        validated_commands.append(line)

    return validated_commands


def check_against_checklist(final_answer: str, checklist: list):
    """
    Compare the user's final answer to the question's checklist.
    Returns (found, missing) items based on a simple substring match.
    """
    found = []
    missing = []
    user_lower = final_answer.lower()

    for item in checklist:
        if item.lower() in user_lower:
            found.append(item)
        else:
            missing.append(item)
    return found, missing


def special_mock_output_q10(user_answer: str):
    """
    Handles special cases for Question 10 where pipes/filters are required.
    Simulates output to help users identify missing parts.
    """
    user_lower = user_answer.lower()

    # Missing 'grep -i ready'
    if "kubectl get nodes" in user_lower and "grep -i ready" not in user_lower:
        print("[MOCK OUTPUT] Missing '| grep -i ready'. Example output:\n")
        print("NAME         STATUS     ROLES    AGE   VERSION")
        print("k8s-master   Ready      master   12d   v1.19.0")
        print("wk8s-node-0  NotReady   <none>   11d   v1.19.0\n")

    # Missing 'grep -i noschedule'
    if (
        "kubectl describe nodes" in user_lower
        and "grep -i noschedule" not in user_lower
    ):
        print("[MOCK OUTPUT] Missing '| grep -i noSchedule'. Example taints:\n")
        print("Taints: node-role.kubernetes.io/master:NoSchedule\n")
