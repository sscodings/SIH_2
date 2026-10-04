# Provider limits (checked 2026-09-30). Re-verify before demo; these change often.

## Etherscan V2
- Endpoint: https://api.etherscan.io/v2/api?chainid=<id>&module=...&apikey=<KEY>
- One key works across supported chains; ONE chainid per request (no comma lists).
- Free tier per Etherscan docs: 3 calls/s, up to 100,000 calls/day, SELECTED CHAINS ONLY.
  (Older docs/3rd-party pages say 5/s. Confirm on your dashboard.)
- Reports say Base, BNB Smart Chain, OP and Avalanche moved off the free tier.
  Check https://docs.etherscan.io/supported-chains before promising BSC. TODO: confirm chain by chain.
- Errors: "Max rate limit reached"; "Free API access is not supported for this chain"
  (upgrade needed); "Community Free API limit reached" (shared pool exhausted).
- Fallback for unsupported chains: Blockscout PRO API (free key, 5 RPS, 100K credits/day per their docs).
- Config default: 3 req/s, shared across ALL chains (use one global limiter).

## TronGrid
- Header: TRON-PRO-API-KEY. Free: 100K requests/day per account, ~15 QPS with key.
- Exceeding QPS => 403 and ~30s block; quota exhausted => throttled to very low rate.
- Newer docs describe limits only as examples (e.g. 30 rps, 1 rps after quota); use 10 QPS default.
- TRON block time ~3s: don't poll faster.

## CoinGecko (Demo/free)
- 100 calls/min (raised from 30 on 2026-05-17), 10,000 calls/month cap.
- Monthly cap is the binding limit: cache prices, batch with /simple/price.
- Demo key param: x_cg_demo_api_key; root URL api.coingecko.com. GET /key shows usage.

## Suggested config defaults
ETHERSCAN_RPS=3, TRONGRID_QPS=10, COINGECKO_RPM=60, COINGECKO_MONTHLY_BUDGET=9000