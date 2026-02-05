import re
import socket
from urllib.parse import urlparse

class InputHandler:
    def __init__(self):
        # Regex for basic domain validation (e.g., example.com)
        self.domain_regex = re.compile(
            r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,6}$'
        )
        # Regex for IP validation (IPv4)
        self.ip_regex = re.compile(
            r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
        )

    def validate_target(self, target):
        """
        Validates if the input is a valid Domain, IP, or URL.
        Returns a cleaned 'hostname' (domain or IP) if valid, or None if invalid.
        """
        target = target.strip()
        
        # 1. Handle URLs (strip http://)
        if target.startswith("http://") or target.startswith("https://"):
            parsed = urlparse(target)
            target = parsed.netloc.split(':')[0] # Remove port if present

        # 2. Check if valid IP
        if self.ip_regex.match(target):
            return {"type": "ip", "target": target}

        # 3. Check if valid Domain
        if self.domain_regex.match(target):
            return {"type": "domain", "target": target}

        return None

    def check_connectivity(self, target):
        """
        Simple check to see if the target is reachable.
        """
        try:
            # Attempt to resolve hostname
            socket.gethostbyname(target)
            return True
        except socket.error:
            return False
