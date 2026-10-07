# Findings

Scope: 2010-12-01 to 2011-12-09.

- Recorded positive sales: **£10,666,684.54**, across **19,960 purchase invoices**.
- Average positive sale-line value per purchase invoice: **£534.40**.
- United Kingdom accounts for **84.6%** of the positive sales value.
- The highest complete month is **2011-11**, with **£1,509,496.33**.
- **65.6%** of identified purchasing customers have more than one purchase invoice.

## Interpretation

The UK dominates the recorded sales mix. November 2011 is the largest complete month; this is a descriptive observation, not proof of a seasonal cause. Repeat purchasing among identified customers is a useful prompt for deeper retention analysis, but anonymous customers and returns limit conclusions.

## Data preparation

Read 541,909 invoice lines; retained 530,104 positive sale lines and excluded 11,805 lines. Flagged 5,268 exact duplicate-looking rows without deleting them. Missing customer IDs occur in 135,080 source rows. Quality categories overlap and must not be added together.

## Limits

- Historical portfolio study, not current business performance.
- December 2011 is partial; do not compare it directly with complete months.
- Negative quantities, cancellations and nonpositive prices are excluded; returns are not subtracted.
- Anonymous sales count in totals; customer analysis excludes missing CustomerID.
- Exact duplicate-looking lines are flagged and retained because line identifiers are unavailable.
- Shipping, charges and adjustment StockCodes are retained when positive; totals are not merchandise-only.
- No observed trend is treated as a causal explanation or achieved business improvement.
