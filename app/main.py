from pathlib import Path

from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import data

STATIC = Path(__file__).resolve().parent / "static"

app = FastAPI(title="Amazon Order History")

# Reconciled order IDs. In-memory only: lasts while this server process runs, never written to disk.
reconciled: set[str] = set()


@app.get("/api/orders")
def list_orders(
    q: str = "",
    sort: str = Query("orderDate", pattern="^(" + "|".join(data.SORT_KEYS) + ")$"),
    dir: str = Query("desc", pattern="^(asc|desc)$"),
    show_reconciled: bool = False,
):
    """Orders (each with its transaction fields and items), reloaded from export-data on every call.

    Reconciled orders are hidden unless show_reconciled is true; hidden_count says how many were hidden.
    """
    orders = data.query_orders(data.load_orders(), q, sort, dir)
    for o in orders:
        o["reconciled"] = o["orderId"] in reconciled
    visible = orders if show_reconciled else [o for o in orders if not o["reconciled"]]
    return {"count": len(visible), "hidden_count": len(orders) - len(visible), "orders": visible}


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
