# Backlog

- [x] Export to CSV
  - `GET /api/orders.csv` (same `q`, `sort`, `dir`, `show_reconciled` as `/api/orders`), "Export CSV" link in the header.
  - One row per item. Order-level columns repeat on each row, so do not sum them across rows.
- [ ] ~~Export to XLSX~~ Dropped: CSV opens in Excel and Google Sheets.
- [ ] ~~Export to PDF~~ Dropped: the browser's Print > Save as PDF covers it.
- [x] Reconciled checkbox on each transaction
  - Checking it hides the transaction from the view.
  - Add a toggle to show reconciled transactions.
  - Reconciled state lives in server memory only: it persists while the web server is running and is not saved to disk or anywhere else.
- [x] Show the date range of the loaded data
  - Display the earliest and latest order date across all combined JSON files in `export-data/`.
  - Show it at the top of the page, near the title and order count.
