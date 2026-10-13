from pathlib import Path

from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from . import data

STATIC = Path(__file__).resolve().parent / "static"

app = FastAPI(title="Amazon Order History")

# Reconciled order IDs. In-memory only: lasts while this server process runs, never written to disk.
reconciled: set[str] = set()


SortParam = Query("orderDate", pattern="^(" + "|".join(data.SORT_KEYS) + ")$")
DirParam = Query("desc", pattern="^(asc|desc)$")


@app.get("/api/orders.csv")
def export_csv(q: str = "", sort: str = SortParam, dir: str = DirParam, show_reconciled: bool = False):
    """The orders list as CSV, one row per item. Takes the same filters as /api/orders."""
    orders = data.query_orders(data.load_orders(), q, sort, dir)
    for o in orders:
        o["reconciled"] = o["orderId"] in reconciled
    if not show_reconciled:
        orders = [o for o in orders if not o["reconciled"]]
    # BOM so Excel reads the file as UTF-8
    body = "﻿" + data.orders_to_csv(orders)
    return Response(
        body, media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="amazon-orders.csv"'},
    )


@app.get("/api/orders")
def list_orders(q: str = "", sort: str = SortParam, dir: str = DirParam, show_reconciled: bool = False):
    """Orders (each with its transaction fields and items), reloaded from export-data on every call.

    Reconciled orders are hidden unless show_reconciled is true; hidden_count says how many were hidden.
    date_range is the earliest and latest order date across all loaded orders, ignoring search and reconciled filters.
    """
    all_orders = data.load_orders()
    orders = data.query_orders(all_orders, q, sort, dir)
    for o in orders:
        o["reconciled"] = o["orderId"] in reconciled
    visible = orders if show_reconciled else [o for o in orders if not o["reconciled"]]
    return {
        "count": len(visible),
        "hidden_count": len(orders) - len(visible),
        "date_range": data.date_range(all_orders),
        "orders": visible,
    }


@app.put("/api/orders/{order_id}/reconciled")
def set_reconciled(order_id: str, reconciled_flag: bool = Body(embed=True, alias="reconciled")):
    """Mark or unmark an order as reconciled (in memory only)."""
    if order_id not in {o["orderId"] for o in data.load_orders()}:
        raise HTTPException(404, "Unknown order")
    if reconciled_flag:
        reconciled.add(order_id)
    else:
        reconciled.discard(order_id)
    return {"orderId": order_id, "reconciled": reconciled_flag}


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


app.mount("/static", StaticFiles(directory=STATIC), name="static")
