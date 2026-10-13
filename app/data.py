"""Load and query Amazon order-history JSON exports."""
from __future__ import annotations

import csv
import io
import json
import re
from pathlib import Path
from typing import Any

DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent / "export-data"

SORT_KEYS = {
    "orderId": lambda o: o["orderId"],
    "orderDate": lambda o: o["orderDate"],
    "itemCount": lambda o: o["itemCount"],
    "totalAmount": lambda o: o["totalAmount"],
    "totalSavings": lambda o: o["totalSavings"],
    "orderStatus": lambda o: o["orderStatus"].lower(),
    "taxEstimate": lambda o: o["taxEstimate"],
}


def _normalize(order: dict[str, Any], source: str) -> dict[str, Any]:
    items = []
    for it in order.get("items", []):
        qty = it.get("quantity", 1) or 1
        price = it.get("price", 0) or 0
        items.append(
            {
                "title": it.get("title", ""),
                "asin": it.get("asin", ""),
                "quantity": qty,
                "price": price,
                "discount": it.get("discount", 0) or 0,
                "lineTotal": round(price * qty, 2),
                "itemUrl": it.get("itemUrl", ""),
            }
        )
    total = order.get("totalAmount", 0) or 0
    promotions = order.get("promotions", [])
    savings = order.get("totalSavings", 0) or 0
    # Estimate only when nothing else (promotions/savings) can explain the gap between items and total.
    # Includes any shipping or fees, since the export does not itemize them.
    tax_estimate = None if promotions or savings else round(total - sum(i["lineTotal"] for i in items), 2)
    subtotal = sum(i["lineTotal"] for i in items)
    return {
        "orderId": order["orderId"],
        "orderDate": order.get("orderDate", ""),
        "currency": order.get("currency", "USD"),
        "totalAmount": order.get("totalAmount", 0) or 0,
        "totalSavings": order.get("totalSavings", 0) or 0,
        "orderStatus": order.get("orderStatus", ""),
        "detailsUrl": order.get("detailsUrl", ""),
        "promotions": order.get("promotions", []),
        "recipient": ", ".join(
            p
            for p in (
                order.get("recipientName"),
                order.get("recipientStreet"),
                order.get("recipientCityPostal"),
                order.get("recipientCountry"),
            )
            if p
        ),
        "items": items,
        "taxEstimate": tax_estimate,
        "itemSubtotal": round(subtotal, 2),
        "itemCount": sum(i["quantity"] for i in items),
        "source": source,
    }


def load_orders(data_dir: Path = DEFAULT_DATA_DIR) -> list[dict[str, Any]]:
    """Read every *.json in data_dir. Duplicate order IDs: the file that sorts last wins."""
    by_id: dict[str, dict[str, Any]] = {}
    for path in sorted(Path(data_dir).glob("*.json")):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(raw, list):
            continue
        for order in raw:
            if isinstance(order, dict) and order.get("orderId"):
                by_id[order["orderId"]] = _normalize(order, path.name)
    return list(by_id.values())


def date_range(orders: list[dict[str, Any]]) -> dict[str, str | None]:
    """Earliest and latest orderDate across all orders (None when there are no dates)."""
    dates = [o["orderDate"] for o in orders if o["orderDate"]]
    return {"from": min(dates, default=None), "to": max(dates, default=None)}


CSV_COLUMNS = [
    "orderId", "orderDate", "orderStatus", "currency", "totalAmount", "totalSavings", "taxEstimate",
    "reconciled", "itemTitle", "asin", "quantity", "unitPrice", "lineTotal", "itemDiscount",
]


def _csv_text(value: Any) -> Any:
    """Stop spreadsheets from running a text cell as a formula."""
    if isinstance(value, str) and value[:1] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + value
    return value


def orders_to_csv(orders: list[dict[str, Any]]) -> str:
    """One row per item. Order-level columns repeat on every row of the order, so do not sum them
    across rows. An order with no items still gets one row, with blank item columns."""
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\r\n")
    writer.writerow(CSV_COLUMNS)
    for o in orders:
        head = [
            o["orderId"], o["orderDate"], _csv_text(o["orderStatus"]), o["currency"], o["totalAmount"],
            o["totalSavings"], "" if o["taxEstimate"] is None else o["taxEstimate"],
            "yes" if o.get("reconciled") else "no",
        ]
        for i in o["items"] or [None]:
            item = ["", "", "", "", "", ""] if i is None else [
                _csv_text(i["title"]), i["asin"], i["quantity"], i["price"], i["lineTotal"], i["discount"],
            ]
            writer.writerow(head + item)
    return out.getvalue()


def _amount_strings(order: dict[str, Any]) -> list[str]:
    amounts = [order["totalAmount"], order["totalSavings"], order["taxEstimate"] or 0]
    amounts += [p.get("amount", 0) for p in order["promotions"]]
    for i in order["items"]:
        amounts += [i["price"], i["lineTotal"], i["discount"]]
    return [f"{a:.2f}" for a in amounts if a]


def matches(order: dict[str, Any], query: str) -> bool:
    """Match item title/ASIN/order ID text, or any dollar amount on the order."""
    q = query.strip().lower()
    if not q:
        return True
    if q in order["orderId"].lower():
        return True
    for i in order["items"]:
        if q in i["title"].lower() or q in i["asin"].lower():
            return True
    numeric = re.sub(r"[$,\s]", "", q)
    if re.fullmatch(r"(?=.*\d)\d*\.?\d*", numeric):  # digits with optional trailing "."
        return any(numeric in s for s in _amount_strings(order))
    return False


def query_orders(
    orders: list[dict[str, Any]], q: str = "", sort: str = "orderDate", direction: str = "desc"
) -> list[dict[str, Any]]:
    result = [o for o in orders if matches(o, q)]
    key = SORT_KEYS.get(sort, SORT_KEYS["orderDate"])
    reverse = direction.lower() != "asc"
    known = sorted((o for o in result if key(o) is not None), key=key, reverse=reverse)
    return known + [o for o in result if key(o) is None]  # missing values always last
