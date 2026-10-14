import argparse
import platform
import socket
import subprocess
import sys
from datetime import datetime


def resolve_dns(hostname):
    try:
        results = socket.getaddrinfo(hostname, None)
        return {"ok": True, "addresses": sorted({item[4][0] for item in results})}
    except socket.gaierror as exc:
        return {"ok": False, "error": str(exc)}


def ping_host(host, count=4, timeout=2):
    system = platform.system().lower()
    if system == "windows":
        command = ["ping", "-n", str(count), "-w", str(timeout * 1000), host]
    elif system == "darwin":
        command = ["ping", "-c", str(count), "-W", str(timeout * 1000), host]
    else:
        command = ["ping", "-c", str(count), "-W", str(timeout), host]
    try:
        result = subprocess.run(command, capture_output=True, text=True,
                                timeout=max(10, count * (timeout + 1)), check=False)
        return {"ok": result.returncode == 0,
                "output": (result.stdout or result.stderr).strip() or "No output returned."}
    except FileNotFoundError:
        return {"ok": False, "output": "The ping command was not found on this system."}
    except subprocess.TimeoutExpired:
        return {"ok": False, "output": "Ping timed out before the command completed."}


def local_network_info():
    hostname = socket.gethostname()
    local_ip = "Unavailable"
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # UDP connect selects a route; it does not send data to this documentation address.
        sock.connect(("192.0.2.1", 80))
        local_ip = sock.getsockname()[0]
    except OSError:
        try:
            local_ip = socket.gethostbyname(hostname)
        except OSError:
            pass
    finally:
        sock.close()
    return {"hostname": hostname, "local_ip": local_ip,
            "os": f"{platform.system()} {platform.release()}"}


def main():
    parser = argparse.ArgumentParser(description="Basic network diagnostics: device info, DNS, and ping.")
    parser.add_argument("host", nargs="?", default="example.com", help="Hostname or IP to test (default: example.com)")
    parser.add_argument("--info", action="store_true", help="Show local device and IP information")
    parser.add_argument("--dns", action="store_true", help="Resolve the host using DNS")
    parser.add_argument("--ping", action="store_true", help="Run a basic ping test")
    parser.add_argument("--all", action="store_true", help="Run device info, DNS, and ping checks")
    parser.add_argument("--count", type=int, default=4, help="Ping count (1-10; default 4)")
    parser.add_argument("--timeout", type=int, default=2, help="Ping timeout seconds (1-10; default 2)")
    args = parser.parse_args()
    if not (args.info or args.dns or args.ping or args.all):
        parser.print_help()
        print("\nExample: python network_toolkit.py example.com --all")
        return 0
    if not 1 <= args.count <= 10:
        parser.error("--count must be between 1 and 10")
    if not 1 <= args.timeout <= 10:
        parser.error("--timeout must be between 1 and 10")

    print("=" * 62)
    print("NETWORK TROUBLESHOOTING TOOLKIT")
    print("Run time:", datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z"))
    print("=" * 62)
    if args.info or args.all:
        info = local_network_info()
        print("\n[LOCAL DEVICE]")
        print("Hostname :", info["hostname"])
        print("Local IP :", info["local_ip"])
        print("OS       :", info["os"])
    if args.dns or args.all:
        print(f"\n[DNS LOOKUP: {args.host}]")
        result = resolve_dns(args.host)
        if result["ok"]:
            for address in result["addresses"]:
                print(" ", address)
        else:
            print("  Lookup failed:", result["error"])
    if args.ping or args.all:
        print(f"\n[PING TEST: {args.host}]")
        print(ping_host(args.host, args.count, args.timeout)["output"])
    print("\nDiagnostics complete. A failed ping may be caused by DNS, routing, firewall rules, host downtime, or ICMP filtering.")
    print("Only test systems and networks you are authorized to troubleshoot.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
