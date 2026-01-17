from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import subprocess
import sys
import os
import uvicorn

app = FastAPI(title="Red Team Attack Console", version="1.0")

# Serve static files (templates)
templates_dir = os.path.join(os.path.dirname(__file__), 'templates')

# Global state for attack process
attack_process = None

class AttackRequest(BaseModel):
    target_ip: str
    port: int = 80
    threads: int = 100

@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve the attack dashboard HTML"""
    html_path = os.path.join(templates_dir, 'index.html')
    with open(html_path, 'r') as f:
        return HTMLResponse(content=f.read())

@app.get("/api/status")
async def status():
    """Check if an attack is currently running"""
    global attack_process
    is_running = attack_process is not None and attack_process.poll() is None
    return {"running": is_running}

@app.post("/api/stop")
async def stop_attack():
    """Stop the currently running attack"""
    global attack_process
    if attack_process:
        attack_process.terminate()
        attack_process = None
        return {"status": "stopped", "message": "Attack stopped successfully"}
    return {"status": "not_running", "message": "No attack running"}

@app.post("/api/attack")
async def start_attack(request: AttackRequest):
    """Start a network stress test attack"""
    global attack_process
    
    if not request.target_ip:
        raise HTTPException(status_code=400, detail="Target IP required")
        
    if attack_process and attack_process.poll() is None:
        raise HTTPException(status_code=409, detail="Attack already running")
        
    # Path to local stress test script
    script_path = os.path.join(os.path.dirname(__file__), '..', 'utils', 'network_stress_test.py')
    script_path = os.path.abspath(script_path)
    
    # Launch attack as subprocess
    try:
        cmd = [sys.executable, script_path, request.target_ip, str(request.port), str(request.threads)]
        attack_process = subprocess.Popen(cmd)
        return {"status": "started", "pid": attack_process.pid, "target": request.target_ip}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == '__main__':
    print("😈 Red Team Attack Console (FastAPI) starting on port 5002...")
    uvicorn.run(app, host='0.0.0.0', port=5002)
