# checks.py

import re
import subprocess


def canonicalize_kubectl(cmd: str) -> str:
    """
    Convert standalone 'k' => 'kubectl'.
    Example: "k get pods" => "kubectl get pods"
    """
    return re.sub(r"\bk\b", "kubectl", cmd)


def run_help_command(cmd: str):
    """
    Run '--help' commands (kubectl/kubeadm/apt-get/systemctl, etc.) with no timeout.
    Show output, don't store in final answer.
    """
    tokens = cmd.strip().split()
    print(f"\n[Running help command]: {cmd}\n{'-'*40}")
    try:
        result = subprocess.run(tokens, capture_output=True, text=True)
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        print(f"Exit code: {result.returncode}\n{'-'*40}\n")
    except FileNotFoundError:
        print("[ERROR] Command not found or not in PATH.\n")
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}\n")


def syntax_check_cli(cmd: str, timeout_secs: int = 2) -> bool:
    """
    Run the command with a short timeout to detect syntax/usage errors.
    If it times out => assume it's correct enough (avoid indefinite hangs).
    If it returns non-zero => it's a syntax/usage error.

    For kubectl 'create'/'delete', we insert '--dry-run=client' and '-o yaml'.
    You could similarly add logic for 'apt-get' or 'systemctl' if you want specific flags.
    """
    tokens = cmd.strip().split()
    lower_cmd = cmd.lower()

    # Insert additional logic for known subcommands if desired
    # e.g. for "apt-get install" we could do a certain approach...
    if lower_cmd.startswith("kubectl "):
        # If it's "create" or "delete", add a dry-run
        if len(tokens) >= 2 and tokens[1] in ["create", "delete"]:
            if not any(t.startswith("--dry-run") for t in tokens):
                tokens.insert(2, "--dry-run=client")
            if not any(t in ["-o", "--output"] for t in tokens):
                tokens.insert(3, "-o")
                tokens.insert(4, "yaml")

    print(f"\n[Syntax-checking]: {' '.join(tokens)}")
    try:
        result = subprocess.run(
            tokens, capture_output=True, text=True, timeout=timeout_secs
        )
        if result.returncode != 0:
            # Non-zero => some error from the command
            print("STDOUT:\n", result.stdout)
            print("STDERR:\n", result.stderr)
            print(f"[ERROR] Command exited with code {result.returncode}\n")
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


def get_user_commands_with_syntax_check() -> list:
    """
    Prompt user for multi-line commands.
      - If line has '--help', run it immediately (no storing).
      - If line starts with recognized commands (kubectl, kubeadm, apt-get, systemctl, bash), do short-timeout syntax check.
      - Otherwise, skip syntax check.
      - If error, let user re-enter or keep it anyway.
    """
    validated_commands = []
    print(
        "Enter your commands below (one per line). Press Enter on a blank line to finish.\n"
    )

    while True:
        line = input("> ").strip()
        if not line:
            # blank line => done
            break

        # Convert 'k' => 'kubectl'
        line = canonicalize_kubectl(line)
        lower_line = line.lower()

        # Check if user wants help
        if "--help" in lower_line:
            run_help_command(line)
            continue

        # Decide if we syntax-check. List all recognized "bash" commands:
        recognized_cmds = ("kubectl ", "kubeadm ", "apt-get ", "systemctl ", "bash ")
        if any(lower_line.startswith(cmd) for cmd in recognized_cmds):
            # Attempt short-timeout check
            is_ok = syntax_check_cli(line)
            if not is_ok:
                print("It seems there's a syntax or usage error.\n")
                retry = input("Would you like to re-enter this command? (y/n) ").lower()
                if retry.startswith("y"):
                    continue
                else:
                    validated_commands.append(line)
            else:
                validated_commands.append(line)
        else:
            # Not recognized => skip syntax check
            validated_commands.append(line)

    return validated_commands


def check_against_checklist(final_answer: str, checklist: list):
    """
    Compare final answer to the question's checklist. Return (found, missing).
    Naive substring matching, case-insensitive.
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
    For question #10, show partial mocks if user forgot certain pipes.
    """
    user_lower = user_answer.lower()
    if "kubectl get nodes" in user_lower and "grep -i ready" not in user_lower:
        print("[MOCK] You forgot '| grep -i ready'. So you'd see:\n")
        print("NAME         STATUS     ROLES    AGE   VERSION")
        print("k8s-master   Ready      master   12d   v1.19.0")
        print("wk8s-node-0  NotReady   <none>   11d   v1.19.0")
        print("...\n")

    if (
        "kubectl describe nodes" in user_lower
        and "grep -i noschedule" not in user_lower
    ):
        print("[MOCK] You forgot '| grep -i noSchedule'. Taints might be:\n")
        print("Taints: node-role.kubernetes.io/master:NoSchedule\n")
