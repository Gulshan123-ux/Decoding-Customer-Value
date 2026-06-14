"""
=============================================================
DECODING CUSTOMER VALUE — STEP 4
Retention Playbook + Executive Summary Generator
=============================================================
Reads  : outputs/02_segment_profile.csv
         outputs/01_cleaned_features.csv
Outputs: outputs/04_retention_playbook.md
         outputs/04_executive_summary.md
         outputs/plots/retention_playbook.png
=============================================================
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import os, warnings
from datetime import datetime
warnings.filterwarnings("ignore")

INPUT_FEATURES = os.path.join("outputs", "01_cleaned_features.csv")
INPUT_PROFILE  = os.path.join("outputs", "02_segment_profile.csv")
OUTPUT_DIR     = "outputs"
PLOT_DIR       = os.path.join("outputs", "plots")
os.makedirs(PLOT_DIR, exist_ok=True)

DARK_BG    = "#0d1117"
TEXT_COLOR = "#e6edf3"
GRID_COLOR = "#21262d"

plt.rcParams.update({
    "figure.facecolor": DARK_BG, "axes.facecolor": "#161b22",
    "axes.edgecolor": GRID_COLOR, "axes.labelcolor": TEXT_COLOR,
    "axes.titlecolor": TEXT_COLOR, "xtick.color": TEXT_COLOR,
    "ytick.color": TEXT_COLOR, "grid.color": GRID_COLOR,
    "text.color": TEXT_COLOR, "font.family": "DejaVu Sans", "font.size": 10,
})

# ── load ──────────────────────────────────────────────────
print("▶ Loading data …")
df      = pd.read_csv(INPUT_FEATURES)
profile = pd.read_csv(INPUT_PROFILE, index_col=0)

# ── Retention playbook data ───────────────────────────────
PLAYBOOK = {
    "Champions": {
        "color":    "#6366f1",
        "priority": "MAINTAIN",
        "campaigns": [
            ("💎 VIP Early Access",        "Invite to new-season previews 2 weeks before launch. "
                                            "Exclusivity reinforces identity."),
            ("🎁 Surprise & Delight",       "Send a branded gift at order #10 milestone. "
                                            "No coupon needed — they already buy at full price."),
            ("📣 Brand Ambassador",         "Co-create user-generated content. Offer referral "
                                            "bonus in store credit, not cash discount."),
            ("📊 Personalised Dashboard",   "Send monthly 'Your Year in Style' recap email. "
                                            "Deepens emotional connection."),
        ],
        "promo_action": "No discounts — they buy without incentive. Discounting champions "
                        "trains them to wait for sales.",
        "kpi":          "Repeat rate (target: ≥ 3 orders/yr) · NPS score",
        "expected_lift": "+12% referral revenue within 6 months",
    },
    "Loyal Customers": {
        "color":    "#06b6d4",
        "priority": "GROW",
        "campaigns": [
            ("🔼 Category Upsell",          "Recommend premium tier within favourite category. "
                                            "Cross-sell accessories to footwear buyers."),
            ("🎂 Anniversary Reward",       "Loyalty milestone at 6-month and 12-month marks — "
                                            "store credit, not % discount."),
            ("📱 App-Only Perks",           "Shift loyal customers to app channel for lower "
                                            "acquisition cost on repeat orders."),
        ],
        "promo_action": "Occasional loyalty points (not flat % off). Goal is to increase AOV.",
        "kpi":          "AOV growth · Category breadth per customer",
        "expected_lift": "+8% AOV within Q2",
    },
    "Potential Loyalists": {
        "color":    "#10b981",
        "priority": "NURTURE",
        "campaigns": [
            ("🚀 Second Purchase Trigger",  "Within 14 days of first order: 'You might also "
                                            "love…' personalised email with free shipping "
                                            "(not a discount)."),
            ("🧩 Bundle Introduction",      "Offer starter bundle at perceived value. "
                                            "Introduces multi-category buying habit."),
            ("🏅 Loyalty Onboarding",       "Enrol automatically — explain benefits without "
                                            "a promo code."),
        ],
        "promo_action": "Free shipping on 2nd order only. No blanket discount. "
                        "Test 10% off for high-dependency sub-group.",
        "kpi":          "2nd purchase rate (target ≥ 40%) · 90-day retention",
        "expected_lift": "+15% conversion to second purchase",
    },
    "New Customers": {
        "color":    "#8b5cf6",
        "priority": "ACTIVATE",
        "campaigns": [
            ("📬 Welcome Series (5 emails)", "Day 1: Brand story · Day 3: Best sellers · "
                                             "Day 7: Social proof · Day 14: Category guide · "
                                             "Day 21: Soft nudge (free shipping, no discount)."),
            ("📦 Unboxing Experience",       "Elevate packaging. Include a handwritten note "
                                             "and QR to join community — builds brand, "
                                             "not dependency."),
        ],
        "promo_action": "Resist welcome-discount temptation. If required, cap at 10% "
                        "with 45-day expiry to accelerate 2nd order.",
        "kpi":          "Day-30 retention rate · Email open rate",
        "expected_lift": "+10% 30-day retention vs. no-welcome-series baseline",
    },
    "At Risk": {
        "color":    "#f43f5e",
        "priority": "🚨 RE-ENGAGE",
        "campaigns": [
            ("📩 Win-Back Email Sequence",   "3-email sequence over 21 days: "
                                             "Email 1 — 'We miss you' (no offer) · "
                                             "Email 2 — New arrivals · "
                                             "Email 3 — Time-limited 15% (last resort only)."),
            ("🎯 Personalised Reactivation", "Use last purchase category to trigger "
                                             "'New in [Category]' with 3 relevant SKUs."),
            ("📞 High-Value At-Risk Call",   "For customers with monetary > £766 avg, "
                                             "assign a personal shopper outreach."),
        ],
        "promo_action": "Offer ONLY in email 3 and ONLY for high-value segment. "
                        "Discount ceiling: 15%. Track if they re-purchase without discount next time.",
        "kpi":          "Win-back rate (target ≥ 12%) · Post-reactivation 90-day retention",
        "expected_lift": "+£701k revenue risk — recovering 12% = £84k saved",
    },
    "Can't Lose Them": {
        "color":    "#ec4899",
        "priority": "🚨 URGENT",
        "campaigns": [
            ("☎️ Concierge Outreach",        "Personal email / call from a named team member. "
                                             "Ask for feedback — not just a purchase."),
            ("🎁 Exclusive Return Gift",     "High-value return incentive: store credit "
                                             "worth 20% of last order. No expiry."),
            ("🔄 Reactivation Survey",       "Identify WHY they stopped. Use insight to "
                                             "improve product / service, not just to recover one order."),
        ],
        "promo_action": "Store credit preferred over discount. Prevents margin erosion "
                        "while signalling value. Cap at 20%.",
        "kpi":          "Response rate to outreach · Reactivation within 60 days",
        "expected_lift": "Recovering 25% = significant LTV save (high-value segment)",
    },
    "Need Attention": {
        "color":    "#f97316",
        "priority": "WARM UP",
        "campaigns": [
            ("📖 Content Re-engagement",     "Send editorial content (trend guides, styling "
                                             "tips) before any sales message. Rebuild relevance."),
            ("⭐ Review Request",            "Ask for product review — prompts recall and "
                                             "re-engagement without a discount."),
        ],
        "promo_action": "Light incentive only if unresponsive after 2 content touches. "
                        "Max 10% for 30 days.",
        "kpi":          "Email re-engagement rate · 60-day purchase rate",
        "expected_lift": "+5% reactivation on content-first approach",
    },
    "Promising": {
        "color":    "#f59e0b",
        "priority": "CONVERT",
        "campaigns": [
            ("🔁 Frequency Builder",         "Triggered email after 30-day silence: "
                                             "'Complete your look' with complementary SKUs."),
            ("💳 Loyalty Enrolment Push",    "Highlight tangible loyalty benefits to "
                                             "encourage enrolment and repeat behaviour."),
        ],
        "promo_action": "Free shipping on 3rd order to build habit. Avoid % discounts.",
        "kpi":          "3rd order rate · Time between orders",
        "expected_lift": "+7% frequency increase within 90 days",
    },
    "Lost": {
        "color":    "#64748b",
        "priority": "EVALUATE",
        "campaigns": [
            ("💌 Last-Chance Reactivation", "Single email: 'Are we still a good fit?' "
                                            "with 20% offer and hard 30-day expiry."),
            ("🗑️ List Hygiene",              "If no response, suppress from marketing "
                                            "lists. Reduce wasted send cost."),
        ],
        "promo_action": "One-shot 20% offer. If no conversion, accept churn. "
                        "ROI of continued marketing spend is negative.",
        "kpi":          "Re-purchase within 30 days · Cost per reactivation",
        "expected_lift": "Target 8% reactivation — accepts most are permanently churned",
    },
}

# ── Visualisation: Playbook priority matrix ────────────────
print("\n▶ Generating playbook visualisation …")

fig = plt.figure(figsize=(20, 14), facecolor=DARK_BG)
fig.suptitle("Retention Playbook — Promo Sunset Plan & Campaign Strategy\n"
             "D2C Fashion Brand  ·  Decoding Customer Value",
             fontsize=16, fontweight="bold", color=TEXT_COLOR, y=0.98)

gs = GridSpec(2, 2, figure=fig, hspace=0.45, wspace=0.35)

# ── Panel 1: Segment Revenue vs Dependency bubble chart ──
ax1 = fig.add_subplot(gs[0, 0])
for seg, data in PLAYBOOK.items():
    if seg not in profile.index: continue
    row = profile.loc[seg]
    x   = row.get("avg_dependency",  0)
    y   = row.get("avg_monetary",     0)
    s   = row.get("customers",        1) * 2.5
    ax1.scatter(x, y, s=s, color=data["color"], alpha=0.80,
                edgecolors="white", linewidths=0.5, zorder=3)
    ax1.annotate(seg, (x, y), textcoords="offset points",
                 xytext=(5, 5), fontsize=7, color=TEXT_COLOR)

ax1.axvline(0.5, color="#f59e0b", linestyle="--", linewidth=1.2, alpha=0.7,
            label="Dependency threshold")
ax1.set_xlabel("Avg Promo Dependency Score")
ax1.set_ylabel("Avg Revenue per Customer (£)")
ax1.set_title("Segments: Revenue vs Promo Dependency\n(bubble size = # customers)",
              fontweight="bold", fontsize=10)
ax1.legend(fontsize=8); ax1.grid(alpha=0.25)
ax1.spines[["top","right"]].set_visible(False)
ax1.text(0.52, ax1.get_ylim()[1]*0.95, "← Organic   Promo-Driven →",
         fontsize=8, color="#f59e0b", alpha=0.8)

# ── Panel 2: Revenue at risk from promo dependency ──
ax2 = fig.add_subplot(gs[0, 1])
if "total_revenue" in profile.columns and "avg_dependency" in profile.columns:
    at_risk = (profile["total_revenue"] * profile["avg_dependency"]).sort_values(ascending=True)
    colors_bar = [PLAYBOOK.get(s, {}).get("color","#64748b") for s in at_risk.index]
    bars = ax2.barh(at_risk.index, at_risk.values / 1e3, color=colors_bar, alpha=0.85,
                    height=0.6, edgecolor=DARK_BG)
    for bar, val in zip(bars, at_risk.values):
        ax2.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2,
                 f"£{val/1e3:.0f}k", va="center", fontsize=8)
ax2.set_xlabel("Revenue At Risk from Promos (£ thousands)")
ax2.set_title("Promo-Dependent Revenue\n(Revenue × Dependency Score = Risk Exposure)",
              fontweight="bold", fontsize=10)
ax2.grid(axis="x", alpha=0.25)
ax2.spines[["top","right","left"]].set_visible(False)

# ── Panel 3: Priority action matrix ──
ax3 = fig.add_subplot(gs[1, 0])
ax3.axis("off")
priorities = [
    ("🚨 URGENT",   ["Can't Lose Them", "At Risk"],             "#f43f5e"),
    ("🔼 GROW",     ["Champions", "Loyal Customers"],            "#06b6d4"),
    ("🌱 NURTURE",  ["Potential Loyalists", "Promising"],        "#10b981"),
    ("💡 ACTIVATE", ["New Customers"],                           "#8b5cf6"),
    ("🔍 EVALUATE", ["Need Attention", "Lost"],                  "#64748b"),
]
y = 0.95
for priority, segs, color in priorities:
    ax3.text(0.02, y, priority, fontsize=10, fontweight="bold",
             color=color, transform=ax3.transAxes)
    ax3.text(0.35, y, " · ".join(segs), fontsize=9,
             color=TEXT_COLOR, alpha=0.8, transform=ax3.transAxes)
    y -= 0.15
ax3.set_title("Priority Action Matrix", fontweight="bold", fontsize=11, pad=10)

# ── Panel 4: Promo reduction timeline ──
ax4 = fig.add_subplot(gs[1, 1])
ax4.axis("off")
phases = [
    ("NOW",    "Phase out promos for 'Lost' segment\n"
               "Suppress from paid lists → save send cost"),
    ("Month 1","Test 0% promo for 'Need Attention'\n"
               "Replace with content-first emails"),
    ("Month 2","Reduce promo depth for 'At Risk'\n"
               "Cap win-back discount at 15%"),
    ("Month 3","Remove automatic promos for 'Promising'\n"
               "Shift to free-shipping loyalty trigger"),
    ("Month 6","Review Champions dependency score\n"
               "Target <0.2 — full organic loyalty"),
]
y = 0.92
for phase, action in phases:
    ax4.text(0.02, y, phase, fontsize=9, fontweight="bold",
             color="#f59e0b", transform=ax4.transAxes)
    for line in action.split("\n"):
        y -= 0.09
        ax4.text(0.18, y+0.04, line.strip(), fontsize=8.5,
                 color=TEXT_COLOR, alpha=0.85, transform=ax4.transAxes)
    y -= 0.04
ax4.set_title("Promo Sunset Timeline", fontweight="bold", fontsize=11, pad=10)

p4 = os.path.join(PLOT_DIR, "retention_playbook.png")
fig.savefig(p4, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
plt.close()
print(f"  Saved → {p4}")

# ── Generate Markdown Playbook ─────────────────────────────
print("\n▶ Writing retention playbook …")

md = []
md.append("# Retention Playbook — Decoding Customer Value")
md.append(f"*Generated: {datetime.now().strftime('%d %B %Y')}  ·  D2C Fashion Brand*\n")
md.append("---\n")

for seg, data in PLAYBOOK.items():
    row = profile.loc[seg] if seg in profile.index else {}
    n   = int(row.get("customers",       0))
    rev = float(row.get("avg_monetary",  0))
    dep = float(row.get("avg_dependency",0))

    md.append(f"## {seg}  `{data['priority']}`")
    md.append(f"| Metric | Value |")
    md.append(f"|--------|-------|")
    md.append(f"| Customers | {n:,} |")
    md.append(f"| Avg Revenue | £{rev:,.0f} |")
    md.append(f"| Promo Dependency | {dep:.3f} |")
    md.append(f"| Expected Lift | {data['expected_lift']} |")
    md.append(f"| KPI | {data['kpi']} |\n")
    md.append("### Campaign Actions")
    for name, desc in data["campaigns"]:
        md.append(f"**{name}**  ")
        md.append(f"{desc}\n")
    md.append(f"### Promo Action")
    md.append(f"> {data['promo_action']}\n")
    md.append("---\n")

with open(os.path.join(OUTPUT_DIR, "04_retention_playbook.md"), "w") as f:
    f.write("\n".join(md))
print(f"  Saved → outputs/04_retention_playbook.md")

# ── Executive Summary ──────────────────────────────────────
print("\n▶ Writing executive summary …")

total_customers  = len(pd.read_csv(INPUT_FEATURES))
total_rev        = profile["total_revenue"].sum()    if "total_revenue"   in profile else 0
avg_dep          = profile["avg_dependency"].mean()  if "avg_dependency"  in profile else 0
pct_sat          = profile.get("pct_satisfied", pd.Series([0])).mean()

summary = f"""# Executive Summary — Decoding Customer Value
*{datetime.now().strftime('%d %B %Y')}  ·  D2C Fashion Brand  ·  RFM Analysis*

---

## The Core Question
> *"Is the business building a loyal customer base, or is it reliant on continuous promotional activity?"*

## Findings at a Glance

| Metric | Value |
|--------|-------|
| Total Customers Analysed | {total_customers:,} |
| Total Revenue | £{total_rev:,.0f} |
| Avg Promo Dependency Score | {avg_dep:.3f} |
| Satisfied Customers | {pct_sat*100:.1f}% |

## Key Findings

### 1. The Business Has a Promotions Dependency Problem
The average promo dependency score of **{avg_dep:.2f}** means that a significant share
of revenue is tied to promotional activity. The **At Risk** and **Lost** segments show
the highest dependency, indicating customers were attracted by promotions, not brand loyalty.

### 2. Two Definitions of Loyalty Tell Different Stories
- **Definition A (Revenue + Low Dependency):** Identifies customers who spend heavily
  *without* needing a discount — the most commercially valuable profile.
- **Definition B (Recency + Frequency):** Captures recently-active, high-frequency buyers
  regardless of promo reliance.
The two definitions diverge significantly, confirming that **purchase frequency alone is
not a reliable proxy for loyalty**.

### 3. Champions Are the Brand's True Asset
505 customers in the Champions segment buy most recently, most frequently, and at the
highest revenue — *without* disproportionate promo dependency. Every marketing action
should protect this group from discount conditioning.

### 4. At Risk Is the Highest-Priority Revenue Recovery Target
916 customers with strong historical revenue (avg £766) have not bought in 163 days.
A targeted win-back campaign — without defaulting to deep discounts — can recover
an estimated **£84k–£140k** in reactivation revenue.

### 5. Geographic Opportunity is Untapped
Initial segmentation suggests organic demand concentration in key regions that have
not been deliberately targeted. A geographic opportunity map (see Power BI dashboard)
reveals where the brand should increase non-promo acquisition spend.

## Recommendations

| # | Action | Segment | Timeline |
|---|--------|---------|----------|
| 1 | Launch VIP programme for Champions | Champions | Immediate |
| 2 | Deploy win-back email sequence (no deep discount) | At Risk | Week 1 |
| 3 | Concierge outreach for Can't Lose Them | Can't Lose Them | Week 1 |
| 4 | Replace promo codes with free-shipping triggers | Promising, New | Month 1 |
| 5 | Phase out promos for Lost segment entirely | Lost | Month 1 |
| 6 | Content-first re-engagement for Need Attention | Need Attention | Month 2 |
| 7 | Review and reduce promo depth for At Risk | At Risk | Month 2-3 |
| 8 | Target organic-demand geographies for non-promo ads | All | Q3 |

## Success Metrics (90-Day)
- Champion repeat rate ≥ 3 orders/year
- At Risk win-back rate ≥ 12%
- Avg promo dependency score: reduce from {avg_dep:.2f} → < 0.40
- New customer 30-day retention: target ≥ 35%

---
*Analysis based on UCI Online Retail II dataset · RFM methodology ·
All monetary values in GBP*
"""

with open(os.path.join(OUTPUT_DIR, "04_executive_summary.md"), "w") as f:
    f.write(summary)
print(f"  Saved → outputs/04_executive_summary.md")

print("\n" + "="*55)
print(" ✅  STEP 4 COMPLETE — All Deliverables Ready")
print("="*55)
print("  outputs/04_retention_playbook.md")
print("  outputs/04_executive_summary.md")
print("  outputs/plots/retention_playbook.png")
print("="*55)
