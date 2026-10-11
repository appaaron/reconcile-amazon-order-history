# Backlog

- [ ] Export to CSV
- [ ] Export to XLSX
- [ ] Export to PDF
- [x] Reconciled checkbox on each transaction
  - Checking it hides the transaction from the view.
  - Add a toggle to show reconciled transactions.
  - Reconciled state lives in server memory only: it persists while the web server is running and is not saved to disk or anywhere else.
- [ ] Show the date range of the loaded data
  - Display the earliest and latest order date across all combined JSON files in `export-data/`.
  - Show it at the top of the page, near the title and order count.
