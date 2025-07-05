@echo off
curl -X POST http://127.0.0.1:8000/agent ^
  -H "Content-Type: application/json" ^
  -H "x-api-key: secret-key" ^
  -d "{\"prompt\":\"Explain the approval decision for application_id=test1\"}"
pause
