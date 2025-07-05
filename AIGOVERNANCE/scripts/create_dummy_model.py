# scripts/create_dummy_model.py

import sys
from pathlib import Path

# Ensure project root is on the path so we can import FEATURE_ORDER
sys.path.append(str(Path(__file__).parent.parent))

import pickle
from sklearn.tree import DecisionTreeClassifier  # CHANGED
from app import FEATURE_ORDER

# CHANGED: Use a tree‐based classifier so TreeExplainer works
model = DecisionTreeClassifier(max_depth=1, random_state=0)
# Fit on one dummy example of the right feature length
model.fit([[0] * len(FEATURE_ORDER)], [0])

# Serialize to model.pkl in the app directory
output_path = Path(__file__).parent.parent / "model.pkl"
with open(output_path, "wb") as f:
    pickle.dump(model, f)

print(f"✅ Created dummy DecisionTreeClassifier model at {output_path}")
