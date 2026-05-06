import socket
import requests
import threading
import json
from datetime import datetime
from queue import Queue
from colorama import Fore, Style

class SecIntelTool:
    def __init__(self, target):
        print(f"\n{Fore.CYAN}{Style.BRIGHT}--- SCIENTIFIC PROJECT ---{Style.RESET_ALL}")
        self.target = target
        self.ip = self.resolve_target()
        self.lock = threading.Lock()

        self.report = {
            "timestamp": datetime.now().isoformat(),
            "target": self.target,
            "ip": self.ip,
            "vulnerabilities": [],
            "open_ports": []
        }

    def resolve_target(self):
        try:
            return socket.gethostbyname(self.target)
        except socket.gaierror:
            print(f"{Fore.RED}[-] Failed to resolve host: {self.target}{Style.RESET_ALL}")
            return None

    def audit_http_headers(self):
        print(f"{Fore.GREEN}[+] Analyzing HTTP headers for: {Fore.WHITE}{self.target}{Style.RESET_ALL}")

        security_headers = [
            "Content-Security-Policy",
            "X-Frame-Options",
            "X-Content-Type-Options",
            "Strict-Transport-Security",
            "Permissions-Policy"
        ]
        
        try:
            response = requests.get(f"https://{self.target}", timeout=5)
            headers = response.headers
            
            for header in security_headers:
                if header in headers:
                    pass

                else:
                    issue = f"Missing security header: {header}"
                    self.report["vulnerabilities"].append({"level": "Medium", "issue": issue})
                    print(f"{Fore.YELLOW}{Style.BRIGHT}[!] DETECTED: {Fore.WHITE}{issue}{Style.RESET_ALL}")

        except Exception as e:
            print(f"  [-] Error during HTTP analysis: {e}")

    def service_fingerprint(self, port):
        try:
            s = socket.socket()
            s.settimeout(1)
            s.connect((self.ip, port))
            s.send(b'\r\n')
            banner = s.recv(1024).decode().strip()

            if banner:
                return banner
            else:
                return "Service unrecognized"
            
        except:
            return "Service unrecognized"

    def scan_port(self, port):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            result = s.connect_ex((self.ip, port))

            if result == 0:
                service = self.service_fingerprint(port)

                with self.lock:
                    print(f"{Fore.BLUE}[*] Port {port} OPEN {Fore.WHITE}| Service: {service[:50]}{Style.RESET_ALL}")
                    self.report["open_ports"].append({"port": port, "banner": service})

            else:
                pass

            s.close()

        except:
            pass

    def thread_worker(self, queue):
        while not queue.empty():
            try:
                port = queue.get_nowait()
                self.scan_port(port)
                queue.task_done()
            except:
                break

    def run_multi_scan(self, port_list):
        print(f"\n{Fore.GREEN}[+] Starting multi-threaded port scan on {Fore.CYAN}{self.ip}{Fore.GREEN}...{Style.RESET_ALL}")
        queue = Queue()

        for port in port_list:
            queue.put(port)

        threads = []

        for _ in range(10):
            t = threading.Thread(target=self.thread_worker, args=(queue,))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

    def generate_report(self):
        filename = f"report_{self.target}_{datetime.now().strftime('%Y%m%d')}.json"

        try:
            with open(filename, "w") as f:
                json.dump(self.report, f, indent=4)

            print(f"\n{Fore.GREEN}[+] Audit complete. Report saved to: {Fore.YELLOW}{filename}{Style.RESET_ALL}\n")

        except Exception as e:
            print(f"[-] Failed to save report: {e}")

if __name__ == "__main__":
    target_host = input(f"\n{Fore.WHITE}{Style.BRIGHT}Enter target hostname or IP: www.{Style.RESET_ALL}")
    
    scanner = SecIntelTool(target_host)

    if scanner.ip:
        print(f"{Fore.MAGENTA}{Style.BRIGHT}--- SECURITY AUDIT PRO v1.0 ---{Style.RESET_ALL}\n")
        scanner.audit_http_headers()
        
        common_ports = [21, 22, 23, 25, 53, 80, 110, 443, 445, 3306, 8080]
        scanner.run_multi_scan(common_ports)
        
        scanner.generate_report()

    else:
        print(f"{Fore.RED}[-] Target resolution failed. Exiting!{Style.RESET_ALL}\n")