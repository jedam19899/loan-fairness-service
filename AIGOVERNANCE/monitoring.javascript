// Function Node - Performance Monitoring
function() {
  const deployments = $input.all();
  const alerts = [];
  
  for (const deploy of deployments) {
    const data = deploy.json;
    
    // Check for performance regression
    if (data.actual_improvement < -0.05) {
      alerts.push({
        type: 'performance_regression',
        deployment_id: data.deployment_id,
        severity: 'high',
        message: `Prompt ${data.prompt_id} showing ${(data.actual_improvement * 100).toFixed(1)}% performance decline`
      });
    }
    
    // Check for insufficient improvement
    if (data.actual_improvement < data.expected_improvement * 0.5) {
      alerts.push({
        type: 'underperforming_optimization',
        deployment_id: data.deployment_id,
        severity: 'medium',
        message: `Optimization for ${data.prompt_id} achieving only ${(data.actual_improvement * 100).toFixed(1)}% improvement (expected ${(data.expected_improvement * 100).toFixed(1)}%)`
      });
    }
  }
  
  return alerts;
}