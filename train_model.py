import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import LabelEncoder
import pickle

data = {
    "amount": [500, 1000, 2000, 3000, 1500, 2500, 4000, 5000, 1200, 1800],
    "location": [
        "Hyderabad", "Hyderabad", "Bangalore", "Bangalore",
        "Chennai", "Chennai", "Hyderabad", "Mumbai",
        "Mumbai", "Hyderabad"
    ]
}

df = pd.DataFrame(data)

# Encode location (text → numbers)
location_encoder = LabelEncoder()
df["location_encoded"] = location_encoder.fit_transform(df["location"])

X = df[["amount", "location_encoded"]]

# Train Isolation Forest
model = IsolationForest(
    n_estimators=200,
    contamination=0.1,
    random_state=42
)

model.fit(X)

with open("fraud_model.pkl", "wb") as f:
    pickle.dump(model, f)

with open("location_encoder.pkl", "wb") as f:
    pickle.dump(location_encoder, f)

print("✅ Fraud Detection Model trained with Amount + Location!")
