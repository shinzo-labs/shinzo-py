import subprocess
import sys
import json

def run():
    process = subprocess.Popen(
        [sys.executable, "repro.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Send initialize request
    init_req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "debug", "version": "1.0"}
        }
    }
    
    input_str = json.dumps(init_req) + "\n"
    
    # Wait for metric export (default 60s)
    import time
    time.sleep(70)
    
    try:
        stdout, stderr = process.communicate(input=input_str, timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        stdout, stderr = process.communicate()

    print("--- STDOUT ---")
    print(repr(stdout))
    print("--- STDERR ---")
    print(stderr)

if __name__ == "__main__":
    run()

