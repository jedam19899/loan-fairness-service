# synthetic_loan_generator.py

import pandas as pd
import numpy as np
import uuid
import datetime

# Configuration: target proportions for attributes
N = 5000
race_probs = {"White": 0.58, "Black": 0.12, "Asian": 0.06, "Hispanic": 0.18, "Other": 0.06}
sex_probs = {"Male": 0.49, "Female": 0.51}
age_probs = {"18-35": 0.35, "36-55": 0.40, "56+": 0.25}

# Generate data
data = {
    "application_id": [str(uuid.uuid4()) for _ in range(N)],
    "timestamp": [datetime.datetime.now(datetime.timezone.utc) for _ in range(N)],
    "race": np.random.choice(list(race_probs), size=N, p=list(race_probs.values())),
    "sex": np.random.choice(list(sex_probs), size=N, p=list(sex_probs.values())),
    "age_group": np.random.choice(list(age_probs), size=N, p=list(age_probs.values())),
    "approval_decision": np.random.choice([1, 0], size=N, p=[0.7, 0.3]),
    "model_score": np.random.rand(N),
    "loan_amount": np.random.normal(20000, 5000, N).clip(1000, 50000),
    "loan_duration_months": np.random.choice([12, 24, 36, 48, 60], N),
    "loan_purpose": np.random.choice(["car", "home", "education", "other"], N),
    "annual_income": np.random.normal(80000, 20000, N).clip(20000, 200000),
    "zipcode": np.random.choice(["98101","10001","60601","90210"], N),
    "employment_length_years": np.random.choice([0,1,2,5,10,15], N),
    "credit_score": np.random.choice([600,650,700,750,800], N),
    "marital_status": np.random.choice(["Single","Married","Divorced"], N),
    "education_level": np.random.choice(["HS","Bachelors","Masters","PhD"], N)
}

df = pd.DataFrame(data)

# Quick distribution checks
print("Race distribution:\n", df["race"].value_counts(normalize=True))
print("\nSex distribution:\n", df["sex"].value_counts(normalize=True))
print("\nAge group distribution:\n", df["age_group"].value_counts(normalize=True))

# Save to CSV
df.to_csv("synthetic_loan_data.csv", index=False)
print("\n✅ synthetic_loan_data.csv saved with", len(df), "records.")
