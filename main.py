#!/usr/bin/env python3

import re
import subprocess
import textwrap

################################################################################
# The Q_AND_A list with 17 questions, references, checklists, etc.
################################################################################
Q_AND_A = [
    {
        "question": textwrap.dedent(
            """\
            1) Create a new ClusterRole named deployment-clusterrole, which only allows creating:
               - Deployment
               - StatefulSet
               - DaemonSet

               Create a new ServiceAccount named cicd-token in the existing namespace app-team1.

               Finally, bind the new ClusterRole to the new ServiceAccount, limited to app-team1.
        """
        ),
        "reference": textwrap.dedent(
            """\
            kubectl create clusterrole deployment-clusterrole --verb=create --resource=deployments,statefulsets,daemonsets
            kubectl create serviceaccount cicd-token --namespace=app-team1
            kubectl create rolebinding deployment-clusterrole \\
              --clusterrole=deployment-clusterrole \\
              --serviceaccount=app-team1:cicd-token \\
              --namespace=app-team1
        """
        ),
        "checklist": [
            "kubectl create clusterrole deployment-clusterrole",
            "--verb=create",
            "--resource=deployments,statefulsets,daemonsets",
            "kubectl create serviceaccount cicd-token",
            "--namespace=app-team1",
            "kubectl create rolebinding",
            "--clusterrole=deployment-clusterrole",
            "--serviceaccount=app-team1:cicd-token",
        ],
        "notes": [
            "Watch out: The original text had '--serviceaccount=default:cicd-token'. The correct approach uses 'app-team1:cicd-token'."
        ],
        "special_handling": None,
    },
    {
        "question": textwrap.dedent(
            """\
            2) Set the node labeled with name=ek8s-node-1 as unavailable
               and reschedule all pods running on it.
        """
        ),
        "reference": textwrap.dedent(
            """\
            kubectl cordon ek8s-node-1
            kubectl drain ek8s-node-1 --delete-emptydir-data --ignore-daemonsets --force
        """
        ),
        "checklist": [
            "kubectl cordon ek8s-node-1",
            "kubectl drain ek8s-node-1",
            "--delete-emptydir-data",
            "--ignore-daemonsets",
            "--force",
        ],
        "notes": [],
        "special_handling": None,
    },
    {
        "question": textwrap.dedent(
            """\
            3) Upgrade an existing cluster (v1.18.8) to v1.19.0 on the master node with name k8s-master:
               - Upgrade all control plane and node components on the master
               - Upgrade kubelet and kubectl on the master node
        """
        ),
        "reference": textwrap.dedent(
            """\
            kubectl cordon k8s-master
            kubectl drain k8s-master --delete-emptydir-data --ignore-daemonsets --force

            apt-get install kubeadm=1.19.0-00 kubelet=1.19.0-00 kubectl=1.19.0-00 --disableexcludes=kubernetes
            kubeadm upgrade apply 1.19.0 --etcd-upgrade=false

            systemctl daemon-reload
            systemctl restart kubelet

            kubectl uncordon k8s-master
        """
        ),
        "checklist": [
            "kubectl cordon k8s-master",
            "kubectl drain k8s-master",
            "apt-get install kubeadm=1.19.0-00 kubelet=1.19.0-00 kubectl=1.19.0-00",
            "kubeadm upgrade apply 1.19.0",
            "systemctl restart kubelet",
            "kubectl uncordon k8s-master",
        ],
        "notes": [
            "In some distros, you might use yum or dnf. The concept is the same: upgrade these packages, then run kubeadm upgrade."
        ],
        "special_handling": None,
    },
    {
        "question": textwrap.dedent(
            """\
            4) Create a snapshot of the etcd instance at https://127.0.0.1:2379
               saving it to /srv/data/etcd-snapshot.db.

               Restore from /var/lib/backup/etcd-snapshot-previous.db

               TLS cert/key in /opt/KUIN00601/...
        """
        ),
        "reference": textwrap.dedent(
            """\
            ETCDCTL_API=3 etcdctl --endpoints="https://127.0.0.1:2379" \\
                --cacert=/opt/KUIN00601/ca.crt \\
                --cert=/opt/KUIN00601/etcd-client.crt \\
                --key=/opt/KUIN00601/etcd-client.key snapshot save /srv/data/etcd-snapshot.db

            ETCDCTL_API=3 etcdctl --endpoints="https://127.0.0.1:2379" \\
                --cacert=/opt/KUIN00601/ca.crt \\
                --cert=/opt/KUIN00601/etcd-client.crt \\
                --key=/opt/KUIN00601/etcd-client.key snapshot restore /var/lib/backup/etcd-snapshot-previous.db
        """
        ),
        "checklist": [
            "ETCDCTL_API=3",
            '--endpoints="https://127.0.0.1:2379"',
            "--cacert=/opt/KUIN00601/ca.crt",
            "--cert=/opt/KUIN00601/etcd-client.crt",
            "--key=/opt/KUIN00601/etcd-client.key",
            "snapshot save /srv/data/etcd-snapshot.db",
            "snapshot restore /var/lib/backup/etcd-snapshot-previous.db",
        ],
        "notes": [
            "Original text had mismatches like /etc/data or 'previoys.db'. This corrected version uses /srv/data and 'previous.db'."
        ],
        "special_handling": None,
    },
    {
        "question": textwrap.dedent(
            """\
            5) Create a new NetworkPolicy named allow-port-from-namespace that
               only allows Pods in namespace 'internal' to connect to port 9000
               of other Pods in the same namespace, disallowing all else.
        """
        ),
        "reference": textwrap.dedent(
            """\
            apiVersion: networking.k8s.io/v1
            kind: NetworkPolicy
            metadata:
              name: allow-port-from-namespace
              namespace: internal
            spec:
              podSelector:
                matchLabels: {}
              ingress:
              - from:
                - podSelector: {}    # same namespace
              - ports:
                - port: 9000
        """
        ),
        "checklist": [
            "apiVersion: networking.k8s.io/v1",
            "kind: NetworkPolicy",
            "name: allow-port-from-namespace",
            "namespace: internal",
            "port: 9000",
        ],
        "notes": [
            "We simplified the official answer to highlight same-namespace access. Real usage may differ."
        ],
        "special_handling": None,
    },
    {
        "question": textwrap.dedent(
            """\
            6) Reconfigure the existing deployment 'front-end' to add a port spec
               named 'http' exposing port 80/tcp of the existing container 'nginx'.
               Then create a NodePort service 'front-end-svc' exposing that container port.
        """
        ),
        "reference": textwrap.dedent(
            """\
            # In the Deployment spec:
            spec:
              containers:
              - name: nginx
                image: nginx
                ports:
                - name: http
                  containerPort: 80

            # Then expose it:
            kubectl expose deployment front-end --name=front-end-svc \
              --port=80 --target-port=80 --type=NodePort
        """
        ),
        "checklist": [
            "ports:",
            "name: http",
            "containerPort: 80",
            "kubectl expose deployment front-end",
            "--type=NodePort",
        ],
        "notes": [
            "The official answer originally only had 'kubectl expose', but we also need the container port in the Deployment spec."
        ],
        "special_handling": None,
    },
    {
        "question": textwrap.dedent(
            """\
            7) Create a new nginx Ingress:
               - Name: pong
               - Namespace: ing-internal
               - Expose service 'hi' on path /hi, port 5678
               So that 'curl -kL <INTERNAL_IP>/hi' returns 'hi'
        """
        ),
        "reference": textwrap.dedent(
            """\
            apiVersion: networking.k8s.io/v1
            kind: Ingress
            metadata:
              name: pong
              namespace: ing-internal
              annotations:
                nginx.ingress.kubernetes.io/rewrite-target: /
            spec:
              rules:
              - http:
                  paths:
                  - path: /hi
                    pathType: Prefix
                    backend:
                      service:
                        name: hi
                        port:
                          number: 5678
        """
        ),
        "checklist": [
            "name: pong",
            "namespace: ing-internal",
            "path: /hi",
            "service:",
            "name: hi",
            "port:",
            "number: 5678",
        ],
        "notes": [
            "We corrected the mismatch from 'ping'/'hello' in the original text."
        ],
        "special_handling": None,
    },
    {
        "question": textwrap.dedent(
            """\
            8) Scale the deployment 'loadbalancer' to 6 pods.
        """
        ),
        "reference": "kubectl scale deploy loadbalancer --replicas=6",
        "checklist": [
            "kubectl scale deploy loadbalancer",
            "--replicas=6",
        ],
        "notes": [],
        "special_handling": None,
    },
    {
        "question": textwrap.dedent(
            """\
            9) Schedule a pod:
               - Name: nginx-kusc00401
               - Image: nginx
               - Node selector: disk=spinning
        """
        ),
        "reference": textwrap.dedent(
            """\
            apiVersion: v1
            kind: Pod
            metadata:
              name: nginx-kusc00401
            spec:
              nodeSelector:
                disk: spinning
              containers:
              - name: nginx
                image: nginx
        """
        ),
        "checklist": [
            "name: nginx-kusc00401",
            "nodeSelector:",
            "disk: spinning",
            "image: nginx",
        ],
        "notes": [],
        "special_handling": None,
    },
    {
        "question": textwrap.dedent(
            """\
            10) Check how many nodes are Ready (excluding those tainted NoSchedule),
                then write that number to /opt/nodenum.
                If you forget to pipe or filter, the output might be incomplete or too large.
        """
        ),
        "reference": textwrap.dedent(
            """\
            kubectl get nodes | grep -i ready
            kubectl describe nodes <nodeName> | grep -i taints | grep -i noSchedule
            # Subtract the noSchedule nodes from the total ready nodes, then:
            echo <someNumber> > /opt/nodenum
        """
        ),
        "checklist": [
            "kubectl get nodes",
            "grep -i ready",
            "kubectl describe nodes",
            "grep -i taints",
            "grep -i noSchedule",
            "/opt/nodenum",
        ],
        "notes": ["We can 'mock' partial output if you forget certain pipes."],
        "special_handling": "q10",
    },
    {
        "question": textwrap.dedent(
            """\
            11) Create a pod named kucc1 with containers for images:
                - nginx
                - redis
                - memcached
                - consul
        """
        ),
        "reference": textwrap.dedent(
            """\
            apiVersion: v1
            kind: Pod
            metadata:
              name: kucc1
            spec:
              containers:
              - name: nginx
                image: nginx
              - name: redis
                image: redis
              - name: memcached
                image: memcached
              - name: consul
                image: consul
        """
        ),
        "checklist": [
            "name: kucc1",
            "image: nginx",
            "image: redis",
            "image: memcached",
            "image: consul",
        ],
        "notes": ["Watch out for spelling: it's 'memcached', not 'memchached'!"],
        "special_handling": None,
    },
    {
        "question": textwrap.dedent(
            """\
            12) Create a PersistentVolume named 'app-config' of capacity 1Gi,
                accessMode=ReadWriteOnce, type=hostPath at /srv/app-config
        """
        ),
        "reference": textwrap.dedent(
            """\
            apiVersion: v1
            kind: PersistentVolume
            metadata:
              name: app-config
              labels:
                type: local
            spec:
              capacity:
                storage: 1Gi
              accessModes:
                - ReadWriteOnce
              hostPath:
                path: /srv/app-config
        """
        ),
        "checklist": [
            "name: app-config",
            "storage: 1Gi",
            "ReadWriteOnce",
            "hostPath",
            "/srv/app-config",
        ],
        "notes": [],
        "special_handling": None,
    },
    {
        "question": textwrap.dedent(
            """\
            13) Create a PVC named 'pv-volume' (class=csi-hostpath-sc, capacity=10Mi),
                then create a pod that mounts it at /usr/share/nginx/html.
                Finally, expand the PVC to 70Mi with kubectl edit (and record that change).
        """
        ),
        "reference": textwrap.dedent(
            """\
            apiVersion: v1
            kind: PersistentVolumeClaim
            metadata:
              name: pv-volume
            spec:
              accessModes:
                - ReadWriteOnce
              volumeMode: Filesystem
              resources:
                requests:
                  storage: 10Mi
              storageClassName: csi-hostpath-sc

            ---
            apiVersion: v1
            kind: Pod
            metadata:
              name: web-server
            spec:
              containers:
              - name: nginx
                image: nginx
                volumeMounts:
                - mountPath: "/usr/share/nginx/html"
                  name: pv-volume
              volumes:
              - name: pv-volume
                persistentVolumeClaim:
                  claimName: pv-volume

            # Then:
            kubectl edit pvc pv-volume --save-config  # expand to 70Mi
        """
        ),
        "checklist": [
            "kind: PersistentVolumeClaim",
            "name: pv-volume",
            "storage: 10Mi",
            "storageClassName: csi-hostpath-sc",
            "kind: Pod",
            "name: web-server",
            'mountPath: "/usr/share/nginx/html"',
            "kubectl edit pvc pv-volume",
        ],
        "notes": [],
        "special_handling": None,
    },
    {
        "question": textwrap.dedent(
            """\
            14) Monitor logs of pod foobar, extract lines with 'unable-to-access-website'
                and write them to /opt/KUTR00101/foobar
        """
        ),
        "reference": textwrap.dedent(
            """\
            kubectl logs foobar | grep unable-to-access-website > /opt/KUTR00101/foobar
            cat /opt/KUTR00101/foobar
        """
        ),
        "checklist": [
            "kubectl logs foobar",
            "grep unable-to-access-website",
            "> /opt/KUTR00101/foobar",
        ],
        "notes": [],
        "special_handling": None,
    },
    {
        "question": textwrap.dedent(
            """\
            15) Add a streaming sidecar to an existing Pod legacy-app, which runs:
                /bin/sh -c 'tail -n+1 -f /var/log/legacy-app.log'
                using a shared volumeMount named 'logs'.
                Don't modify the existing container or the log path.
        """
        ),
        "reference": textwrap.dedent(
            """\
            apiVersion: v1
            kind: Pod
            metadata:
              name: legacy-app
            spec:
              containers:
              - name: existing-container
                # ...
                volumeMounts:
                - name: logs
                  mountPath: /var/log

              - name: sidecar
                image: busybox
                command: ["/bin/sh", "-c"]
                args: ["tail -n+1 -f /var/log/legacy-app.log"]
                volumeMounts:
                - name: logs
                  mountPath: /var/log

              volumes:
              - name: logs
                emptyDir: {}
        """
        ),
        "checklist": [
            "name: legacy-app",
            "kind: Pod",
            "tail -n+1 -f /var/log/legacy-app.log",
            "volumeMounts:",
            "emptyDir: {}",
        ],
        "notes": [
            "Original text had a mismatch: 'legacy-ap.log'. Now corrected to 'legacy-app.log'."
        ],
        "special_handling": None,
    },
    {
        "question": textwrap.dedent(
            """\
            16) From pods labeled name=cpu-user, find which pod has the highest CPU usage
                and append that pod name to /opt/KUT00401/KUT00401.txt
        """
        ),
        "reference": textwrap.dedent(
            """\
            kubectl top pod -l name=cpu-user -A
            # Identify the highest CPU usage, then:
            echo <podname> >> /opt/KUT00401/KUT00401.txt
        """
        ),
        "checklist": [
            "kubectl top pod -l name=cpu-user",
            "/opt/KUT00401/KUT00401.txt",
        ],
        "notes": [],
        "special_handling": None,
    },
    {
        "question": textwrap.dedent(
            """\
            17) A worker node wk8s-node-0 is NotReady. Investigate and fix it so it
                becomes Ready, ensuring the fix is permanent.
        """
        ),
        "reference": textwrap.dedent(
            """\
            sudo -i
            systemctl status kubelet
            systemctl start kubelet
            systemctl enable kubelet
        """
        ),
        "checklist": [
            "systemctl start kubelet",
            "systemctl enable kubelet",
        ],
        "notes": [],
        "special_handling": None,
    },
]


################################################################################
# Utility Functions
################################################################################


def canonicalize_kubectl(cmd: str) -> str:
    """
    Replace standalone 'k' with 'kubectl'.
    Example: "k get pods" -> "kubectl get pods"
    """
    return re.sub(r"\bk\b", "kubectl", cmd)


def run_help_command(cmd: str):
    """
    Run 'kubectl ... --help' (no timeout),
    show the output, don't store in final answer.
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
        print("[ERROR] 'kubectl' not found or not in PATH.\n")
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}\n")


def syntax_check_kubectl(cmd: str, timeout_secs: int = 2) -> bool:
    """
    Run the command with a short timeout to catch quick syntax errors.
    If it times out => assume it's correct (avoid hanging).
    If it returns non-zero => it's a syntax/usage error.

    We optionally insert '--dry-run=client' & '-o yaml' if subcommand is 'create'/'delete'.
    """
    tokens = cmd.strip().split()

    # Insert --dry-run=client -o yaml if subcommand is create/delete
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
            print("STDOUT:\n", result.stdout)
            print("STDERR:\n", result.stderr)
            print(f"[ERROR] Command exited with code {result.returncode}\n")
            return False
        return True
    except subprocess.TimeoutExpired:
        print("[INFO] Command timed out, assuming syntax is correct enough.\n")
        return True
    except FileNotFoundError:
        print("[ERROR] 'kubectl' not found.\n")
        return False
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}\n")
        return False


def get_user_commands_with_syntax_check() -> list:
    """
    Prompt user for multiple commands (one per line). Press Enter on blank line to finish.
      - If line has `--help`, run it immediately, skip storing.
      - If line starts with `kubectl` or `k ` (alias -> 'kubectl'), do syntax check.
      - Otherwise, skip syntax check (accept as is).
      - If syntax error, ask if user wants to re-enter or keep.
    Return list of final stored commands.
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

        # Convert 'k ' => 'kubectl '
        line = canonicalize_kubectl(line)

        # If it's a help command, just run and skip
        if "--help" in line:
            run_help_command(line)
            continue

        # If line starts with 'kubectl' (case-insensitive), do syntax check
        lower_line = line.lower()
        if lower_line.startswith("kubectl "):
            is_ok = syntax_check_kubectl(line)
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
            # Not a kubectl command => skip syntax check
            validated_commands.append(line)

    return validated_commands


def check_against_checklist(final_answer: str, checklist: list):
    """
    Compare the user's final answer (all lines in one string) to the question's checklist.
    Return (found, missing). Simple substring matching (case-insensitive).
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
    Example "special handling" for question #10.
    If user forgot 'grep -i ready' or 'grep -i noSchedule', show partial mock.
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


################################################################################
# Main Program
################################################################################


def main():
    print(
        "Welcome to the K8s Mock Exam with partial syntax checking & real '--help'!\n"
    )

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
