"""
=============================================================
DECODING CUSTOMER VALUE — STEP 1
Data Preparation & Feature Engineering (Python)
=============================================================
Deliverable : Cleaned dataset + engineered features
              - dependency_score   (promo reliance proxy)
              - value_tier         (High / Mid / Low)
              - satisfaction_flag  (return-rate proxy)

Dataset     : UCI Online Retail II  (Dec 2010 – Dec 2011)
              Place the .xlsx file in ./data/ before running.
              Download link is in the Problem Statements PDF.
=============================================================
"""

import pandas as pd
import numpy as np
import os, warnings
warnings.filterwarnings("ignore")

RAW_PATH    = os.path.join("data", "online_retail_II.xlsx")
OUTPUT_PATH = os.path.join("outputs", "01_cleaned_features.csv")
os.makedirs("outputs", exist_ok=True)

# ── 1. LOAD ────────────────────────────────────────────────
print("▶ Loading raw dataset …")
try:
    df = pd.read_excel(RAW_PATH, sheet_name="Year 2010-2011", engine="openpyxl")
except FileNotFoundError:
    df = pd.read_excel(RAW_PATH, sheet_name=0, engine="openpyxl")

print(f"  Raw rows      : {len(df):,}")
print(f"  Columns       : {list(df.columns)}")

# ── 2. NORMALISE COLUMNS ───────────────────────────────────
df.columns = (df.columns.str.strip().str.lower()
                .str.replace(" ", "_").str.replace("-", "_"))

col_map = {
    "invoice":     "invoice_no",
    "invoiceno":   "invoice_no",
    "stockcode":   "stock_code",
    "customerid":  "customer_id",
    "customer_id": "customer_id",
    "customer id": "customer_id",   # UCI Online Retail II has a space
    "unitprice":   "unit_price",
    "price":       "unit_price",     # UCI Online Retail II uses 'Price'
    "invoicedate": "invoice_date",
}
# Strip spaces from column names before mapping
df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_").str.replace("-", "_")
df.rename(columns={c: col_map.get(c, c) for c in df.columns}, inplace=True)
print(f"  Mapped columns: {list(df.columns)}")

# ── 3. CLEAN ───────────────────────────────────────────────
print("\n▶ Cleaning …")
df.dropna(subset=["customer_id"], inplace=True)
df["customer_id"]  = df["customer_id"].astype(int)
df["invoice_date"] = pd.to_datetime(df["invoice_date"])

# Remove test/admin stock codes
bad_codes = {"POST","D","M","BANK CHARGES","PADS","DOT","AMAZONFEE","S"}
df = df[~df["stock_code"].astype(str).str.upper().isin(bad_codes)]

df["is_return"] = df["invoice_no"].astype(str).str.startswith("C")
df["revenue"]   = df["quantity"] * df["unit_price"]
df = df[~((df["unit_price"] <= 0) & (~df["is_return"]))]

forward_sales = df[~df["is_return"] & (df["quantity"] > 0)].copy()
returns       = df[df["is_return"]].copy()

print(f"  Forward sales : {len(forward_sales):,}")
print(f"  Returns       : {len(returns):,}")

# ── 4. SNAPSHOT DATE ───────────────────────────────────────
snapshot_date = forward_sales["invoice_date"].max() + pd.Timedelta(days=1)
print(f"\n▶ Snapshot date : {snapshot_date.date()}")

# ── 5. RFM BASE ────────────────────────────────────────────
print("\n▶ Computing RFM base …")
rfm = (forward_sales.groupby("customer_id").agg(
    last_purchase = ("invoice_date", "max"),
    frequency     = ("invoice_no",   "nunique"),
    monetary      = ("revenue",       "sum"),
    total_qty     = ("quantity",       "sum"),
    n_orders      = ("invoice_no",     "nunique"),
    n_items       = ("stock_code",     "nunique"),
).reset_index())
rfm["recency"] = (snapshot_date - rfm["last_purchase"]).dt.days

# avg order value
aov = (forward_sales.groupby(["customer_id","invoice_no"])["revenue"]
       .sum().reset_index()
       .groupby("customer_id")["revenue"].mean()
       .rename("avg_order_val"))
rfm = rfm.merge(aov, on="customer_id", how="left")

# ── 6. ENGINEERED FEATURES ────────────────────────────────
print("\n▶ Engineering features …")

# 6a. Satisfaction flag (return rate proxy)
return_qty = (returns.groupby("customer_id")["quantity"]
              .sum().abs().rename("return_qty"))
rfm = rfm.merge(return_qty, on="customer_id", how="left")
rfm["return_qty"]  = rfm["return_qty"].fillna(0)
rfm["return_rate"] = rfm["return_qty"] / (rfm["total_qty"] + rfm["return_qty"] + 1e-9)
p75_return = rfm["return_rate"].quantile(0.75)
rfm["satisfaction_flag"] = (
    (rfm["return_rate"] < p75_return) & (rfm["frequency"] >= 2)
).astype(int)

# 6b. Dependency score (promo months = Nov, Dec)
promo_months = {11, 12}
promo_orders = (
    forward_sales[forward_sales["invoice_date"].dt.month.isin(promo_months)]
    .groupby("customer_id")["invoice_no"].nunique().rename("promo_orders"))
rfm = rfm.merge(promo_orders, on="customer_id", how="left")
rfm["promo_orders"]     = rfm["promo_orders"].fillna(0)
rfm["dependency_score"] = (rfm["promo_orders"] / (rfm["n_orders"] + 1e-9)).round(4)

# 6c. Value tier
p33 = rfm["monetary"].quantile(0.33)
p66 = rfm["monetary"].quantile(0.66)
rfm["value_tier"] = rfm["monetary"].apply(
    lambda m: "High" if m >= p66 else ("Mid" if m >= p33 else "Low"))

# 6d. Two loyalty definitions
med_freq = rfm["frequency"].median()
rfm["loyal_defA"] = ((rfm["value_tier"] == "High") & (rfm["dependency_score"] < 0.5)).astype(int)
rfm["loyal_defB"] = ((rfm["frequency"] >= med_freq) & (rfm["recency"] <= 90)).astype(int)

# 6e. Tenure
first_purchase = (forward_sales.groupby("customer_id")["invoice_date"]
                  .min().rename("first_purchase"))
rfm = rfm.merge(first_purchase, on="customer_id", how="left")
rfm["tenure_days"] = (snapshot_date - rfm["first_purchase"]).dt.days

# ── 7. RFM SCORES ─────────────────────────────────────────
print("\n▶ Computing RFM scores …")
rfm["R_score"] = pd.qcut(rfm["recency"], 5, labels=[5,4,3,2,1]).astype(int)
rfm["F_score"] = pd.qcut(rfm["frequency"].rank(method="first"), 5, labels=[1,2,3,4,5]).astype(int)
rfm["M_score"] = pd.qcut(rfm["monetary"].rank(method="first"),  5, labels=[1,2,3,4,5]).astype(int)
rfm["RFM_score"] = (rfm["R_score"].astype(str)
                  + rfm["F_score"].astype(str)
                  + rfm["M_score"].astype(str))
rfm["RFM_total"] = rfm["R_score"] + rfm["F_score"] + rfm["M_score"]

# ── 8. SEGMENTS ────────────────────────────────────────────
def segment(row):
    r, f, m = row["R_score"], row["F_score"], row["M_score"]
    if   r >= 4 and f >= 4              : return "Champions"
    elif r >= 2 and f >= 3 and m >= 3   : return "Loyal Customers"
    elif r >= 3 and f <= 3 and m >= 3   : return "Potential Loyalists"
    elif r >= 4 and f <= 2              : return "New Customers"
    elif r >= 3 and f >= 2 and m >= 2   : return "Promising"
    elif r <= 2 and f >= 3 and m >= 3   : return "At Risk"
    elif r <= 2 and f >= 4 and m >= 4   : return "Can't Lose Them"
    elif r <= 2 and f >= 2 and m >= 2   : return "Need Attention"
    else                                : return "Lost"

rfm["segment"] = rfm.apply(segment, axis=1)

# ── 9. PRINT SUMMARY ──────────────────────────────────────
print("\n" + "="*55)
print(" FEATURE ENGINEERING SUMMARY")
print("="*55)
print(f"  Customers        : {len(rfm):,}")
print(f"\n  Value Tier split :")
print(rfm["value_tier"].value_counts().to_string())
print(f"\n  Segment counts   :")
print(rfm["segment"].value_counts().to_string())
print(f"\n  Avg dependency   : {rfm['dependency_score'].mean():.3f}")
print(f"  Avg return rate  : {rfm['return_rate'].mean():.3f}")
print(f"  % satisfied      : {rfm['satisfaction_flag'].mean()*100:.1f}%")
print(f"  Loyal (Def A)    : {rfm['loyal_defA'].sum():,}")
print(f"  Loyal (Def B)    : {rfm['loyal_defB'].sum():,}")
print(f"  Agreement rate   : {(rfm['loyal_defA']==rfm['loyal_defB']).mean()*100:.1f}%")
print("="*55)

# ── 10. SAVE ──────────────────────────────────────────────
cols_out = [
    "customer_id","recency","frequency","monetary",
    "avg_order_val","n_items","tenure_days",
    "return_rate","satisfaction_flag",
    "dependency_score","promo_orders","n_orders",
    "value_tier","loyal_defA","loyal_defB",
    "R_score","F_score","M_score","RFM_score","RFM_total","segment",
]
rfm[cols_out].to_csv(OUTPUT_PATH, index=False)
print(f"\n✅  Saved → {OUTPUT_PATH}")
