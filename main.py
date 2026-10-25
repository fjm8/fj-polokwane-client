from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
import sqlite3, random, hashlib
from datetime import datetime

app = FastAPI()
DB = "client.db"

def init_db():
    con = sqlite3.connect(DB)
    con.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT)")
    con.execute("""CREATE TABLE IF NOT EXISTS deliveries (
        code TEXT PRIMARY KEY, 
        username TEXT, 
        client_name TEXT, 
        address TEXT, 
        product_name TEXT,
        product_type TEXT,
        quantity TEXT,
        created_at TEXT)""")
    con.close()
init_db()

def hash_pw(p): return hashlib.sha256(p.encode()).hexdigest()

@app.get("/api/verify/{code}")
def api_verify(code: str):
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute("SELECT client_name, address, product_name, product_type, quantity FROM deliveries WHERE code=?", (code,))
    row = cur.fetchone()
    con.close()
    if row:
        return {"status": "valid", "client_name": row[0], "address": row[1], "product_name": row[2], "product_type": row[3], "quantity": row[4], "code": code}
    return {"status": "invalid"}

def styled_page(content):
    return f"""
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body{{font-family: 'Segoe UI', sans-serif; background:#f5f7fb; margin:0; padding:15px;}}
        .card{{max-width:450px; margin:20px auto; background:white; padding:25px; border-radius:16px; box-shadow:0 4px 20px rgba(0,0,0,0.08);}}
        h2{{color:#1a3c6e; margin-top:0;}} input{{width:100%; padding:12px; margin:8px 0; border:1px solid #d1d5db; border-radius:10px; box-sizing:border-box; font-size:15px;}}
        button{{width:100%; padding:12px; background:#1a3c6e; color:white; border:none; border-radius:10px; font-size:16px; font-weight:bold; margin-top:10px;}}
        .label{{font-size:13px; font-weight:600; color:#374151; margin-top:12px; display:block;}}
        .code-box{{background:#e6f0ff; border:2px dashed #1a3c6e; padding:15px; border-radius:12px; text-align:center; margin-top:15px}}
    </style></head><body>{content}</body></html>
    """

@app.get("/", response_class=HTMLResponse)
def home():
    content = """
    <div class="card"><h2>🚚 FJ Polokwane</h2><p style="color:#6b7280">Client Portal</p>
        <form action="/register" method="post"><h3>Create Account</h3>
        <span class="label">Username</span><input name="username" required>
        <span class="label">Password</span><input name="password" type="password" required><button>Create Account</button></form><hr>
        <form action="/login" method="post"><h3>Login</h3>
        <span class="label">Username</span><input name="username" required>
        <span class="label">Password</span><input name="password" type="password" required><button style="background:#0f9d58">Login</button></form></div>
    """
    return HTMLResponse(styled_page(content))

@app.post("/register")
def register(username: str = Form(...), password: str = Form(...)):
    try:
        con = sqlite3.connect(DB)
        con.execute("INSERT INTO users VALUES (NULL,?,?)", (username, hash_pw(password)))
        con.commit(); con.close()
        return HTMLResponse(styled_page(f"<div class='card'><h2>✓ Created</h2><p>{username}</p><a href='/'>Login</a></div>"))
    except:
        return HTMLResponse(styled_page("<div class='card'><h2>Taken</h2><a href='/'>Back</a></div>"))

@app.post("/login", response_class=HTMLResponse)
def login(username: str = Form(...), password: str = Form(...)):
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute("SELECT * FROM users WHERE username=? AND password=?", (username, hash_pw(password)))
    u = cur.fetchone(); con.close()
    if not u: return HTMLResponse(styled_page("<div class='card'><h2>Invalid</h2><a href='/'>Back</a></div>"))
    content = f"""
    <div class="card"><h2>Welcome, {username} 👋</h2>
        <form action="/create-delivery" method="post">
            <input name="username" value="{username}" type="hidden">
            <span class="label">Client / Receiver Name</span><input name="client_name" required placeholder="e.g. Shoprite Polokwane">
            <span class="label">Delivery Address</span><input name="address" required placeholder="123 Market St">
            <hr><h3>📦 Product Details</h3>
            <span class="label">1. Product Name</span><input name="product_name" placeholder="e.g. Rice" required>
            <span class="label">2. What is the product? (Description/Type)</span><input name="product_type" placeholder="e.g. 25kg White Rice - Fragile" required>
            <span class="label">3. Quantity</span><input name="quantity" placeholder="e.g. 100 Bags" required>
            <button>Create & Get CODE</button>
        </form></div>
    """
    return HTMLResponse(styled_page(content))

@app.post("/create-delivery", response_class=HTMLResponse)
def create_delivery(username: str = Form(...), client_name: str = Form(...), address: str = Form(...), product_name: str = Form(...), product_type: str = Form(...), quantity: str = Form(...)):
    code = f"FJ-{random.randint(100000,999999)}"
    con = sqlite3.connect(DB)
    con.execute("INSERT INTO deliveries VALUES (?,?,?,?,?,?,?,?)", (code, username, client_name, address, product_name, product_type, quantity, datetime.now().isoformat()))
    con.commit(); con.close()
    content = f"""
    <div class="card"><h2>✓ Delivery Created!</h2>
        <div class="code-box"><p style="margin:0;color:#6b7280">Your CODE</p><h1 style="color:#1a3c6e">{code}</h1><p>Give CODE to Warehouse</p></div>
        <div style="margin-top:15px;line-height:1.6;font-size:14px"><b>Client:</b> {client_name}<br><b>1. Name:</b> {product_name}<br><b>2. Type:</b> {product_type}<br><b>3. Qty:</b> {quantity}</div>
        <br><a href='/'><button style="background:#6b7280">Back</button></a></div>
    """
    return HTMLResponse(styled_page(content))
