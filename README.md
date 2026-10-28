# Aguess

A-share end-of-day research scanner for mainland China main-board stocks.

The system builds a market-state view, routes to market-specific signal rules, and emits a JSON/HTML report. It is research software: it does not place orders.

## Run

Use the bundled Python environment and run `temp/daily_pick.py --no-update` for the legacy report, or `temp/daily_b4.py --source <temp-directory>` for the routed scanner.

## Scope

Only Shanghai/Shenzhen main-board symbols are considered. The default budget constraint is 2,000 RMB per position and a maximum of five candidates.
