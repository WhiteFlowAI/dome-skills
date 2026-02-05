---
name: data-analysis
description: Analyze data using pandas and create visualizations with matplotlib. Use when the user needs data processing, statistics, or charts.
---

# Data Analysis Skill

## Overview

This skill provides data analysis and visualization capabilities using pandas and matplotlib.

## Dependencies

This skill requires additional packages (automatically installed):
- pandas: Data manipulation and analysis
- matplotlib: Plotting and visualization

## How to Analyze Data

### Load and Inspect Data

```python
import pandas as pd

# From CSV file in workspace
df = pd.read_csv("/workspace/data.csv")

# Quick inspection
print(f"Shape: {df.shape}")
print(f"Columns: {list(df.columns)}")
print(df.head())
print(df.describe())
```

### Basic Statistics

```python
import pandas as pd

df = pd.read_csv("/workspace/data.csv")

# Summary statistics
print("Mean:", df["column_name"].mean())
print("Median:", df["column_name"].median())
print("Std:", df["column_name"].std())

# Group by analysis
grouped = df.groupby("category")["value"].agg(["mean", "sum", "count"])
print(grouped)
```

### Create Visualizations

```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("/workspace/data.csv")

# Bar chart
fig, ax = plt.subplots(figsize=(10, 6))
df.groupby("category")["value"].sum().plot(kind="bar", ax=ax)
ax.set_title("Values by Category")
ax.set_xlabel("Category")
ax.set_ylabel("Total Value")
plt.tight_layout()
plt.savefig("/workspace/chart.png", dpi=150)
print("Chart saved to /workspace/chart.png")
```

## Examples

### Example 1: CSV Analysis

```python
import pandas as pd

# Load data
df = pd.read_csv("/workspace/sales.csv")

# Top 5 products by revenue
top_products = df.groupby("product")["revenue"].sum().nlargest(5)
print("Top 5 Products by Revenue:")
print(top_products)
```

### Example 2: Time Series Plot

```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("/workspace/metrics.csv")
df["date"] = pd.to_datetime(df["date"])
df = df.set_index("date")

fig, ax = plt.subplots(figsize=(12, 5))
df["value"].plot(ax=ax)
ax.set_title("Metrics Over Time")
plt.savefig("/workspace/timeseries.png")
print("Saved to /workspace/timeseries.png")
```
