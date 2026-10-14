
from flask import Flask, render_template, request, jsonify
import platform
import socket
import subprocess

app = Flask(__name__)


def get_device_info():
    hostname = socket.gethostname()

    try:
        local_ip = socket.gethostbyname(hostname)
    except OSError:
        local_ip = "Unavailable"

    return {
        "Hostname": hostname,
        "Operating System": platform.platform(),
        "System": platform.system(),
        "Python Version": platform.python_version(),
        "Local IP Address": local_ip
    }


def valid_host(host):
    return (
        isinstance(host, str)
        and 0 < len(host) <= 253
        and not any(char.isspace() for char in host)
        and not host.startswith("-")
    )


def ping_host(host):
    if not valid_host(host):
        return False, "Enter a valid hostname or IP address."

    if platform.system() == "Windows":
        command = ["ping", "-n", "4", "-w", "2000", host]
    else:
        command = ["ping", "-c", "4", "-W", "2", host]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=12,
            check=False
        )

        output = result.stdout or result.stderr or "No output returned."
        return result.returncode == 0, output.strip()

    except subprocess.TimeoutExpired:
        return False, "Ping timed out."
    except FileNotFoundError:
        return False, "Ping utility is unavailable."
    except OSError as error:
        return False, str(error)


def dns_lookup(host):
    if not valid_host(host):
        return False, "Enter a valid hostname."

    try:
        records = socket.getaddrinfo(host, None)
        addresses = sorted({record[4][0] for record in records})

        if not addresses:
            return False, "No IP addresses found."

        return True, "\n".join(addresses)

    except (socket.gaierror, OSError):
        return False, "DNS lookup failed. Check the hostname and network."


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/diagnose", methods=["POST"])
def diagnose():
    data = request.get_json(silent=True) or {}
    action = str(data.get("action", "")).lower()
    host = str(data.get("host", "")).strip()

    if action == "device":
        return jsonify({
            "success": True,
            "title": "Device Information",
            "result": get_device_info()
        })

    if action == "ping":
        success, result = ping_host(host)
        return jsonify({
            "success": success,
            "title": f"Ping Test: {host}",
            "result": result
        })

    if action == "dns":
        success, result = dns_lookup(host)
        return jsonify({
            "success": success,
            "title": f"DNS Lookup: {host}",
            "result": result
        })

    if action == "all":
        device = get_device_info()

        if not host:
            return jsonify({
                "success": True,
                "title": "All Diagnostics",
                "result": {
                    "device": device,
                    "ping": {
                        "success": False,
                        "message": "Enter a hostname to run ping."
                    },
                    "dns": {
                        "success": False,
                        "message": "Enter a hostname to run DNS lookup."
                    }
                }
            })

        ping_success, ping_result = ping_host(host)
        dns_success, dns_result = dns_lookup(host)

        return jsonify({
            "success": True,
            "title": "All Diagnostics",
            "result": {
                "device": device,
                "ping": {
                    "success": ping_success,
                    "message": ping_result
                },
                "dns": {
                    "success": dns_success,
                    "message": dns_result
                }
            }
        })

    return jsonify({
        "success": False,
        "title": "Invalid Request",
        "result": "Choose a valid diagnostic option."
    }), 400


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
