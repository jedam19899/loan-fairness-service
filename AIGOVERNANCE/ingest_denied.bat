@echo off
curl -X POST http://127.0.0.1:8000/ingest ^
  -H "Content-Type: application/json" ^
  -H "x-api-key: secret-key" ^
  -d "{\"application_id\":\"test2\",\"timestamp\":\"2025-07-02T20:05:00Z\",\"loan_amount\":6000,\"loan_duration_months\":12,\"loan_purpose\":\"auto\",\"employment_length_years\":2,\"annual_income\":30000,\"credit_score\":620,\"age\":35,\"sex\":\"M\",\"race\":\"Asian\",\"marital_status\":\"Married\",\"zipcode\":\"90210\",\"age_group\":\"30-39\",\"model_score\":0.40,\"approval_decision\":0}"
pause
