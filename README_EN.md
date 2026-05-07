# Savva Stealth System (SSS) ⚡

**Savva Stealth System** is a console utility for increasing anonymity and network security in Linux. The script automates a comprehensive system setup: from randomizing physical identifiers to creating a secure network perimeter.

> **Project Status:** `Alpha / Experimental` ⚠️  
> **Tested on:** `Arch Linux`

---

## ⚠️ DISCLAIMER
Using this software may lead to loss of network access, service disruption, and loss of data. 
* Run **only in a test environment** (VM, Live USB).
* Use at your own risk. 
* Always make backups and check the installer code before execution.

---

## 🛠 What the script does now

*   **Identification:** Generation of a random `hostname` and MAC address at the L2 level (including scan mode).
*   **DNS Protection:** Configuration of a local `Unbound` resolver with **DNS-over-TLS**. Blocking DNS hijacking via DHCP.
*   **Privacy:** Strict disabling of request/response logging, QNAME minimization, and hiding of service versions.
*   **Network Hardening:** Complete disabling of IPv6 at the kernel level to prevent leaks.
*   **Kill-Switch:** `iptables` configuration to block all outgoing traffic outside the whitelist of allowed services (Tor, local resolver, HTTP/S, etc.).
*   **Anti-Forensics:** Manual control of system time and disabling of NTP synchronization.
*   **Audit:** Real-time monitoring of active connections and telemetry of the status of protective mechanisms.

---

## 🛡 From what SSS protects your system

### Network Identification (L2/L3)
*   **MAC Tracking:** Prevents tracking your movements between Wi-Fi points.
*   **De-anonymization by Hostname:** Hides identity in router logs.
*   **DHCP Manipulations:** Protects against enforced suspicious DNS servers from the router.

### Traffic Privacy (DNS/IPv6)
*   **DNS Hijacking (MITM):** Encryption hides visited sites from the provider.
*   **Leaks via IPv6:** Blocks "backdoors" for traffic through which the real IP is visible.
*   **Local Tracking:** Zero Unbound logging guarantees no request history is stored on disk.

### Control and Footprint
*   **Kill-Switch:** Prohibits software from going online directly bypassing the protection.
*   **Fingerprinting:** Interferes with calculating location by time zones and OS version.

---

## 📦 Installation and launch

The script contains a built-in installer that automatically pulls dependencies (`unbound`, `tor`, `curl`, etc.) depending on the available package manager (`pacman` or `apt`).

### Launch
```bash
# It is recommended to run in emulation mode first:
sudo python main.py --dry-run

# Execution of changes:
sudo python main.py --confirm
```

# Backup recommendations (save before launch)

    Make backup copies of key configurations: sudo cp /etc/resolv.conf /etc/resolv.conf.bak
    sudo cp -r /etc/unbound /etc/unbound.bak
    sudo cp /etc/NetworkManager/NetworkManager.conf /etc/NetworkManager/NetworkManager.conf.bak
    sudo cp /etc/hosts /etc/hosts.bak
    sudo cp /etc/hostname /etc/hostname.bak
    To save the current state of iptables: sudo iptables-save > ~/iptables.rules.bak
    To save sysctl and IPv6 settings: sudo cp /etc/sysctl.conf /etc/sysctl.conf.bak
    If you change the system time — fix the current hardware time: sudo hwclock --systohc

# Best practices before launch

    Run only in an isolated environment (VM, Live USB) during the first test.
    Make sure you have physical or console access for recovery if you lose network access.
    Do not store real keys, passwords, or Tor bridges in the repository — use templates/placeholders.
    Check git history for possible secret leaks and clean if necessary.

# License and security

    The project is experimental; use with caution. 
    See SECURITY.md for details on vulnerability reporting and contacts (if available).
