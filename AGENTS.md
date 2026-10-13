# Agent guide

Local website to browse and reconcile Amazon order history. It reads JSON produced by
[order-history-exporter-for-amazon](https://github.com/xenolphthalein/order-history-exporter-for-amazon#usage).

## Stack
- Python 3.13, FastAPI, uvicorn. Managed with **uv** (never use pip directly).
- Frontend is a single static page (`app/static/index.html`) with vanilla JS. No build step.

## Commands
```
uv sync                                   # install deps
uv run uvicorn app.main:app --reload      # run at http://127.0.0.1:8000
uv run pytest                             # tests
uv add <pkg>  /  uv add --dev <pkg>       # add dependencies
```

## Layout
- `app/data.py`: loads `export-data/*.json`, normalizes, dedupes, search and sort.
- `app/main.py`: FastAPI app. `GET /api/orders?q=&sort=&dir=` and the static page at `/`.
- `app/static/index.html`: UI (orders table, expandable transaction and items).
- `tests/`: pytest tests using temp dirs, not the real export.
- `export-data/`: user's exports. Gitignored because it contains names and addresses. Never commit it or print its contents unnecessarily.
- `BACKLOG.md`: planned work. Check it before starting new features.

## Data model (export JSON = array of orders)
Order: `orderId`, `orderDate`, `totalAmount`, `currency`, `items[]`, `orderStatus`, `detailsUrl`,
`promotions[] {description, amount}`, `totalSavings`, `recipientName/Street/CityPostal/Country`.
Item: `title`, `asin`, `quantity`, `price` (unit), `discount`, `itemUrl`.

The export has no separate payment records. A **transaction** in this app is the order's charge:
`totalAmount`, `currency`, `totalSavings`, `promotions`, `orderStatus`. Line total = `price * quantity`.
`taxEstimate` = `totalAmount` minus the sum of line totals. It includes any shipping or fees, and is `null` (shown as a dash, sorted last) when the order has promotions or savings.

## Behavior rules
- Every `*.json` in `export-data/` is loaded on each request. Duplicate `orderId` across files: the file that sorts last by name wins.
- Search matches item title, ASIN, order ID (text), and any amount on the order (total, savings, promotion, unit price, line total, discount). Amounts match as substrings of the 2-decimal value, `$` and `,` ignored.
- Currency display is a browser-side setting (saved in localStorage). Default: show every amount in USD. Alternative: use each order's exported currency, with $0 orders shown as a dash. The exporter sometimes mislabels currency (for example EUR on $0 orders), so the data's `currency` is not fully trusted.
- Reconciled orders: `PUT /api/orders/{id}/reconciled` with `{"reconciled": bool}`. Stored in an in-memory set in `app/main.py`, so it resets when the server restarts and is never written to disk. `GET /api/orders` hides them unless `show_reconciled=true`.
- The exporter's "Additional discount" promotion is a catch-all that may include gift cards or other credits. The UI labels it that way. The export has no gift card field.
- The "Check items" badge is computed in the browser: it appears when an order's estimated tax/fees (see `taxEstimate`) are 1 or more percentage points above the local tax rate setting (default 11%, saved in localStorage), or negative. The server only supplies `itemSubtotal`. It hints at a missing or returned item, since the export has no return or refund data. The tax/fees column shows a dash for flagged orders, because the gap would include the missing item. It is a guess, not proof.
- Orders are sortable by every column server-side. Item columns sort client-side within an order.

## Conventions
- Keep it simple: no database, no frontend framework, no build tooling unless the backlog needs it.
- Add or update tests in `tests/` for any change to `app/data.py` or the API.
- Update `BACKLOG.md` when work is completed or new ideas come up.
