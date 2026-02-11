import pandas as pd
import pickle
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

df = pd.read_csv("data/creditcard.csv")

le_location = LabelEncoder()
le_purpose = LabelEncoder()

df["location"] = le_location.fit_transform(df["location"])
df["purpose"] = le_purpose.fit_transform(df["purpose"])

df["date"] = pd.to_datetime(df["date"])
df["day"] = df["date"].dt.day
df["month"] = df["date"].dt.month
df["hour"] = df["time"].apply(lambda x: int(x.split(":")[0]))

df.drop(["date", "time"], axis=1, inplace=True)

X = df.drop("prediction", axis=1)
y = df["prediction"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

model = RandomForestClassifier(
    n_estimators=100,
    random_state=42
)

model.fit(X_train, y_train)

y_pred = model.predict(X_test)
print("Accuracy:", accuracy_score(y_test, y_pred))

model_bundle = {
    "model": model,
    "location_encoder": le_location,
    "purpose_encoder": le_purpose
}

with open("fraud_model.pkl", "wb") as f:
    pickle.dump(model_bundle, f)

print("✅ Model + encoders saved ")
