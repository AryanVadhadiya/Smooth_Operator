import platform
import subprocess
import socket
import time
import asyncio
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class NetworkScanner:
    """
    Active network monitoring tools for real devices.
    Performs ping checks and port scans to gather real metrics from an IP.
    """
    
    COMMON_PORTS = {
        21: "FTP",
        22: "SSH",
        23: "Telnet",
        25: "SMTP",
        53: "DNS",
        80: "HTTP",
        443: "HTTPS",
        3306: "MySQL",
        3389: "RDP",
        5432: "PostgreSQL",
        8000: "HTTP-Alt",
        8080: "HTTP-Proxy"
    }

    @staticmethod
    def ping_host(host: str, timeout: int = 2) -> Dict[str, Any]:
        """
        Pings a host to check availability and latency.
        Returns: {'reachable': bool, 'latency_ms': float}
        """
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        command = ['ping', param, '1', "-W" if platform.system().lower() == 'darwin' else "-w", str(timeout * 1000) if platform.system().lower() == 'darwin' else str(timeout), host]
        
        try:
            start_time = time.time()
            # Run ping command
            result = subprocess.run(
                command, 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL,
                timeout=timeout + 1
            )
            
            end_time = time.time()
            is_reachable = (result.returncode == 0)
            latency = (end_time - start_time) * 1000 if is_reachable else 0.0
            
            # Simple simulation of "packet loss" if unreachable
            packet_loss = 0.0 if is_reachable else 100.0
            
            return {
                "is_reachable": is_reachable,
                "latency_ms": latency,
                "packet_loss": packet_loss
            }
            
        except subprocess.TimeoutExpired:
            return {"is_reachable": False, "latency_ms": 0.0, "packet_loss": 100.0}
        except Exception as e:
            logger.error(f"Ping error for {host}: {e}")
            return {"is_reachable": False, "latency_ms": 0.0, "packet_loss": 100.0}

    @staticmethod
    async def scan_common_ports(host: str, timeout: float = 0.5) -> Dict[str, Any]:
        """
        Scans common ports to fingerprint the device service state.
        Async to be efficient.
        """
        open_ports = []
        
        async def check_port(port, name):
            try:
                # Use asyncio stream opening for async connection check
                future = asyncio.open_connection(host, port)
                reader, writer = await asyncio.wait_for(future, timeout=timeout)
                writer.close()
                await writer.wait_closed()
                return port, name
            except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
                return None

        # Create tasks for all common ports
        tasks = [check_port(port, name) for port, name in NetworkScanner.COMMON_PORTS.items()]
        results = await asyncio.gather(*tasks)
        
        # Filter None results
        open_ports = [{"port": r[0], "service": r[1]} for r in results if r]
        
        return {
            "open_port_count": len(open_ports),
            "open_ports": open_ports,
            # Security risk calculation (simple heuristic based on open unsecured ports)
            "exposure_score": sum(1 for p in open_ports if p['port'] in [21, 23, 80]) * 10
        }

    @staticmethod
    async def get_device_metrics(ip_address: str) -> Dict[str, Any]:
        """
        Gather comprehensive metrics for a real IP address.
        """
        # 1. Availability check (Ping)
        ping_stats = NetworkScanner.ping_host(ip_address)
        
        metrics = {
            "is_simulated": False,
            "availability": 100.0 if ping_stats["is_reachable"] else 0.0,
            "network_latency_ms": ping_stats["latency_ms"],
            "packet_loss_percent": ping_stats["packet_loss"]
        }
        
        # 2. If reachable, check services
        if ping_stats["is_reachable"]:
            port_stats = await NetworkScanner.scan_common_ports(ip_address)
            metrics.update({
                "open_port_count": port_stats["open_port_count"],
                "security_exposure_score": port_stats["exposure_score"]
            })
            
            # Heuristic for traffic based on open ports (simulation of 'activity')
            # More open ports = more likely to have higher baseline traffic
            metrics["network_traffic_estimation"] = port_stats["open_port_count"] * 50.0  # arbitrary scale
            
        else:
            metrics.update({
                "open_port_count": 0,
                "security_exposure_score": 0,
                "network_traffic_estimation": 0.0
            })
            
        return metrics
