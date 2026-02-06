# Troubleshooting: Local Preview Not Reachable

## Issue Summary
Attempted to open `http://localhost:8000/index.html` but the page could not be reached.

## Environment
- OS: Windows (PowerShell)
- Project path: `C:\Users\inder\.cursor\ai-tracking\doc-pipelines`
- Python: `3.13.2`

## Checks Performed (and Results)
1. **Background job check**
   - Command: `Get-Job -Name doc-pipelines-server`
   - Result: Job not found.

2. **List all PowerShell jobs**
   - Command: `Get-Job`
   - Result: No jobs running.

3. **Port 8000 listener check**
   - Command: `Get-NetTCPConnection -LocalPort 8000`
   - Result: No output (no listener).
   - Fallback: `netstat -ano | findstr ":8000"`
   - Result: No output (port 8000 unused).

## Diagnosis
The local HTTP server is **not running**. There is no background job and no process listening on port `8000`, so the browser cannot connect.

## Likely Causes
- The server was started in a background job that **exited immediately**.
- The server was started in the foreground and **terminated** when the command timed out or the terminal session ended.
- The previous run did not actually launch (e.g., job creation failed or command context did not persist).

## How to Fix (Reliable Options)
### Option A: Foreground (simplest)
Run this in a PowerShell window and keep it open:
```powershell
cd C:\Users\inder\.cursor\ai-tracking\doc-pipelines
python -m http.server 8000
```
Then open:
```
http://localhost:8000/index.html
```

### Option B: Background Job (PowerShell)
```powershell
Start-Job -Name doc-pipelines-server -ScriptBlock {
  Set-Location 'C:\Users\inder\.cursor\ai-tracking\doc-pipelines'
  python -m http.server 8000
}
```
Verify it is running:
```powershell
Get-Job -Name doc-pipelines-server
```
If it fails, inspect the error:
```powershell
Receive-Job -Name doc-pipelines-server -Keep
```

## Notes for Learning
- A running HTTP server **must keep the process alive**. If the shell command times out or the job exits, the server stops.
- The quickest way to verify a server is up is to check for a **listener on the port** (e.g., `netstat` or `Get-NetTCPConnection`).

