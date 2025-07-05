-- Core performance tracking
CREATE TABLE prompt_performance_log (
  id SERIAL PRIMARY KEY,
  prompt_id VARCHAR(255) NOT NULL,
  prompt_text TEXT NOT NULL,
  pass_rate DECIMAL(5,4) NOT NULL,
  trust_score DECIMAL(5,4) NOT NULL,
  hallucination_rate DECIMAL(5,4) NOT NULL,
  total_runs INTEGER NOT NULL,
  failure_patterns JSONB,
  analyzed_at TIMESTAMP DEFAULT NOW(),
  INDEX idx_prompt_perf_id_time (prompt_id, analyzed_at),
  INDEX idx_prompt_perf_rates (pass_rate, trust_score)
);

-- Optimization results
CREATE TABLE prompt_optimizations (
  id SERIAL PRIMARY KEY,
  prompt_id VARCHAR(255) NOT NULL,
  original_prompt TEXT NOT NULL,
  optimized_prompt TEXT NOT NULL,
  optimization_strategy VARCHAR(100) NOT NULL,
  original_pass_rate DECIMAL(5,4) NOT NULL,
  original_trust_score DECIMAL(5,4) NOT NULL,
  generated_at TIMESTAMP DEFAULT NOW(),
  status VARCHAR(50) DEFAULT 'ready_for_testing',
  version VARCHAR(50) NOT NULL,
  approval_notes TEXT,
  INDEX idx_opt_status_time (status, generated_at)
);

-- Deployment tracking
CREATE TABLE prompt_deployments (
  id SERIAL PRIMARY KEY,
  deployment_id VARCHAR(255) UNIQUE NOT NULL,
  prompt_id VARCHAR(255) NOT NULL,
  deployed_version VARCHAR(50) NOT NULL,
  deployment_type VARCHAR(50) NOT NULL,
  deployed_at TIMESTAMP DEFAULT NOW(),
  status VARCHAR(50) DEFAULT 'active',
  expected_improvement DECIMAL(5,4),
  actual_improvement DECIMAL(5,4),
  rollback_at TIMESTAMP,
  INDEX idx_deploy_status_time (status, deployed_at)
);