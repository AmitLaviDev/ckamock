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


def syntax_check_cli(cmd: str, timeout_secs: int = 2) -> bool:
    """
    Syntax-check commands for kubectl, kubeadm, and bash-like commands.
    Handles pipes and redirects by enabling shell execution.
    """
    # Check if the command includes pipes or redirects
    if "|" in cmd or ">" in cmd:
        # Shell execution to support pipes and redirections
        print(f"[Shell Execution]: {cmd}")
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=timeout_secs
            )
            # Print captured output for visibility
            if result.stdout:
                print(result.stdout.strip())
            if result.stderr:
                print(result.stderr.strip())

            # Check for errors
            if result.returncode != 0:
                return False
            return True
        except subprocess.TimeoutExpired:
            print("[INFO] Command timed out, assuming syntax is correct enough.\n")
            return True
        except FileNotFoundError:
            print("[ERROR] Command not found.\n")
            return False
        except Exception as e:
            print(f"[ERROR] Unexpected error: {e}\n")
            return False

    # Continue normal processing for non-shell commands
    tokens = cmd.strip().split()
    lower_cmd = cmd.lower()

    # Insert --dry-run=client and -o yaml for 'create' or 'delete'
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
        if result.returncode != 0:
            print(result.stderr.strip())
            return False
        return True
    except subprocess.TimeoutExpired:
        print("[INFO] Command timed out, assuming syntax is correct enough.\n")
        return True
    except FileNotFoundError:
        print("[ERROR] Command not found.\n")
        return False
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}\n")
        return False


def get_user_commands_with_syntax_check(question_id=None) -> list:
    """
    Prompt user for multiple commands (one per line). Press Enter on blank line to finish.
    - If line has `--help`, run it immediately, skip storing.
    - For kubectl/kubeadm/bash commands, do syntax check.
    - Handle special cases (e.g., Q10 mock output).
    Return list of validated commands.
    """
    validated_commands = []
    print(
        "Enter commands below (one per line). Press Enter on a blank line to finish.\n"
    )

    while True:
        line = input("> ").strip()
        if not line:  # blank line => done
            break

        # Normalize 'k' => 'kubectl'
        line = canonicalize_kubectl(line)

        # Handle Q10 mock output immediately if needed
        if question_id == "q10":
            special_mock_output_q10(line)

        # Handle help commands
        if "--help" in line:
            run_help_command(line)
            continue

        # Skip syntax checks for etcdctl commands
        if line.startswith("ETCDCTL_API="):
            validated_commands.append(line)
            continue

        # Syntax check for supported CLI commands
        lower_line = line.lower()
        if lower_line.startswith(("kubectl", "kubeadm", "apt-get", "systemctl")):
            is_ok = syntax_check_cli(line)
            if not is_ok:
                print("It seems there's a syntax or usage error.\n")
                retry = input("Would you like to re-enter this command? (y/n) ").lower()
                if retry.startswith("y"):
                    continue
            validated_commands.append(line)
        else:
            # Accept other commands without checks
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

    # Detect piping behavior and split commands
    commands = [cmd.strip() for cmd in user_answer.split("|")]

    # Handle raw 'kubectl get nodes' without pipes
    if "kubectl get nodes" in commands[0] and len(commands) == 1:
        print(
            "[MOCK OUTPUT] You might be missing pipes or filters. Example raw output:\n"
        )
        print("NAME         STATUS     ROLES    AGE   VERSION")
        print("k8s-master   Ready      master   12d   v1.19.0")
        print("wk8s-node-0  NotReady   <none>   11d   v1.19.0\n")

    # Handle pipe with 'grep -i ready'
    elif len(commands) > 1 and "grep -i ready" in commands[1]:
        print("[MOCK OUTPUT] Example filtered output:\n")
        print("NAME         STATUS     ROLES    AGE   VERSION")
        print("k8s-master   Ready      master   12d   v1.19.0\n")

    # Missing 'grep -i ready' but has 'kubectl get nodes'
    elif "kubectl get nodes" in commands[0] and "grep -i ready" not in user_lower:
        print("[MOCK OUTPUT] Missing '| grep -i ready'. Example output:\n")
        print("NAME         STATUS     ROLES    AGE   VERSION")
        print("k8s-master   Ready      master   12d   v1.19.0")
        print("wk8s-node-0  NotReady   <none>   11d   v1.19.0\n")

    # Missing 'grep -i noschedule' after describing nodes
    elif (
        "kubectl describe nodes" in commands[0]
        and "grep -i noschedule" not in user_lower
    ):
        print("[MOCK OUTPUT] Missing '| grep -i noSchedule'. Example taints:\n")
        print("Taints: node-role.kubernetes.io/master:NoSchedule\n")
