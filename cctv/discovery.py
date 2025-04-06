import asyncio
import ipaddress
import socket
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import threading

class CCTVScanner:
    """Enhanced CCTV Network Discovery Tool with Diagnostics"""
    
    def __init__(self):
        self._results = []
        self._scanning = False
        self._scan_complete = threading.Event()
        self._scan_thread = None
        self._loop = None
        self._progress = 0
        self._total_ips = 0
        
        # Expanded port list with more CCTV manufacturers
        self.ports = {
            # Common ports
            80: "HTTP", 443: "HTTPS", 8080: "Alt HTTP",
            
            # RTSP/Streaming
            554: "RTSP", 8554: "Alt RTSP", 10554: "RTSP",
            
            # Hikvision
            8000: "Hikvision", 34567: "Hikvision", 8899: "Hikvision Backdoor",
            
            # Dahua
            37777: "Dahua", 37778: "Dahua Mobile", 37779: "Dahua",
            
            # ONVIF
            9000: "ONVIF",
            
            # TP-Link
            8200: "TP-Link",
            
            # Other manufacturers
            8001: "Mobile Service", 8008: "AXIS", 9001: "Samsung",
            5000: "FLIR", 5001: "FLIR", 7000: "Pelco", 7001: "Pelco"
        }
        
        # Default settings
        self.timeout = 1.0  # Increased timeout for reliability
        self.max_concurrent = 200  # Reduced concurrency for stability
        self.verbose = False
    
    def scan_network(self, network_range: str) -> None:
        """Start network scan in background"""
        if self._scanning:
            raise RuntimeError("Scan already in progress")
        
        try:
            network = ipaddress.ip_network(network_range, strict=False)
            self._total_ips = network.num_addresses
        except ValueError as e:
            raise ValueError(f"Invalid network range: {e}")
        
        self._reset_scan_state()
        print(f"Scanning {self._total_ips} IPs on {network_range}...")
        
        self._scan_thread = threading.Thread(
            target=self._run_scan,
            args=(network,),
            daemon=True
        )
        self._scan_thread.start()
    
    def _reset_scan_state(self):
        """Reset all scan-related variables"""
        self._results = []
        self._scanning = True
        self._progress = 0
        self._scan_complete.clear()
        self._loop = asyncio.new_event_loop()
    
    def _run_scan(self, network):
        """Thread target that runs the async scan"""
        asyncio.set_event_loop(self._loop)
        
        try:
            start_time = datetime.now()
            found_devices = self._loop.run_until_complete(
                self._async_scan_network(network)
            )
            duration = datetime.now() - start_time
            
            print(f"\nScan completed in {duration.total_seconds():.2f} seconds")
            print(f"Scanned {self._progress}/{self._total_ips} IPs")
            print(f"Found {len(found_devices)} potential CCTV devices")
            
            self._results = found_devices
        except Exception as e:
            print(f"\nScan error: {str(e)}")
        finally:
            self._scanning = False
            self._scan_complete.set()
            self._loop.close()
    
    async def _async_scan_network(self, network):
        """Main async scanning coroutine"""
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def scan_single_ip(ip):
            async with semaphore:
                result = await self._scan_single_ip(str(ip))
                self._progress += 1
                if self.verbose and self._progress % 50 == 0:
                    print(f"Progress: {self._progress}/{self._total_ips} IPs scanned")
                return result
        
        tasks = [scan_single_ip(ip) for ip in network.hosts()]
        return [device for device in await asyncio.gather(*tasks) if device]
    
    async def _scan_single_ip(self, ip: str):
        """Scan single IP address"""
        try:
            # First try a quick ping check
            if not await self._is_host_alive(ip):
                return None
            
            # Then scan ports
            open_ports = []
            for port, service in self.ports.items():
                if await self._check_port(ip, port):
                    open_ports.append((port, service))
            
            return (ip, open_ports) if open_ports else None
        except Exception as e:
            if self.verbose:
                print(f"Error scanning {ip}: {str(e)}")
            return None
    
    async def _is_host_alive(self, ip: str) -> bool:
        """Check if host is responsive (ICMP ping alternative)"""
        try:
            # Try connecting to common port first as ICMP might be blocked
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, 80),
                timeout=0.5
            )
            writer.close()
            await writer.wait_closed()
            return True
        except:
            try:
                # Fallback to actual ping for devices that don't have port 80 open
                proc = await asyncio.create_subprocess_exec(
                    'ping', '-c', '1', '-W', '1', ip,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await proc.wait()
                return proc.returncode == 0
            except:
                return False
    
    async def _check_port(self, ip: str, port: int) -> bool:
        """Check if specific port is open"""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port),
                timeout=self.timeout
            )
            writer.close()
            await writer.wait_closed()
            return True
        except:
            return False
    
    def wait(self, timeout: Optional[float] = None) -> bool:
        """Wait for scan to complete with optional timeout"""
        return self._scan_complete.wait(timeout=timeout)
    
    def get_results(self) -> List[Tuple[str, List[Tuple[int, str]]]]:
        """Get scan results"""
        return self._results.copy()
    
    def is_scanning(self) -> bool:
        """Check if scan is in progress"""
        return self._scanning
    
    def print_results(self) -> None:
        """Display formatted results"""
        if not self._results:
            print("\nNo CCTV devices found. Possible reasons:")
            print("- Devices are not on the scanned network range")
            print("- Devices are behind firewalls blocking our probes")
            print("- Network requires authentication")
            print("- Try increasing timeout (currently {self.timeout}s)")
            print("- Try scanning a different network range")
            return
        
        print("\nDiscovered Devices:")
        print("-" * 70)
        print(f"{'IP':<15} | {'Open Ports':<50}")
        print("-" * 70)
        
        for ip, ports in self._results:
            port_desc = ", ".join(f"{p}:{s}" for p, s in ports)
            print(f"{ip:<15} | {port_desc:<50}")

# Example usage
if __name__ == "__main__":
    scanner = CCTVScanner()
    scanner.timeout = 1.5  # Increase timeout if needed
    scanner.verbose = True  # Show progress
    
    try:
        network = input("Enter network range (e.g., 192.168.1.0/24): ").strip()
        scanner.scan_network(network)
        
        print("Scan running in background...")
        while scanner.is_scanning():
            scanner.wait(5)  # Check every 5 seconds
            print(f"Progress: {scanner._progress}/{scanner._total_ips} IPs scanned")
        
        scanner.print_results()
    except KeyboardInterrupt:
        print("\nScan cancelled by user")
    except Exception as e:
        print(f"Error: {e}")