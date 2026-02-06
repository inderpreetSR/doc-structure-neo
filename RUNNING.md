# Running the Local Docs Site

## Status
The local server is running and the site is reachable at:
```
http://localhost:8000/index.html
```

## How It Was Started
A background PowerShell process was launched to serve `doc-pipelines`:
```powershell
Start-Process -FilePath "powershell" -WindowStyle Hidden -ArgumentList "-NoProfile","-Command","cd 'C:\Users\inder\.cursor\ai-tracking\doc-pipelines'; python -m http.server 8000"
```

## Verification
Port 8000 is listening:
```
netstat -ano | findstr ":8000"
```

## How to Stop It
Find and terminate the listening process:
```powershell
netstat -ano | findstr ":8000"
```
Then:
```powershell
Stop-Process -Id <PID> -Force
```

