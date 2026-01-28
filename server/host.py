import subprocess
import json
import sys
import threading

def read_stdout(proc):
    for line in proc.stdout:
        print("SERVER:", line.strip())

proc = subprocess.Popen(
    [
        "uv", "run",
        "--project", "/Users/kyle/Documents/interview/Intelligine-Technologies/weather-mcp-server",
        "python", "server/run_stdio.py"
    ],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1
)

# stdout
threading.Thread(target=read_stdout, args=(proc,), daemon=True).start()


init_msg = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {
            "tools": {}
        },
        "clientInfo": {
            "name": "minimal-host",
            "version": "0.1"
        }
    }
}

proc.stdin.write(json.dumps(init_msg) + "\n")
proc.stdin.flush()


tools_msg = {
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list",
    "params": {}
}

proc.stdin.write(json.dumps(tools_msg) + "\n")
proc.stdin.flush()

# call get_current_weather
call_msg = {
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
        "name": "get_current_weather",
        "arguments": {
            "city": "Tokyo"
        }
    }
}

proc.stdin.write(json.dumps(call_msg) + "\n")
proc.stdin.flush()

input("Press Enter to exit...\n")
proc.terminate()