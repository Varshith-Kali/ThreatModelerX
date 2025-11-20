import os
import subprocess
import json
import sys

os.environ["PYTHONIOENCODING"] = "utf-8"

def run_command(command, log_file, cwd=None):
    print(f"Running command: {command}")
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            shell=True
        )
        print("Return Code:", result.returncode)
        
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(f"Command: {command}\n")
            f.write(f"Return Code: {result.returncode}\n")
            f.write("STDOUT:\n")
            f.write(result.stdout)
            f.write("\nSTDERR:\n")
            f.write(result.stderr)
            
        return result.stdout
    except Exception as e:
        print(f"Error running command: {e}")
        return None

def test_semgrep():
    print("\n--- Testing Semgrep ---")
    target_path = os.path.abspath("demo-apps/python-flask")
    if not os.path.exists(target_path):
        print(f"Target path does not exist: {target_path}")
        return

    cmd = f"semgrep scan --config=auto --json {target_path}"
    output = run_command(cmd, "semgrep_debug.log")
    
    if output:
        try:
            data = json.loads(output)
            print(f"Parsed JSON. Findings count: {len(data.get('results', []))}")
        except json.JSONDecodeError:
            print("Failed to parse JSON output")

def test_retire():
    print("\n--- Testing Retire.js ---")
    target_path = os.path.abspath("demo-apps/node-express")
    if not os.path.exists(target_path):
        print(f"Target path does not exist: {target_path}")
        return

    # Note: Retire.js might need 'npm install' first in the target directory if it checks node_modules
    cmd = f"retire --path {target_path} --outputformat json"
    output = run_command(cmd, "retire_debug.log")
    
    if output:
        try:
            data = json.loads(output)
            print(f"Parsed JSON. Findings count: {len(data)}")
            if len(data) > 0:
                print("First finding:", json.dumps(data[0], indent=2))
        except json.JSONDecodeError:
            print("Failed to parse JSON output")

if __name__ == "__main__":
    print("Current Working Directory:", os.getcwd())
    test_semgrep()
    test_retire()
