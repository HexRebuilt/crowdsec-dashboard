import logging
from typing import List, Dict, Any
import ipaddress

class IPWhitelist:
    def __init__(self, whitelist: List[str] = None):
        self.whitelist = whitelist or []
        self.ip_networks = []
        self._compile_whitelist()
    
    def _compile_whitelist(self):
        self.ip_networks = []
        for entry in self.whitelist:
            try:
                # Try to parse as CIDR network
                network = ipaddress.ip_network(entry, strict=False)
                self.ip_networks.append(network)
            except ValueError:
                # Try to parse as single IP address
                try:
                    ip = ipaddress.ip_address(entry)
                    self.ip_networks.append(ip)
                except ValueError:
                    logging.warning('Invalid IP whitelist entry: %s', entry)
    
    def is_allowed(self, ip: str) -> bool:
        try:
            ip_obj = ipaddress.ip_address(ip)
            for network in self.ip_networks:
                if ip_obj in network:
                    return True
            return False
        except ValueError:
            return False
    
    def add_ip(self, ip: str) -> bool:
        try:
            ip_obj = ipaddress.ip_address(ip)
            self.whitelist.append(ip)
            self.ip_networks.append(ip_obj)
            return True
        except ValueError:
            return False
    
    def add_network(self, cidr: str) -> bool:
        try:
            network = ipaddress.ip_network(cidr, strict=False)
            self.whitelist.append(cidr)
            self.ip_networks.append(network)
            return True
        except ValueError:
            return False
    
    def remove_ip(self, ip: str) -> bool:
        try:
            ip_obj = ipaddress.ip_address(ip)
            if ip in self.whitelist:
                self.whitelist.remove(ip)
                self.ip_networks = [net for net in self.ip_networks if net != ip_obj]
                return True
            return False
        except ValueError:
            return False
    
    def remove_network(self, cidr: str) -> bool:
        try:
            network = ipaddress.ip_network(cidr, strict=False)
            if cidr in self.whitelist:
                self.whitelist.remove(cidr)
                self.ip_networks = [net for net in self.ip_networks if net != network]
                return True
            return False
        except ValueError:
            return False
    
    def get_whitelist(self) -> List[str]:
        return self.whitelist
    
    def is_empty(self) -> bool:
        return len(self.ip_networks) == 0
    
    def clear(self):
        self.whitelist = []
        self.ip_networks = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'whitelist': self.whitelist,
            'count': len(self.ip_networks),
            'is_empty': self.is_empty()
        }
    
    def from_dict(self, data: Dict[str, Any]):
        self.whitelist = data.get('whitelist', [])
        self._compile_whitelist()

# Global IP whitelist instance
ip_whitelist = IPWhitelist()