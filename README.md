
# K8s Mock Exam with CLI Syntax Checking

A mock exam tool to practice Kubernetes tasks (RBAC, node drain, upgrades) with **real syntax checks** for:

- **Kubernetes CLI**: `kubectl` and `kubeadm`  
- **Bash Commands**: `apt-get`, `systemctl`, `bash` scripts  
- **Partial Mock Outputs**: For missing pipes or filters in certain commands  
- **Persistent History**: Command history across runs using **arrow keys**  
- **Keyboard Shortcuts**: Supports **left/right arrow keys**, **Ctrl+A/E**, and **tab-completion**  

---

## Features

- **Multi-Question Exam**: 17 tasks covering Kubernetes scenarios
- **Command Aliases**: Supports shorthand aliases for commands (e.g., `k` → `kubectl`, `sa` → `serviceaccount`).
- **Syntax Validation**: Short timeout checks for valid flags and arguments  
- **Help Support**: Use commands like `kubectl create --help` to check usage  
- **Error Handling**: Displays real errors if commands fail validation  
- **Persistent History**: Commands persist across runs using **history file**  
- **Keyboard Shortcuts**: Enables Bash-like navigation with **arrow keys** and shortcuts  

---

## Usage

1. **Clone & Run**  

   ```bash
   git clone https://github.com/your-username/your-repo.git
   cd your-repo
   python main.py
   ```

2. **Answer Questions**  
   - Enter one command per line. Press **Enter** on a blank line to finalize.  
   - **Use help commands** anytime (e.g., `kubectl --help`).  

3. **Validate Answers**  
   - Compare answers against references with flags/keywords.  
   - **Mock outputs** shown for commands requiring pipes or filters.  

---

## Notes

- **Safe Mode**: Use a local cluster (`kind`/`minikube`) to avoid modifying real systems.  
- **Timeouts**: Default timeout is **2 seconds** (adjustable in `res/checks.py`).  
- **Persistent History**: Commands are saved in `~/.k8s_mock_exam_history`.  
- **Arrow Key Support**: Navigate left/right like a real CLI.  

---

**Happy Learning Kubernetes!**
