#!/usr/bin/env python3
"""
Start all Python microservices and display their logs in a unified view
"""
import subprocess
import threading
import time
import sys
from pathlib import Path

# ANSI color codes for terminal output
COLORS = {
    'transformation': '\033[92m',  # Green
    'rating': '\033[94m',          # Blue
    'billing': '\033[93m',         # Yellow
    'reset': '\033[0m',            # Reset
    'bold': '\033[1m',             # Bold
}

# Service configurations
SERVICES = [
    {
        'name': 'transformation',
        'port': 3001,
        'path': 'services/transformation',
    },
    {
        'name': 'rating',
        'port': 3002,
        'path': 'services/rating',
    },
    {
        'name': 'billing',
        'port': 3003,
        'path': 'services/billing',
    }
]

processes = []

def colorize(service_name, text):
    """Add color to service output"""
    color = COLORS.get(service_name, COLORS['reset'])
    reset = COLORS['reset']
    bold = COLORS['bold']
    return f"{color}{bold}[{service_name.upper()}]{reset} {text}"

def stream_output(process, service_name):
    """Stream process output with colored service prefix"""
    try:
        for line in iter(process.stdout.readline, b''):
            if line:
                decoded_line = line.decode('utf-8').rstrip()
                print(colorize(service_name, decoded_line))
                sys.stdout.flush()
    except Exception as e:
        print(colorize(service_name, f"Error reading output: {e}"))

def start_service(service):
    """Start a single service and return the process"""
    name = service['name']
    port = service['port']
    path = service['path']

    print(colorize(name, f"Starting on port {port}..."))

    # Build command to activate venv and start uvicorn
    venv_path = Path.cwd() / 'venv' / 'bin' / 'activate'
    service_path = Path.cwd() / path

    cmd = f"source {venv_path} && cd {service_path} && python -m uvicorn main:app --reload --port {port}"

    try:
        process = subprocess.Popen(
            cmd,
            shell=True,
            executable='/bin/bash',
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1
        )

        # Start thread to stream output
        thread = threading.Thread(target=stream_output, args=(process, name))
        thread.daemon = True
        thread.start()

        return process
    except Exception as e:
        print(colorize(name, f"Failed to start: {e}"))
        return None

def main():
    """Main entry point"""
    print(f"\n{COLORS['bold']}{'='*60}{COLORS['reset']}")
    print(f"{COLORS['bold']}  Billing System - Service Launcher{COLORS['reset']}")
    print(f"{COLORS['bold']}{'='*60}{COLORS['reset']}\n")

    # Check if venv exists
    venv_path = Path.cwd() / 'venv'
    if not venv_path.exists():
        print(f"{COLORS['bold']}ERROR:{COLORS['reset']} Virtual environment not found at {venv_path}")
        print("Please run: python3 -m venv venv")
        sys.exit(1)

    # Start all services
    for service in SERVICES:
        process = start_service(service)
        if process:
            processes.append((service['name'], process))
            time.sleep(2)  # Stagger startup

    print(f"\n{COLORS['bold']}{'='*60}{COLORS['reset']}")
    print(f"{COLORS['bold']}  All services started! Press Ctrl+C to stop all services{COLORS['reset']}")
    print(f"{COLORS['bold']}{'='*60}{COLORS['reset']}\n")

    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
            # Check if any process has died
            for name, process in processes:
                if process.poll() is not None:
                    print(colorize(name, f"Process died with exit code {process.returncode}"))
    except KeyboardInterrupt:
        print(f"\n\n{COLORS['bold']}Shutting down services...{COLORS['reset']}")
        for name, process in processes:
            print(colorize(name, "Stopping..."))
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print(colorize(name, "Force killing..."))
                process.kill()
        print(f"{COLORS['bold']}All services stopped.{COLORS['reset']}\n")
        sys.exit(0)

if __name__ == '__main__':
    main()