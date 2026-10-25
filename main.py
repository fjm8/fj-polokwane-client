from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
import sqlite3, random, os, hashlib
from datetime import datetime

app = FastAPI()
DB = "client.db"

def init_db():
    con = sqlite3.connect(DB)
    con.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT)")
    con.execute("CREATE TABLE IF NOT EXISTS deliveries (code TEXT PRIMARY KEY, username TEXT, client_name TEXT, address TEXT, items TEXT, created_at TEXT)")
    con.close()
init_db()

def hash_pw(p): return hashlib.sha256(p.encode()).hexdigest()

# Public API for Warehouse to verify - NO LOGIN NEEDED
@app.get("/api/verify/{code}")
def api_verify(code: str):
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute("SELECT client_name, address, items, username FROM deliveries WHERE code=?", (code,))
    row = cur.fetchone()
    con.close()
    if row:
        return {"status": "valid", "client_name": row[0], "address": row[1], "items": row[2], "username": row[3], "code": code}
    return {"status": "invalid"}

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html><body style="font-family:sans-serif;padding:20px">
    <h2>FJ Client Portal</h2>
    <form action="/register" method="post"><h3>Create Account</h3>
    <input name="username" placeholder="username" required><br><br>
    <input name="password" type="password" placeholder="password" required><br><br>
    <button>Create Account</button></form><hr>
    <form action="/login" method="post"><h3>Login</h3>
    <input name="username" placeholder="username" required><br><br>
    <input name="password" type="password" placeholder="password" required><br><br>
    <button>Login</button></form>
    </body></html>
    """

@app.post("/register")
def register(username: str = Form(...), password: str = Form(...)):
    try:
        con = sqlite3.connect(DB)
        con.execute("INSERT INTO users VALUES (NULL,?,?)", (username, hash_pw(password)))
        con.commit(); con.close()
        return HTMLResponse(f"Account created for {username}. <a href='/'>Go Back</a>")
    except:
        return HTMLResponse("Username taken. <a href='/'>Back</a>")

@app.post("/login", response_class=HTMLResponse)
def login(username: str = Form(...), password: str = Form(...)):
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute("SELECT * FROM users WHERE username=? AND password=?", (username, hash_pw(password)))
    u = cur.fetchone()
    con.close()
    if not u:
        return HTMLResponse("Invalid login. <a href='/'>Back</a>")
    return HTMLResponse(f"""
    <html><body style="font-family:sans-serif;padding:20px">
    <h2>Welcome {username}</h2>
    <form action="/create-delivery" method="post">
    <h3>Create Delivery</h3>
    <input name="username" value="{username}" type="hidden">
    Client Name: <input name="client_name" required><br><br>
    Address: <input name="address" required><br><br>
    Items: <input name="items" placeholder="e.g. 10x Rice 25kg" required><br><br>
    <button>Create & Get CODE</button>
    </form>
    </body></html>
    """)

@app.post("/create-delivery", response_class=HTMLResponse)
def create_delivery(username: str = Form(...), client_name: str = Form(...), address: str = Form(...), items: str = Form(...)):
    code = f"FJ-{random.randint(100000,999999)}"
    con = sqlite3.connect(DB)
    con.execute("INSERT INTO deliveries VALUES (?,?,?,?,?,?)", (code, username, client_name, address, items, datetime.now().isoformat()))
    con.commit(); con.close()
    return HTMLResponse(f"<h1>Delivery Created!</h1><h2>CODE: {code}</h2><p>Client: {client_name}<br>Address: {address}<br>Items: {items}</p><p>Give this CODE to Warehouse.</p><a href='/'>Home</a>")
