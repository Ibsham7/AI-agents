import pandas as pd
import numpy as np

np.random.seed(42)
n = 200

# Sales dataset
sales = pd.DataFrame({
    "date": pd.date_range("2024-01-01", periods=n, freq="D"),
    "product": np.random.choice(["Laptop", "Phone", "Tablet", "Watch"], n),
    "region": np.random.choice(["North", "South", "East", "West"], n),
    "units_sold": np.random.randint(1, 50, n),
    "unit_price": np.random.choice([999, 599, 399, 249], n),
    "discount_pct": np.random.choice([0, 5, 10, 15, 20], n),
})
sales["revenue"] = sales["units_sold"] * sales["unit_price"] * (1 - sales["discount_pct"]/100)
# Introduce some nulls for realism
sales.loc[np.random.choice(n, 10), "discount_pct"] = np.nan
sales.to_csv("datasets/sales.csv", index=False)

# Students dataset
students = pd.DataFrame({
    "student_id": range(1, 101),
    "name": [f"Student_{i}" for i in range(1, 101)],
    "major": np.random.choice(["CS", "Math", "Physics", "Engineering"], 100),
    "year": np.random.choice([1, 2, 3, 4], 100),
    "gpa": np.round(np.random.uniform(2.0, 4.0, 100), 2),
    "assignments_submitted": np.random.randint(5, 20, 100),
    "passed": np.random.choice([True, False], 100, p=[0.8, 0.2]),
})
students.to_csv("datasets/students.csv", index=False)

print("Created datasets/sales.csv and datasets/students.csv")