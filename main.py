import os
import sys
import subprocess
import time
import random
import string
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.console import Group

console = Console()

class AnonManager:
    def __init__(self):
        # Configuration file paths
        self.unbound_conf = "/etc/unbound/unbound.conf"
        self.nm_mac_conf = "/etc/NetworkManager/conf.d/00-macrandomize.conf"
        self.nm_dns_conf = "/etc/NetworkManager/conf.d/10-dns-resolved.conf"
        self.resolved_conf = "/etc/systemd/resolved.conf"
        self.resolv_conf = "/etc/resolv.conf"
        
        # Change hostname on startup
        self.change_hostname_randomly()

        # Module definitions: Menu ID -> (Display Name, Function)
        self.modules = {
            "1": ("Enable/Disable Local Protection (DNS + MAC + Resolved)", self.toggle_protection),
            "2": ("Manage Tor", self.manage_tor),
            "3": ("Manage I2P (i2pd)", self.manage_i2p),
            "4": ("Flush DNS Cache (Unbound)", self.flush_dns_cache),
            
            "5": ("Manage Firewall (Iptables)", self.manage_firewall),
            "6": ("Change System Time (Clock)", self.change_system_time),            
            "7": ("SECURITY MONITORING & AUDIT", self.run_security_audit),

            "0": ("Exit", sys.exit)
        }

    def set_file_immutable(self, path, lock=True):
        """Sets or removes the immutable flag on a file"""
        try:
            flag = "+i" if lock else "-i"
            subprocess.run(["chattr", flag, path], capture_output=True)
        except:
            pass

    def get_tor_user(self):
        """Identifies the Tor user dynamically across different OS distributions"""
        for user in ["debian-tor", "tor", "tor-daemon"]:
            check = subprocess.run(["id", "-u", user], capture_output=True, text=True)
            if check.returncode == 0:
                return user
        return None

    def change_hostname_randomly(self):
        """Generates and applies a random professional-looking hostname"""
        prefix = random.choice(["LAPTOP", "DESKTOP", "HOME-PC", "USER-PC", "PC"])
        suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))
        new_hostname = f"{prefix}-{suffix}"
        try:
            subprocess.run(["hostnamectl", "set-hostname", new_hostname], check=True)
            self.current_hostname = new_hostname
        except:
            self.current_hostname = "DESKTOP-GENERIC"

    def get_service_status(self, service_name):
        """Checks if a systemd service is currently active"""
        try:
            result = subprocess.run(['systemctl', 'is-active', service_name], capture_output=True, text=True)
            if result.stdout.strip() == "active":
                return "[bold green]ONLINE[/bold green]"
            return "[bold red]OFFLINE[/bold red]"
        except:
            return "[grey]NOT FOUND[/grey]"

    def banner(self):
            """Displays the main system banner and service statuses"""
            console.clear()
            # Main Welcome Panel
            console.print(Panel.fit(
                f"[bold magenta]⚡ SAVVA STEALTH SYSTEM ⚡[/bold magenta]\n"
                f"[white]Authorized User: Savva | Hostname: {self.current_hostname}[/white]",
                border_style="magenta"
            ))
            
            # Service Status Table
            table = Table(show_header=True, header_style="bold magenta", box=None)
            table.add_column("Service", style="cyan")
            table.add_column("Status")
            
            table.add_row("Unbound DNS", self.get_service_status("unbound"))
            table.add_row("NetworkManager", self.get_service_status("NetworkManager"))
            table.add_row("Tor Daemon", self.get_service_status("tor"))
            
            console.print(table)
            console.print("[magenta]" + "━" * 45 + "[/magenta]") # System-themed separator

    def toggle_protection(self):
        """Menu for activating local DNS and MAC randomization layers"""
        console.print("\n[bold yellow]--- Local Protection Setup ---[/bold yellow]")
        choice = Prompt.ask("Activate hardened DNS and MAC protection?", choices=["y", "n"], default="y")
        if choice == "y":
            self.apply_hardened_configs()
        else:
            console.print("[red]Operation cancelled.[/red]")

    def apply_hardened_configs(self):
        """Applies privacy-focused configurations to Unbound and NetworkManager"""
        unbound_content = """
# SAVVA STEALTH SYSTEM - DNS CORE CONFIG
# Security Lead: Savva

server:
    num-threads: 4 
    interface: 127.0.0.1
    port: 53
    do-ip4: yes
    do-udp: yes
    do-tcp: yes
    root-hints: "/etc/unbound/root.hints"
    auto-trust-anchor-file: "/etc/unbound/getroot.key"
    tls-cert-bundle: "/etc/ssl/certs/ca-certificates.crt"
    msg-cache-size: 32m
    rrset-cache-size: 64m
    do-daemonize: yes
    verbosity: 0
    use-syslog: no
    log-queries: no
    log-replies: no
    harden-glue: yes
    harden-dnssec-stripped: yes
    use-caps-for-id: yes 
    hide-identity: yes
    hide-version: yes
    qname-minimisation: yes
    prefetch: yes
    rrset-roundrobin: yes
    access-control: 127.0.0.1 allow
    do-not-query-localhost: no

    local-zone: "onion." nodefault
    domain-insecure: "onion."
    private-domain: "onion."
    do-not-query-localhost: no

forward-zone:
    name: "."
    forward-tls-upstream: yes
    forward-addr: 1.1.1.1@853#cloudflare-dns.com
    forward-addr: 9.9.9.9@853#dns.quad9.net

forward-zone:
    name: "onion."
    forward-addr: 127.0.0.1@9053

forward-zone:
    name: "i2p."
    forward-addr: 127.0.0.1@4444
"""
        nm_mac_content = """
# SAVVA STEALTH SYSTEM - L2 PRIVACY LAYER
# Created by Savva | Anti-tracking & MAC Randomization
[device-mac-randomization]
wifi.scan-rand-mac-address=yes
[connection]
wifi.cloned-mac-address=random
ethernet.cloned-mac-address=random
connection.stable-id=${CONNECTION}/${BOOT}
ipv4.dhcp-send-hostname=false
ipv6.dhcp-send-hostname=false
ipv4.dhcp-client-id=mac
ipv6.dhcp-duid=ll
[ipv6]
ip6-privacy=2
"""
        nm_dns_content = """[main]
dns=none
systemd-resolved=false
"""
        try:
            console.print("[blue]Writing configurations...[/blue]")
            os.makedirs("/etc/NetworkManager/conf.d", exist_ok=True)
            self.set_file_immutable(self.resolv_conf, False)
            
            if os.path.islink(self.resolv_conf):
                os.remove(self.resolv_conf)

            with open(self.unbound_conf, 'w') as f: f.write(unbound_content)
            with open(self.nm_mac_conf, 'w') as f: f.write(nm_mac_content)
            with open(self.nm_dns_conf, 'w') as f: f.write(nm_dns_content)
            
            with open(self.resolv_conf, 'w') as f:
                f.write("# SAVVA STEALTH PROTECTED\nnameserver 127.0.0.1\noptions edns0 trust-ad\n")

            self.set_file_immutable(self.resolv_conf, True)

            console.print("[blue]Restarting services...[/blue]")
            os.system("systemctl stop systemd-resolved && systemctl disable systemd-resolved")
            os.system("systemctl restart unbound NetworkManager")

            console.print("[blue]Applying network filters...[/blue]")
            self.setup_firewall()

            # Universal IPv6 Disable
            if os.path.exists("/proc/sys/net/ipv6"):
                console.print("[blue]Disabling IPv6 in kernel...[/blue]")
                os.system("sysctl -w net.ipv6.conf.all.disable_ipv6=1 >/dev/null")
                os.system("sysctl -w net.ipv6.conf.default.disable_ipv6=1 >/dev/null")
                os.system("ip -6 route flush all 2>/dev/null")
            else:
                console.print("[green]IPv6 is already completely removed from system.[/green]")

            console.print("[bold green]✔ Full DNS and MAC isolation activated![/bold green]")
        except Exception as e:
            console.print(f"[bold red]✘ Error: {e}[/bold red]")
        
        Prompt.ask("\nPress Enter to continue")

    def run_security_audit(self):
            """Starts a real-time security dashboard monitoring connections and leaks"""
            from rich.layout import Layout
            
            # Fix monitor height to prevent layout flickering
            ROWS_LIMIT = 10 

            def generate_audit_content():
                # 1. CORE GUARD TABLE (Top)
                status_table = Table(show_header=True, header_style="bold magenta", box=None, padding=(0, 2))
                status_table.add_column("Parameter", width=20)
                status_table.add_column("Status", justify="center", width=15)
                status_table.add_column("Details")

                # IPv6 Leak Check
                v6_check = subprocess.getoutput("ip -6 addr").strip()
                v6_status = "[bold green]DISABLED[/bold green]" if not v6_check else "[bold red]LEAK DETECTED![/bold red]"
                status_table.add_row("IPv6 Protection", v6_status, "Kernel-level block")

                # Firewall & Kill-Switch Check
                fw_active = "DROP" in subprocess.getoutput("iptables -L OUTPUT -n | head -n 1")
                status_table.add_row("Firewall Logic", "[green]ENFORCED[/green]" if fw_active else "[red]OFF[/red]", "Kill-switch status")
                
                # Active Anonymity Networks
                active_nets = []
                if subprocess.run("pgrep -x tor", shell=True, capture_output=True).returncode == 0: active_nets.append("Tor")
                if subprocess.run("pgrep -x i2pd", shell=True, capture_output=True).returncode == 0: active_nets.append("I2P")
                status_table.add_row("Active Networks", ", ".join(active_nets) if active_nets else "None", "Service daemons")

                # 2. NETWORK MONITOR (Bottom)
                conn_table = Table(show_header=True, header_style="bold blue", box=None, padding=(0, 2))
                conn_table.add_column("Proto", width=6)
                conn_table.add_column("Remote IP", width=30)
                conn_table.add_column("Process", style="green")

                raw_conns = subprocess.getoutput("ss -tunap | grep ESTAB | grep -v '127.0.0.1'").split('\n')
                conns = [c for c in raw_conns if c.strip()]
                
                for c in conns[:ROWS_LIMIT]:
                    p = c.split()
                    if len(p) >= 6:
                        proc = p[-1].split('"')[1] if '"' in p[-1] else "Unknown"
                        conn_table.add_row(p[0], p[5], proc)
                
                # Maintain consistent panel height with empty rows
                for _ in range(ROWS_LIMIT - len(conns[:ROWS_LIMIT])):
                    conn_table.add_row("", "", "")

                return Group(
                    Panel(status_table, title="[bold cyan] CORE GUARD [/bold cyan]", border_style="cyan", padding=(0, 1)),
                    Panel(conn_table, title=f"[bold blue] NETWORK MONITOR ({len(conns)})[/bold blue]", border_style="blue", padding=(0, 1)),
                    "[dim] Exit: Ctrl+C | Savva Edition v1.0 [/dim]"
                    ) 

            console.clear()
            try:
                # Use Live rendering for the dashboard
                with Live(generate_audit_content(), refresh_per_second=1, transient=True) as live:
                    while True:
                        live.update(generate_audit_content())
                        time.sleep(1)
            except KeyboardInterrupt:
                console.clear()

    def setup_firewall(self):
        """Configures iptables rules for the stealth kill-switch"""
        try:
            os.system("iptables -F && iptables -X")
            os.system("iptables -P INPUT DROP")
            os.system("iptables -A INPUT -i lo -j ACCEPT")
            os.system("iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT")

            os.system("iptables -P OUTPUT DROP")
            os.system("iptables -A OUTPUT -o lo -j ACCEPT")
            os.system("iptables -A OUTPUT -m state --state ESTABLISHED,RELATED -j ACCEPT")
            
            # Allow DNS queries from Unbound user
            os.system("iptables -A OUTPUT -p tcp --dport 853 -m owner --uid-owner unbound -j ACCEPT")
            os.system("iptables -A OUTPUT -p udp --dport 53 -m owner --uid-owner unbound -j ACCEPT")
            
            t_user = self.get_tor_user()
            if t_user:
                os.system(f"iptables -A OUTPUT -m owner --uid-owner {t_user} -j ACCEPT")
            
            # Standard Web traffic rules
            os.system("iptables -A OUTPUT -p tcp --dport 80 -j ACCEPT")
            os.system("iptables -A OUTPUT -p tcp --dport 443 -j ACCEPT")
            
            console.print(f"[bold green]✔ Firewall configured (Tor User: {t_user or 'None'}).[/bold green]")
        except Exception as e:
            console.print(f"[red]Firewall Error: {e}[/red]")

    def manage_tor(self):
        """Stub for Tor daemon management logic"""
        console.print("[yellow]Tor management function called.[/yellow]")
        pass

    def manage_firewall(self):
            """Menu for toggling between stealth and open firewall modes"""
            console.print("\n[bold yellow]--- 🛡 Firewall Management (Iptables) ---[/bold yellow]")
            console.print(Panel(
                "[1] [bold green]Stealth Mode[/bold green] (INPUT DROP + Kill-Switch)\n"
                "[2] [bold red]Open Mode[/bold red] (ACCEPT ALL + Flush Rules)\n"
                "[0] Back",
                title="Firewall Control Center",
                border_style="yellow"
            ))
            
            choice = Prompt.ask("Selection", choices=["1", "2", "0"])
            
            if choice == "1":
                with console.status("[bold cyan]Applying hardened rules...[/bold cyan]"):
                    self.setup_firewall()
                console.print("[bold green]✔ System in Stealth Mode. Incoming connections blocked.[/bold green]")
                
            elif choice == "2":
                with console.status("[bold red]Resetting security layers...[/bold red]"):
                    try:
                        # Reset default policies to ACCEPT
                        os.system("iptables -P INPUT ACCEPT")
                        os.system("iptables -P FORWARD ACCEPT")
                        os.system("iptables -P OUTPUT ACCEPT")
                        
                        # Flush all tables
                        os.system("iptables -F")
                        os.system("iptables -X")
                        os.system("iptables -t nat -F")
                        os.system("iptables -t nat -X")
                        os.system("iptables -t mangle -F")
                        os.system("iptables -t mangle -X")
                        
                        console.print("[bold red]⚠ Firewall fully open. Stealth mode disabled![/bold red]")
                    except Exception as e:
                        console.print(f"[red]Reset Error: {e}[/red]")
            
            elif choice == "0":
                return

            time.sleep(1.5)

    def change_system_time(self):
            """Allows manual shifting of system clock and disables NTP to prevent fingerprinting"""
            console.print("\n[bold yellow]--- 🕒 Manual Time Correction ---[/bold yellow]")
            
            # Display current time for reference
            current_t = subprocess.getoutput("date +%H:%M")
            console.print(f"Current system time: [bold cyan]{current_t}[/bold cyan]")
            
            new_hours = Prompt.ask("Enter ONLY the hours (00-23)")
            
            if not new_hours.isdigit() or not (0 <= int(new_hours) <= 23):
                console.print("[bold red]✘ Error: Please enter a number between 0 and 23![/bold red]")
                time.sleep(1)
                return

            try:
                # 1. Disable NTP to prevent the system from auto-reverting time
                os.system("timedatectl set-ntp false 2>/dev/null")
                
                # 2. Get current minutes and date to keep them synced
                current_date_min = subprocess.getoutput("date +%M:%S")
                
                # 3. Apply the new time
                full_time = f"{new_hours.zfill(2)}:{current_date_min}"
                subprocess.run(["date", "+%T", "-s", full_time], check=True)
                
                # 4. Sync to Hardware Clock (BIOS/RTC)
                os.system("hwclock --systohc")
                
                console.print(f"[bold green]✔ Time successfully changed to {full_time}[/bold green]")
                console.print("[dim]NTP synchronization disabled to preserve settings.[/dim]")
                
            except Exception as e:
                console.print(f"[bold red]✘ Failed to change time: {e}[/bold red]")
            
            time.sleep(2)

    def manage_i2p(self):
        """Stub for I2P daemon management"""
        pass

    def flush_dns_cache(self):
        """Clears memory caches and restarts the local resolver"""
        os.system("sync; echo 3 > /proc/sys/vm/drop_caches")
        os.system("systemctl restart unbound")

    def run(self):
        """Main application loop"""
        while True:
            self.banner()
            for key, (name, _) in self.modules.items():
                console.print(f"[bold white]{key}[/bold white]: {name}")
            choice = Prompt.ask("\nSelection", choices=list(self.modules.keys()))
            self.modules[choice][1]()

if __name__ == "__main__":
    # Check for root privileges
    if os.getuid() != 0:
        console.print("[red]Critical Error: Run as root (sudo)! [/red]")
        sys.exit(1)
    app = AnonManager()
    app.run()