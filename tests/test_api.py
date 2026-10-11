import json

from fastapi.testclient import TestClient

from app import data
from app.main import app

client = TestClient(app)

ORDER = {
    "orderId": "111-1",
    "orderDate": "2026-01-02",
    "totalAmount": 44.1,
    "currency": "USD",
    "items": [{"title": "USB Microphone", "asin": "B0X", "quantity": 2, "price": 19.95, "discount": 0, "itemUrl": "u"}],
    "orderStatus": "Delivered",
    "detailsUrl": "d",
    "promotions": [],
    "totalSavings": 0,
}


def write(tmp_path, name, orders):
    (tmp_path / name).write_text(json.dumps(orders), encoding="utf-8")


def test_loads_multiple_files_and_dedupes(tmp_path):
    write(tmp_path, "a.json", [ORDER, {**ORDER, "orderId": "111-2", "orderDate": "2026-02-01"}])
    write(tmp_path, "b.json", [{**ORDER, "totalAmount": 50.0}])
    orders = {o["orderId"]: o for o in data.load_orders(tmp_path)}
    assert set(orders) == {"111-1", "111-2"}
    assert orders["111-1"]["totalAmount"] == 50.0  # later file wins
    assert orders["111-1"]["items"][0]["lineTotal"] == 39.9


def test_search_by_item_and_amount(tmp_path):
    write(tmp_path, "a.json", [ORDER, {**ORDER, "orderId": "111-2", "totalAmount": 9.99, "items": []}])
    orders = data.load_orders(tmp_path)
    assert [o["orderId"] for o in data.query_orders(orders, "microphone")] == ["111-1", "111-2"][:1]
    assert [o["orderId"] for o in data.query_orders(orders, "$44.10")] == ["111-1"]
    assert [o["orderId"] for o in data.query_orders(orders, "9.99")] == ["111-2"]
    assert data.query_orders(orders, "nothing") == []


def test_sorting(tmp_path):
    write(tmp_path, "a.json", [ORDER, {**ORDER, "orderId": "111-2", "totalAmount": 9.99}])
    orders = data.load_orders(tmp_path)
    asc = data.query_orders(orders, sort="totalAmount", direction="asc")
    assert [o["orderId"] for o in asc] == ["111-2", "111-1"]


def test_api_and_index():
    r = client.get("/api/orders", params={"sort": "totalAmount", "dir": "asc"})
    assert r.status_code == 200 and r.json()["count"] == len(r.json()["orders"])
    assert client.get("/api/orders", params={"sort": "bogus"}).status_code == 422
    assert "Amazon Order History" in client.get("/").text


def test_tax_estimate(tmp_path):
    promo = {**ORDER, "orderId": "111-2", "totalSavings": 5, "promotions": [{"description": "x", "amount": 5}]}
    write(tmp_path, "a.json", [ORDER, promo])
    orders = {o["orderId"]: o for o in data.load_orders(tmp_path)}
    assert orders["111-1"]["taxEstimate"] == 4.2  # 44.10 - 2 * 19.95
    assert orders["111-2"]["taxEstimate"] is None
    for d in ("asc", "desc"):  # orders without an estimate sort last either way
        assert data.query_orders(list(orders.values()), sort="taxEstimate", direction=d)[-1]["orderId"] == "111-2"


def test_reconciled_hide_show_and_unknown():
    from app import main

    main.reconciled.clear()
    all_ids = [o["orderId"] for o in client.get("/api/orders").json()["orders"]]
    assert all_ids, "needs sample data in export-data/"
    oid = all_ids[0]
    try:
        assert client.put(f"/api/orders/{oid}/reconciled", json={"reconciled": True}).status_code == 200
        hidden = client.get("/api/orders").json()
        assert oid not in [o["orderId"] for o in hidden["orders"]] and hidden["hidden_count"] == 1
        shown = client.get("/api/orders", params={"show_reconciled": True}).json()
        assert [o["reconciled"] for o in shown["orders"] if o["orderId"] == oid] == [True]
        client.put(f"/api/orders/{oid}/reconciled", json={"reconciled": False})
        assert client.get("/api/orders").json()["hidden_count"] == 0
        assert client.put("/api/orders/nope/reconciled", json={"reconciled": True}).status_code == 404
    finally:
        main.reconciled.clear()


def test_partial_amount_with_trailing_dot(tmp_path):
    write(tmp_path, "a.json", [{**ORDER, "totalAmount": 34.81, "items": []}])
    orders = data.load_orders(tmp_path)
    for q in ("34", "34.", "34.8", "34.81", "$34.81"):
        assert len(data.query_orders(orders, q)) == 1, q
    assert data.query_orders(orders, "35.") == []
