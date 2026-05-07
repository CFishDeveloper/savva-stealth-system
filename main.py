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
import time
from rich.live import Live
from rich.layout import Layout
from rich.console import Group

console = Console()

class AnonManager:
    def __init__(self):
        self.unbound_conf = "/etc/unbound/unbound.conf"
        self.nm_mac_conf = "/etc/NetworkManager/conf.d/00-macrandomize.conf"
        self.nm_dns_conf = "/etc/NetworkManager/conf.d/10-dns-resolved.conf"
        self.resolved_conf = "/etc/systemd/resolved.conf"
        self.resolv_conf = "/etc/resolv.conf"
        
        self.change_hostname_randomly()

        self.modules = {
            "1": ("Вкл/Выкл локальную защиту (DNS + MAC + Resolved)", self.toggle_protection),
            "2": ("Управление Tor", self.manage_tor),
            "3": ("Управление I2P (i2pd)", self.manage_i2p),
            "4": ("Очистить DNS кэш (Unbound)", self.flush_dns_cache),
            
            "5": ("Управление Firewall (Iptables)", self.manage_firewall),
            "6": ("Сменить время (Часы)", self.change_system_time),            
            "7": ("МОНИТОРИНГ БЕЗОПАСНОСТИ", self.run_security_audit),

            "0": ("Выход", sys.exit)
        }

    def set_file_immutable(self, path, lock=True):
        try:
            flag = "+i" if lock else "-i"
            subprocess.run(["chattr", flag, path], capture_output=True)
        except:
            pass

    def get_tor_user(self):
        """Определяет пользователя Tor динамически для разных ОС"""
        for user in ["debian-tor", "tor", "tor-daemon"]:
            check = subprocess.run(["id", "-u", user], capture_output=True, text=True)
            if check.returncode == 0:
                return user
        return None

    def change_hostname_randomly(self):
        prefix = random.choice(["LAPTOP", "DESKTOP", "HOME-PC", "USER-PC", "PC"])
        suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))
        new_hostname = f"{prefix}-{suffix}"
        try:
            subprocess.run(["hostnamectl", "set-hostname", new_hostname], check=True)
            self.current_hostname = new_hostname
        except:
            self.current_hostname = "DESKTOP-GENERIC"

    def get_service_status(self, service_name):
        try:
            result = subprocess.run(['systemctl', 'is-active', service_name], capture_output=True, text=True)
            if result.stdout.strip() == "active":
                return "[bold green]ONLINE[/bold green]"
            return "[bold red]OFFLINE[/bold red]"
        except:
            return "[grey]NOT FOUND[/grey]"

    def banner(self):
            console.clear()
            # Основная панель приветствия
            console.print(Panel.fit(
                f"[bold magenta]⚡ SAVVA STEALTH SYSTEM ⚡[/bold magenta]\n"
                f"[white]Authorized User: Savva | Hostname: {self.current_hostname}[/white]",
                border_style="magenta"
            ))
            
            # Таблица статусов сервисов
            table = Table(show_header=True, header_style="bold magenta", box=None)
            table.add_column("Service", style="cyan")
            table.add_column("Status")
            
            table.add_row("Unbound DNS", self.get_service_status("unbound"))
            table.add_row("NetworkManager", self.get_service_status("NetworkManager"))
            table.add_row("Tor Daemon", self.get_service_status("tor"))
            
            console.print(table)
            console.print("[magenta]" + "━" * 45 + "[/magenta]") # Линия в цвет системы

    def toggle_protection(self):
        console.print("\n[bold yellow]--- Настройка локальной защиты ---[/bold yellow]")
        choice = Prompt.ask("Активировать жесткую защиту DNS и MAC?", choices=["y", "n"], default="y")
        if choice == "y":
            self.apply_hardened_configs()
        else:
            console.print("[red]Отмена.[/red]")

    def apply_hardened_configs(self):
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
            console.print("[blue]Запись конфигураций...[/blue]")
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

            console.print("[blue]Перезапуск сервисов...[/blue]")
            os.system("systemctl stop systemd-resolved && systemctl disable systemd-resolved")
            os.system("systemctl restart unbound NetworkManager")

            console.print("[blue]Применение сетевых фильтров...[/blue]")
            self.setup_firewall()

            # Универсальное отключение IPv6
            if os.path.exists("/proc/sys/net/ipv6"):
                console.print("[blue]Отключение IPv6 в ядре...[/blue]")
                os.system("sysctl -w net.ipv6.conf.all.disable_ipv6=1 >/dev/null")
                os.system("sysctl -w net.ipv6.conf.default.disable_ipv6=1 >/dev/null")
                os.system("ip -6 route flush all 2>/dev/null")
            else:
                console.print("[green]IPv6 уже полностью вырезан из системы.[/green]")

            console.print("[bold green]✔ Полная изоляция DNS и MAC активирована![/bold green]")
        except Exception as e:
            console.print(f"[bold red]✘ Ошибка: {e}[/bold red]")
        
        Prompt.ask("\nНажмите Enter")

    def run_security_audit(self):
            from rich.layout import Layout
            
            # Фиксируем высоту монитора, чтобы ничего не прыгало
            ROWS_LIMIT = 10 

            def generate_audit_content():
                # 1. СТАТИЧНАЯ ТАБЛИЦА (Верхняя)
                status_table = Table(show_header=True, header_style="bold magenta", box=None, padding=(0, 2))
                status_table.add_column("Параметр", width=20)
                status_table.add_column("Статус", justify="center", width=15)
                status_table.add_column("Детали")

                # IPv6
                v6_check = subprocess.getoutput("ip -6 addr").strip()
                v6_status = "[bold green]DISABLED[/bold green]" if not v6_check else "[bold red]LEAK![/bold red]"
                status_table.add_row("IPv6 Protection", v6_status, "Kernel-level block")

                # Firewall & Networks
                fw_active = "DROP" in subprocess.getoutput("iptables -L OUTPUT -n | head -n 1")
                status_table.add_row("Firewall Logic", "[green]ENFORCED[/green]" if fw_active else "[red]OFF[/red]", "Kill-switch")
                
                active_nets = []
                if subprocess.run("pgrep -x tor", shell=True, capture_output=True).returncode == 0: active_nets.append("Tor")
                if subprocess.run("pgrep -x i2pd", shell=True, capture_output=True).returncode == 0: active_nets.append("I2P")
                status_table.add_row("Active Networks", ", ".join(active_nets) if active_nets else "None", "Daemons")

                # 2. МОНИТОР СОЕДИНЕНИЙ (Нижняя)
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
                
                # Добиваем пустыми строками, чтобы высота панели была ВСЕГДА одинаковой
                for _ in range(ROWS_LIMIT - len(conns[:ROWS_LIMIT])):
                    conn_table.add_row("", "", "")

                return Group(
                    Panel(status_table, title="[bold cyan] CORE GUARD [/bold cyan]", border_style="cyan", padding=(0, 1)),
                    Panel(conn_table, title=f"[bold blue] NETWORK MONITOR ({len(conns)})[/bold blue]", border_style="blue", padding=(0, 1)),
                    "[dim] Выход: Ctrl+C | Savva Edition v1.0 [/dim]"
                    ) 

            console.clear()
            try:
                # Убрал screen=True, добавил фиксированный рендеринг
                with Live(generate_audit_content(), refresh_per_second=1, transient=True) as live:
                    while True:
                        live.update(generate_audit_content())
                        time.sleep(1)
            except KeyboardInterrupt:
                console.clear()

    def setup_firewall(self):
        try:
            os.system("iptables -F && iptables -X")
            os.system("iptables -P INPUT DROP")
            os.system("iptables -A INPUT -i lo -j ACCEPT")
            os.system("iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT")

            os.system("iptables -P OUTPUT DROP")
            os.system("iptables -A OUTPUT -o lo -j ACCEPT")
            os.system("iptables -A OUTPUT -m state --state ESTABLISHED,RELATED -j ACCEPT")
            
            os.system("iptables -A OUTPUT -p tcp --dport 853 -m owner --uid-owner unbound -j ACCEPT")
            os.system("iptables -A OUTPUT -p udp --dport 53 -m owner --uid-owner unbound -j ACCEPT")
            
            t_user = self.get_tor_user()
            if t_user:
                os.system(f"iptables -A OUTPUT -m owner --uid-owner {t_user} -j ACCEPT")
            
            os.system("iptables -A OUTPUT -p tcp --dport 80 -j ACCEPT")
            os.system("iptables -A OUTPUT -p tcp --dport 443 -j ACCEPT")
            
            console.print(f"[bold green]✔ Firewall настроен (User: {t_user or 'None'}).[/bold green]")
        except Exception as e:
            console.print(f"[red]Firewall Error: {e}[/red]")

    def manage_tor(self):
        # код управления Tor здесь
        console.print("[yellow]Функция управления Tor вызвана.[/yellow]")
        pass

    def manage_firewall(self):
            console.print("\n[bold yellow]--- 🛡 Управление Firewall (Iptables) ---[/bold yellow]")
            console.print(Panel(
                "[1] [bold green]Stealth Mode[/bold green] (INPUT DROP + Kill-Switch)\n"
                "[2] [bold red]Open Mode[/bold red] (ACCEPT ALL + Flush Rules)\n"
                "[0] Назад",
                title="Firewall Control Center",
                border_style="yellow"
            ))
            
            choice = Prompt.ask("Выбор", choices=["1", "2", "0"])
            
            if choice == "1":
                with console.status("[bold cyan]Применение жестких правил...[/bold cyan]"):
                    self.setup_firewall()
                console.print("[bold green]✔ Система в режиме Stealth. Входящие соединения заблокированы.[/bold green]")
                
            elif choice == "2":
                with console.status("[bold red]Сброс защиты...[/bold red]"):
                    try:
                        # Сбрасываем политики в ACCEPT
                        os.system("iptables -P INPUT ACCEPT")
                        os.system("iptables -P FORWARD ACCEPT")
                        os.system("iptables -P OUTPUT ACCEPT")
                        
                        # Очищаем все таблицы
                        os.system("iptables -F")
                        os.system("iptables -X")
                        os.system("iptables -t nat -F")
                        os.system("iptables -t nat -X")
                        os.system("iptables -t mangle -F")
                        os.system("iptables -t mangle -X")
                        
                        console.print("[bold red]⚠ Firewall полностью открыт. Стелс-режим выключен![/bold red]")
                    except Exception as e:
                        console.print(f"[red]Ошибка при сбросе: {e}[/red]")
            
            elif choice == "0":
                return

            time.sleep(1.5)

    def change_system_time(self):
            console.print("\n[bold yellow]--- 🕒 Ручная корректировка времени ---[/bold yellow]")
            
            # Получаем текущее время для справки
            current_t = subprocess.getoutput("date +%H:%M")
            console.print(f"Текущее время в системе: [bold cyan]{current_t}[/bold cyan]")
            
            new_hours = Prompt.ask("Введите только ЧАСЫ (00-23)")
            
            if not new_hours.isdigit() or not (0 <= int(new_hours) <= 23):
                console.print("[bold red]✘ Ошибка: Введите число от 0 до 23![/bold red]")
                time.sleep(1)
                return

            try:
                # 1. Отключаем NTP, чтобы система не откатила время назад
                os.system("timedatectl set-ntp false 2>/dev/null")
                
                # 2. Получаем текущие минуты и дату, чтобы сменить только часы
                current_date_min = subprocess.getoutput("date +%M:%S")
                current_day = subprocess.getoutput("date +%Y-%m-%d")
                
                # 3. Устанавливаем новое время
                # Формат: date + %T -set "10:15:00"
                full_time = f"{new_hours.zfill(2)}:{current_date_min}"
                subprocess.run(["date", "+%T", "-s", full_time], check=True)
                
                # 4. Сохраняем в аппаратные часы (BIOS/RTC)
                os.system("hwclock --systohc")
                
                console.print(f"[bold green]✔ Время успешно изменено на {full_time}[/bold green]")
                console.print("[dim]Синхронизация NTP отключена для сохранения настроек.[/dim]")
                
            except Exception as e:
                console.print(f"[bold red]✘ Не удалось сменить время: {e}[/bold red]")
            
            time.sleep(2)



    def manage_i2p(self):
        pass

    def flush_dns_cache(self):
        os.system("sync; echo 3 > /proc/sys/vm/drop_caches")
        os.system("systemctl restart unbound")

    def run(self):
        while True:
            self.banner()
            for key, (name, _) in self.modules.items():
                console.print(f"[bold white]{key}[/bold white]: {name}")
            choice = Prompt.ask("\nВыбор", choices=list(self.modules.keys()))
            self.modules[choice][1]()

if __name__ == "__main__":
    if os.getuid() != 0:
        console.print("[red]Запусти от root (sudo)! [/red]")
        sys.exit(1)
    app = AnonManager()
    app.run()