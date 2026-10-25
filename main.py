from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
import sqlite3, random
from datetime import datetime

app = FastAPI()
DB = "client.db"

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS orders
                 (code TEXT PRIMARY KEY, client_name TEXT, client_address TEXT,
                  manufacturer TEXT, product_name TEXT, product_type TEXT,
                  quantity INTEGER, individual_weight_kg REAL, products_per_pallet INTEGER,
                  pallet_weight_kg REAL, pallet_height_cm REAL, total_pallets REAL,
                  created_at TIMESTAMP)''')
    conn.commit()
    conn.close()
init_db()

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html><body style="font-family:Arial; max-width:800px; margin:auto; padding:20px">
    <h2>FJ Polokwane - Client Delivery Order</h2>
    <form method="post" action="/create-order" style="display:grid; gap:12px">
        <input name="client_name" placeholder="Client Name" required>
        <input name="client_address" placeholder="Client Address" required>
        <input name="manufacturer" placeholder="Manufacturer e.g. Tiger Brands" required>
        <input name="product_name" placeholder="Product Name e.g. Rice" required>
        <input name="product_type" placeholder="Product Type e.g. 25kg White Rice" required>
        <input type="number" name="quantity" placeholder="Total Quantity (total bags)" required>
        <h3>Weight & Height (NEW)</h3>
        <label>Individual Weight (kg): <input type="number" step="0.01" name="individual_weight_kg" required></label>
        <label>Products Per Pallet: <input type="number" name="products_per_pallet" required></label>
        <label>Pallet Height (cm): <input type="number" step="0.1" name="pallet_height_cm" required></label>
        <button type="submit">Generate FJ-CODE</button>
    </form></body></html>
    """

@app.post("/create-order", response_class=HTMLResponse)
def create_order(client_name: str = Form(...), client_address: str = Form(...),
                 manufacturer: str = Form(...), product_name: str = Form(...),
                 product_type: str = Form(...), quantity: int = Form(...),
                 individual_weight_kg: float = Form(...), products_per_pallet: int = Form(...),
                 pallet_height_cm: float = Form(...)):
    pallet_weight = individual_weight_kg * products_per_pallet
    total_pallets = quantity / products_per_pallet if products_per_pallet else 0
    code = f"FJ-{random.randint(100000,999999)}"
    conn = sqlite3.connect(DB)
    conn.execute("INSERT INTO orders VALUES (?,?,?,?,?,?,?,?,?,?,?, ?, ?)",
                 (code, client_name, client_address, manufacturer, product_name, product_type,
                  quantity, individual_weight_kg, products_per_pallet, pallet_weight, pallet_height_cm, total_pallets, datetime.now()))
    conn.commit()
    conn.close()
    rule = 'HEAVY -> M1/M2 or Level 1 ONLY' if pallet_weight >= 800 else 'Medium -> Level 1-2' if pallet_weight >=500 else 'Light -> Any Level'
    return f"""<html><body style="padding:20px"><h2>Order {code} Created</h2><p>Pallet Weight: {pallet_weight} kg</p><p>Pallets: {total_pallets:.2f}</p><p>Rule: {rule}</p><a href="/">Back</a></body></html>"""

@app.get("/api/verify/{code}")
def verify(code: str):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM orders WHERE code=?", (code,)).fetchone()
    conn.close()
    return {"valid": False} if not row else {"valid": True, **dict(row)}
