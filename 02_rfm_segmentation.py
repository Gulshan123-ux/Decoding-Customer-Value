"""
=============================================================
DECODING CUSTOMER VALUE — STEP 2
RFM Segmentation Analysis + Visualisations
=============================================================
Reads  : outputs/01_cleaned_features.csv
Outputs: outputs/02_segment_profile.csv
         outputs/plots/  (all dashboard charts)
=============================================================
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import os, warnings
warnings.filterwarnings("ignore")

# ── paths ──────────────────────────────────────────────────
INPUT_PATH  = os.path.join("outputs", "01_cleaned_features.csv")
PLOT_DIR    = os.path.join("outputs", "plots")
os.makedirs(PLOT_DIR, exist_ok=True)

# ── palette ────────────────────────────────────────────────
SEGMENT_COLORS = {
    "Champions":          "#6366f1",
    "Loyal Customers":    "#06b6d4",
    "Potential Loyalists":"#10b981",
    "New Customers":      "#8b5cf6",
    "Promising":          "#f59e0b",
    "At Risk":            "#f43f5e",
    "Can't Lose Them":    "#ec4899",
    "Need Attention":     "#f97316",
    "Lost":               "#64748b",
}

DARK_BG    = "#0d1117"
CARD_BG    = "#161b22"
TEXT_COLOR = "#e6edf3"
GRID_COLOR = "#21262d"

plt.rcParams.update({
    "figure.facecolor":  DARK_BG,
    "axes.facecolor":    CARD_BG,
    "axes.edgecolor":    GRID_COLOR,
    "axes.labelcolor":   TEXT_COLOR,
    "axes.titlecolor":   TEXT_COLOR,
    "xtick.color":       TEXT_COLOR,
    "ytick.color":       TEXT_COLOR,
    "grid.color":        GRID_COLOR,
    "text.color":        TEXT_COLOR,
    "legend.facecolor":  CARD_BG,
    "legend.edgecolor":  GRID_COLOR,
    "font.family":       "DejaVu Sans",
    "font.size":         11,
})

# ── load ───────────────────────────────────────────────────
print("▶ Loading cleaned features …")
df = pd.read_csv(INPUT_PATH)
print(f"  Customers: {len(df):,}  |  Segments: {df['segment'].nunique()}")

# ordered segment list
seg_order = list(SEGMENT_COLORS.keys())
df["segment"] = pd.Categorical(df["segment"], categories=seg_order, ordered=True)

# ─────────────────────────────────────────────────────────
# CHART 1 — Overview Dashboard (2×2 + banner KPIs)
# ─────────────────────────────────────────────────────────
print("\n▶ Chart 1: Overview dashboard …")

fig = plt.figure(figsize=(20, 14), facecolor=DARK_BG)
fig.suptitle("Customer Value Intelligence Dashboard\n"
             "RFM Segmentation  ·  D2C Fashion Brand",
             fontsize=18, fontweight="bold", color=TEXT_COLOR, y=0.98)

# ── KPI banner ──
kpi_ax = fig.add_axes([0.02, 0.86, 0.96, 0.10])
kpi_ax.set_facecolor(DARK_BG); kpi_ax.axis("off")

total_rev  = df["monetary"].sum()
avg_aov    = df["avg_order_val"].mean()
champions  = (df["segment"] == "Champions").sum()
kpis = [
    (f"{len(df):,}",            "Total Customers",  "#6366f1"),
    (f"£{total_rev:,.0f}",      "Total Revenue",    "#06b6d4"),
    (f"£{avg_aov:,.1f}",        "Avg Order Value",  "#f59e0b"),
    (f"{champions:,}",          "Champions",        "#f43f5e"),
]
for i, (val, label, color) in enumerate(kpis):
    x = 0.12 + i * 0.25
    rect = mpatches.FancyBboxPatch((x-0.10, 0.05), 0.20, 0.85,
                                   boxstyle="round,pad=0.01",
                                   facecolor=CARD_BG, edgecolor=color,
                                   linewidth=2, transform=kpi_ax.transAxes)
    kpi_ax.add_patch(rect)
    kpi_ax.text(x, 0.62, val, ha="center", va="center", fontsize=20,
                fontweight="bold", color=color, transform=kpi_ax.transAxes)
    kpi_ax.text(x, 0.22, label, ha="center", va="center", fontsize=10,
                color=TEXT_COLOR, alpha=0.7, transform=kpi_ax.transAxes)

# ── Donut chart ──
ax1 = fig.add_subplot(2, 3, 1)
seg_counts = df["segment"].value_counts().reindex(seg_order).dropna()
colors = [SEGMENT_COLORS[s] for s in seg_counts.index]
wedges, texts, autotexts = ax1.pie(
    seg_counts.values, labels=None,
    colors=colors, autopct="%1.0f%%",
    pctdistance=0.82, startangle=140,
    wedgeprops=dict(width=0.5, edgecolor=DARK_BG, linewidth=2),
    textprops={"color": TEXT_COLOR, "fontsize": 8}
)
for at in autotexts: at.set_fontsize(7)
ax1.text(0, 0, f"{len(df):,}\nCustomers", ha="center", va="center",
         fontsize=11, fontweight="bold", color=TEXT_COLOR)
ax1.set_title("Customer Segments", fontweight="bold", pad=12)
ax1.legend(seg_counts.index, loc="lower left", bbox_to_anchor=(-0.3, -0.1),
           fontsize=7, ncol=1)

# ── Revenue by segment ──
ax2 = fig.add_subplot(2, 3, (2, 3))
seg_rev = df.groupby("segment", observed=True)["monetary"].sum().sort_values()
clrs = [SEGMENT_COLORS[s] for s in seg_rev.index]
bars = ax2.barh(seg_rev.index, seg_rev.values / 1e3, color=clrs,
                height=0.65, edgecolor=DARK_BG, linewidth=0.5)
for bar, val in zip(bars, seg_rev.values):
    ax2.text(bar.get_width() + 5, bar.get_y() + bar.get_height()/2,
             f"£{val/1e3:.0f}k", va="center", fontsize=9, color=TEXT_COLOR)
ax2.set_xlabel("Revenue (£ thousands)")
ax2.set_title("Revenue by Segment", fontweight="bold", pad=12)
ax2.grid(axis="x", alpha=0.3)
ax2.spines[["top","right","left"]].set_visible(False)

# ── Scatter: Recency vs Revenue ──
ax3 = fig.add_subplot(2, 3, 4)
for seg in seg_order:
    sub = df[df["segment"] == seg]
    ax3.scatter(sub["recency"], np.log1p(sub["monetary"]),
                c=SEGMENT_COLORS[seg], label=seg, alpha=0.55, s=18, edgecolors="none")
ax3.set_xlabel("Recency (days since last purchase)")
ax3.set_ylabel("log(Revenue £)")
ax3.set_title("Recency vs Revenue — All Customers", fontweight="bold", pad=12)
ax3.grid(alpha=0.2)
ax3.spines[["top","right"]].set_visible(False)

# ── Dependency Score Distribution ──
ax4 = fig.add_subplot(2, 3, 5)
for tier, color in [("High","#6366f1"),("Mid","#06b6d4"),("Low","#94a3b8")]:
    sub = df[df["value_tier"] == tier]["dependency_score"]
    ax4.hist(sub, bins=30, alpha=0.65, color=color, label=f"{tier} Value",
             edgecolor=DARK_BG, linewidth=0.3)
ax4.axvline(df["dependency_score"].mean(), color="#f59e0b", linewidth=1.5,
            linestyle="--", label=f"Mean={df['dependency_score'].mean():.2f}")
ax4.set_xlabel("Dependency Score (0=loyal, 1=promo-only)")
ax4.set_ylabel("# Customers")
ax4.set_title("Promo Dependency by Value Tier", fontweight="bold", pad=12)
ax4.legend(fontsize=8)
ax4.grid(alpha=0.2); ax4.spines[["top","right"]].set_visible(False)

# ── Purchase Frequency histogram ──
ax5 = fig.add_subplot(2, 3, 6)
ax5.hist(df["frequency"].clip(upper=30), bins=40,
         color="#6366f1", edgecolor=DARK_BG, linewidth=0.3, alpha=0.85)
med = df["frequency"].median()
ax5.axvline(med, color="#f59e0b", linewidth=2, linestyle="--",
            label=f"Median: {med:.0f}")
ax5.set_xlabel("Order Frequency (capped at 30)")
ax5.set_ylabel("# Customers")
ax5.set_title("Purchase Frequency", fontweight="bold", pad=12)
ax5.legend(fontsize=9)
ax5.grid(alpha=0.2); ax5.spines[["top","right"]].set_visible(False)

plt.tight_layout(rect=[0, 0, 1, 0.86])
p1 = os.path.join(PLOT_DIR, "dashboard_overview.png")
fig.savefig(p1, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
plt.close()
print(f"  Saved → {p1}")

# ─────────────────────────────────────────────────────────
# CHART 2 — Deep Dive Dashboard
# ─────────────────────────────────────────────────────────
print("\n▶ Chart 2: Deep dive dashboard …")

fig2, axes = plt.subplots(2, 2, figsize=(20, 13), facecolor=DARK_BG)
fig2.suptitle("Segment Deep Dive & Retention Intelligence\n"
              "D2C Fashion Brand — RFM Analysis",
              fontsize=17, fontweight="bold", color=TEXT_COLOR, y=1.01)

# ── Grouped Bar: Avg R/F/M per segment ──
ax = axes[0, 0]
profile = (df.groupby("segment", observed=True)[["R_score","F_score","M_score"]]
           .mean()
           .reindex(seg_order)
           .dropna())
x = np.arange(len(profile))
w = 0.25
ax.bar(x - w, profile["R_score"], w, label="Recency",   color="#6366f1", alpha=0.88)
ax.bar(x,     profile["F_score"], w, label="Frequency", color="#06b6d4", alpha=0.88)
ax.bar(x + w, profile["M_score"], w, label="Monetary",  color="#f59e0b", alpha=0.88)
ax.set_xticks(x)
ax.set_xticklabels(profile.index, rotation=30, ha="right", fontsize=8)
ax.set_ylabel("Avg Score (1-5)"); ax.set_ylim(0, 6)
ax.set_title("Avg RFM Scores by Segment", fontweight="bold", pad=12)
ax.legend(fontsize=9); ax.grid(axis="y", alpha=0.3)
ax.spines[["top","right"]].set_visible(False)

# ── Pareto Curve ──
ax = axes[0, 1]
df_sorted = df.sort_values("monetary", ascending=False).copy()
df_sorted["cum_pct_customers"] = np.arange(1, len(df_sorted)+1) / len(df_sorted) * 100
df_sorted["cum_pct_revenue"]   = df_sorted["monetary"].cumsum() / df_sorted["monetary"].sum() * 100
ax.plot(df_sorted["cum_pct_customers"], df_sorted["cum_pct_revenue"],
        color="#6366f1", linewidth=2.5)
ax.fill_between(df_sorted["cum_pct_customers"], df_sorted["cum_pct_revenue"],
                alpha=0.15, color="#6366f1")
# find 80% threshold
idx80 = (df_sorted["cum_pct_revenue"] >= 80).idxmax()
x80 = df_sorted.loc[idx80, "cum_pct_customers"]
ax.axhline(80, color="#f43f5e", linestyle="--", linewidth=1.2, label="80% revenue threshold")
ax.axvline(x80, color="#f59e0b", linestyle="--", linewidth=1.2,
           label=f"{x80:.0f}% of customers")
ax.set_xlabel("Cumulative % of Customers")
ax.set_ylabel("Cumulative % of Revenue")
ax.set_title("Revenue Concentration (Pareto)", fontweight="bold", pad=12)
ax.legend(fontsize=9); ax.grid(alpha=0.3)
ax.spines[["top","right"]].set_visible(False)
ax.set_xlim(0, 100); ax.set_ylim(0, 100)

# ── Heatmap: Recency × Frequency density ──
ax = axes[1, 0]
heat = df.groupby(["R_score","F_score"]).size().unstack(fill_value=0)
heat = heat.reindex(index=[5,4,3,2,1], columns=[1,2,3,4,5])
heat.index.name = "Recency Score"; heat.columns.name = "Frequency Score"
sns.heatmap(heat, ax=ax, cmap="YlOrRd", annot=True, fmt="d",
            linewidths=0.5, linecolor=DARK_BG,
            cbar_kws={"label":"# Customers"},
            annot_kws={"size":9, "color":"black"})
ax.set_title("Customer Density: Recency × Frequency", fontweight="bold", pad=12)
ax.set_xlabel("Frequency Score"); ax.set_ylabel("Recency Score")

# ── Box plots: Revenue by key segment ──
ax = axes[1, 1]
key_segs = ["Champions", "Loyal Customers", "At Risk", "Lost"]
box_data = [np.log1p(df[df["segment"]==s]["monetary"].values) for s in key_segs]
bp = ax.boxplot(box_data, patch_artist=True, notch=False,
                medianprops=dict(color="white", linewidth=2),
                whiskerprops=dict(color=TEXT_COLOR, linewidth=1),
                capprops=dict(color=TEXT_COLOR, linewidth=1.5),
                flierprops=dict(marker="o", markersize=3, alpha=0.4,
                                markerfacecolor=TEXT_COLOR))
for patch, seg in zip(bp["boxes"], key_segs):
    patch.set_facecolor(SEGMENT_COLORS[seg])
    patch.set_alpha(0.8)
ax.set_xticklabels(key_segs, fontsize=9)
ax.set_ylabel("log(Revenue £)")
ax.set_title("Revenue Distribution by Key Segment", fontweight="bold", pad=12)
ax.grid(axis="y", alpha=0.3)
ax.spines[["top","right"]].set_visible(False)

plt.tight_layout()
p2 = os.path.join(PLOT_DIR, "dashboard_deepdive.png")
fig2.savefig(p2, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
plt.close()
print(f"  Saved → {p2}")

# ─────────────────────────────────────────────────────────
# CHART 3 — Dependency Score vs Loyalty
# ─────────────────────────────────────────────────────────
print("\n▶ Chart 3: Loyalty definition comparison …")

fig3, axes3 = plt.subplots(1, 2, figsize=(16, 6), facecolor=DARK_BG)
fig3.suptitle("Loyal vs Discount Hunter — Two Competing Definitions",
              fontsize=15, fontweight="bold", color=TEXT_COLOR)

# Def A: Revenue-based
ax = axes3[0]
loyal_a = df[df["loyal_defA"]==1]
hunter_a = df[df["loyal_defA"]==0]
ax.scatter(hunter_a["dependency_score"], np.log1p(hunter_a["monetary"]),
           c="#f43f5e", alpha=0.35, s=15, label="Discount Hunter", edgecolors="none")
ax.scatter(loyal_a["dependency_score"], np.log1p(loyal_a["monetary"]),
           c="#06b6d4", alpha=0.55, s=20, label=f"Loyal (n={len(loyal_a):,})",
           edgecolors="none")
ax.axvline(0.5, color="#f59e0b", linestyle="--", linewidth=1.5, label="Threshold 0.5")
ax.set_xlabel("Dependency Score")
ax.set_ylabel("log(Revenue £)")
ax.set_title("Definition A: High-Value + Low Dependency", fontweight="bold")
ax.legend(fontsize=9); ax.grid(alpha=0.2)
ax.spines[["top","right"]].set_visible(False)

# Def B: Behavioural
ax = axes3[1]
loyal_b = df[df["loyal_defB"]==1]
hunter_b = df[df["loyal_defB"]==0]
ax.scatter(hunter_b["recency"], hunter_b["frequency"].clip(upper=50),
           c="#f43f5e", alpha=0.35, s=15, label="Non-Loyal", edgecolors="none")
ax.scatter(loyal_b["recency"], loyal_b["frequency"].clip(upper=50),
           c="#10b981", alpha=0.55, s=20, label=f"Loyal (n={len(loyal_b):,})",
           edgecolors="none")
ax.axvline(90, color="#f59e0b", linestyle="--", linewidth=1.5, label="90-day cutoff")
ax.set_xlabel("Recency (days)")
ax.set_ylabel("Frequency (orders)")
ax.set_title("Definition B: Recent + Frequent", fontweight="bold")
ax.legend(fontsize=9); ax.grid(alpha=0.2)
ax.spines[["top","right"]].set_visible(False)

plt.tight_layout()
p3 = os.path.join(PLOT_DIR, "loyalty_definitions.png")
fig3.savefig(p3, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
plt.close()
print(f"  Saved → {p3}")

# ─────────────────────────────────────────────────────────
# SEGMENT PROFILE TABLE
# ─────────────────────────────────────────────────────────
print("\n▶ Building segment profile …")

profile_df = df.groupby("segment", observed=True).agg(
    customers        = ("customer_id",     "count"),
    avg_recency      = ("recency",         "mean"),
    avg_frequency    = ("frequency",       "mean"),
    avg_monetary     = ("monetary",        "mean"),
    total_revenue    = ("monetary",        "sum"),
    avg_dependency   = ("dependency_score","mean"),
    pct_satisfied    = ("satisfaction_flag","mean"),
    loyal_defA_pct   = ("loyal_defA",       "mean"),
    loyal_defB_pct   = ("loyal_defB",       "mean"),
).round(2)

profile_df["revenue_share_%"] = (profile_df["total_revenue"] /
                                  profile_df["total_revenue"].sum() * 100).round(1)
profile_df.to_csv(os.path.join("outputs","02_segment_profile.csv"))

print("\n" + "="*65)
print(" SEGMENT PROFILE")
print("="*65)
print(profile_df[["customers","avg_recency","avg_frequency",
                   "avg_monetary","revenue_share_%","avg_dependency",
                   "pct_satisfied"]].to_string())
print("="*65)
print("\n✅  All charts and profiles saved to outputs/")
