@echo off
curl -X POST http://127.0.0.1:8000/explain ^
  -H "Content-Type: application/json" ^
  -H "x-api-key: secret-key" ^
  -d "{\"application_id\":\"test1\",\"timestamp\":\"2025-07-02T20:00:00Z\",\"loan_amount\":5000,\"loan_duration_months\":24,\"loan_purpose\":\"education\",\"employment_length_years\":3,\"annual_income\":45000,\"credit_score\":680,\"age\":27,\"sex\":\"F\",\"race\":\"Asian\",\"marital_status\":\"Single\",\"zipcode\":\"90210\",\"age_group\":\"20-29\",\"model_score\":0.65,\"approval_decision\":1}"
pause
