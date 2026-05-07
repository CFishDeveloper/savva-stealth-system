import shutil
import subprocess
import os
from rich.console import Console
from rich.table import Table
from rich.live import Live

console = Console()

class DependencyManager:
    def __init__(self):
        # Список инструментов и их имен в разных менеджерах
        self.tools = {
            "curl": {"pacman": "curl", "apt": "curl"},
            "unbound": {"pacman": "unbound", "apt": "unbound"},
            "tor": {"pacman": "tor", "apt": "tor"},
            "i2p": {"pacman": "i2pd", "apt": "i2pd"} # i2pd эффективнее для Arch/Android
        }
        self.pkg_manager = self._detect_manager()

    def _detect_manager(self):
        if shutil.which("pacman"): return "pacman"
        if shutil.which("apt"): return "apt"
        return None

    def _is_installed(self, tool_name):
        # Для i2p проверяем и i2p, и i2pd
        if tool_name == "i2p":
            return shutil.which("i2pd") or shutil.which("i2p")
        return shutil.which(tool_name)

    def check_and_install_all(self):
        table = Table(title="[bold blue]Initial System Check[/bold blue]", show_header=True)
        table.add_column("Software", style="cyan")
        table.add_column("Status", justify="center")
        table.add_column("Action", style="dim")

        to_install = []

        # Первая фаза: Сбор данных
        for tool, pkgs in self.tools.items():
            if self._is_installed(tool):
                table.add_row(tool, "[bold green]INSTALLED[/bold green]", "None")
            else:
                table.add_row(tool, "[bold red]MISSING[/bold red]", "Will install")
                to_install.append(tool)

        console.print(table)

        if not to_install:
            console.print("[bold green]Everything is ready![/bold green]\n")
            return

        # Вторая фаза: Установка
        if self.pkg_manager:
            console.print(f"\n[bold yellow]Starting installation via {self.pkg_manager}...[/bold yellow]")
            for tool in to_install:
                pkg_name = self.tools[tool].get(self.pkg_manager, tool)
                console.print(f"[blue]>[/blue] Installing {pkg_name}...")
                
                try:
                    if self.pkg_manager == "pacman":
                        subprocess.run(["pacman", "-S", "--noconfirm", pkg_name], check=True)
                    elif self.pkg_manager == "apt":
                        subprocess.run(["apt-get", "install", "-y", pkg_name], check=True)
                    
                    console.print(f"  [bold green]✔[/bold green] {tool} installed.")
                except Exception as e:
                    console.print(f"  [bold red]✘[/bold red] Failed to install {tool}: {e}")
        else:
            console.print("[bold red]Critical Error: No package manager found![/bold red]")
