import pandas as pd
from pathlib import Path
from tabulate import tabulate

def describe_csv(filepath: str) -> str:
    """Give the model a summary of the CSV before it writes any code."""
    try:
        df = pd.read_csv(filepath)
        lines = [
            f"File: {filepath}",
            f"Shape: {df.shape[0]} rows × {df.shape[1]} columns",
            f"\nColumns:",
        ]
        for col in df.columns:
            dtype = str(df[col].dtype)
            nulls = df[col].isnull().sum()
            if df[col].dtype in ("int64", "float64"):
                lines.append(
                    f"  {col} ({dtype}): min={df[col].min()}, "
                    f"max={df[col].max()}, nulls={nulls}"
                )
            else:
                n_unique = df[col].nunique()
                sample = df[col].dropna().head(3).tolist()
                lines.append(
                    f"  {col} ({dtype}): {n_unique} unique values, "
                    f"sample={sample}, nulls={nulls}"
                )
        lines.append(f"\nFirst 3 rows:\n{tabulate(df.head(3), headers='keys', tablefmt='simple')}") # type: ignore
        return "\n".join(lines)
    except Exception as e:
        return f"Error reading CSV: {e}"