from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import sqlite3, uuid, hashlib
from datetime import datetime

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
DB="client.db"

def get_db():
    conn=sqlite3.connect(DB, check_same_thread=False)
    conn.execute("CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, name TEXT, company TEXT, phone TEXT, email TEXT UNIQUE, password TEXT, created TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS deliveries (code TEXT PRIMARY KEY, user_id TEXT, sender_name TEXT, sku TEXT, product TEXT, qty INTEGER, truck_plate TEXT, status TEXT, created TEXT)")
    return conn

def hash_pw(p): return hashlib.sha256(p.encode()).hexdigest()
def get_user(req: Request):
    email=req.cookies.get("email")
    if not email: return None
    conn=get_db()
    row=conn.execute("SELECT id, name, company, phone, email FROM users WHERE email=?", (email,)).fetchone()
    conn.close()
    return row

@app.get("/", response_class=HTMLResponse)
def index(req: Request):
    user=get_user(req)
    if not user:
        return """<html><head><meta name='viewport' content='width=device-width,initial-scale=1'><style>
        body{font-family:sans-serif;background:#f5f7fa;padding:15px;max-width:420px;margin:auto} .card{background:white;border-radius:12px;padding:18px;margin:12px 0;box-shadow:0 2px 8px rgba(0,0,0,0.08)}
        input{width:100%;padding:13px;margin:6px 0;border:1px solid #ddd;border-radius:8px;box-sizing:border-box} button{width:100%;padding:14px;border:none;border-radius:8px;font-weight:bold;color:white;background:#0b5ed7}
        .top{background:#0b5ed7;color:white;padding:22px;border-radius:12px;text-align:center}
        </style></head><body><div class='top'><h2>FJ Logistics</h2><p>Client Delivery Portal</p><small>Polokwane Warehouse</small></div>
        <div class='card'><h3>Create Account</h3><form method='post' action='/signup'><input name='name' placeholder='Full Name' required><input name='company' placeholder='Company Name'><input name='phone' placeholder='Phone / WhatsApp' required><input name='email' type='email' placeholder='Email for login' required><input name='password' type='password' placeholder='Create Password' required><button>Create Account</button></form></div>
        <div class='card'><h3>Login</h3><form method='post' action='/login'><input name='email' type='email' placeholder='Email' required><input name='password' type='password' placeholder='Password' required><button style='background:#198754'>Login</button></form></div>
        </body></html>"""

    conn=get_db()
    rows=conn.execute("SELECT code, sender_name, sku, product, qty, status, created FROM deliveries WHERE user_id=? ORDER BY created DESC", (user[0],)).fetchall()
    conn.close()
    list_html="".join([f"<tr><td><b>{r[0]}</b><br><small>{r[6][:10]}</small></td><td>{r[2]}<br>{r[3]} x {r[4]}</td><td>{r[5]}<br><a href='/code/{r[0]}'>View CODE</a></td></tr>" for r in rows])

    return f"""<html><head><meta name='viewport' content='width=device-width'><style>
    body{{font-family:sans-serif;padding:10px;background:#f5f7fa}} .top{{background:#0b5ed7;color:white;padding:15px;border-radius:10px}} .card{{background:white;padding:14px;margin:10px 0;border-radius:10px}} input{{width:100%;padding:12px;margin:5px 0;border:1px solid #ddd;border-radius:6px;box-sizing:border-box}} button{{width:100%;padding:14px;background:#0b5ed7;color:white;border:none;border-radius:8px;font-weight:bold}} table{{width:100%;border-collapse:collapse}} td{{border:1px solid #eee;padding:8px;font-size:12px;background:white}}
    </style></head><body><div class='top'><h3>Hello, {user[1]}</h3><small>{user[4]} | {user[2]} | <a href='/logout' style='color:white'>Logout</a></small></div>
    <div class='card' style='border:2px solid #0b5ed7'><h4>📦 What are you sending to warehouse?</h4><form method='post' action='/new_delivery'>
    <input name='sender_name' value='{user[1]}' placeholder='Sender Name on Parcel' required><input name='sku' placeholder='SKU e.g. MAIZE-25KG' required><input name='product' placeholder='Product Name' required><input name='qty' type='number' min='1' value='1' required><input name='truck_plate' placeholder='Truck Plate (optional)'><button>Generate Delivery CODE</button></form></div>
    <div class='card'><h4>Your Delivery CODEs - Give this CODE to Warehouse</h4><table><tr><th>CODE</th><th>Product</th><th>Status</th></tr>{list_html if list_html else "<tr><td colspan=3>No deliveries yet</td></tr>"}</table></div>
    </body></html>"""

@app.post("/signup")
def signup(name: str = Form(...), company: str = Form(""), phone: str = Form(...), email: str = Form(...), password: str = Form(...)):
    conn=get_db()
    try:
        conn.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)",(str(uuid.uuid4())[:6], name, company, phone, email.lower(), hash_pw(password), datetime.now().isoformat()))
        conn.commit(); conn.close()
    except:
        conn.close()
        return HTMLResponse("<h3>Email exists. Login.</h3><a href='/'>Back</a>")
    resp=RedirectResponse("/", 302); resp.set_cookie("email", email.lower(), max_age=2592000); return resp

@app.post("/login")
def login(email: str = Form(...), password: str = Form(...)):
    conn=get_db()
    row=conn.execute("SELECT email FROM users WHERE email=? AND password=?", (email.lower(), hash_pw(password))).fetchone()
    conn.close()
    if not row: return HTMLResponse("<h3>Wrong email/password</h3><a href='/'>Back</a>")
    resp=RedirectResponse("/", 302); resp.set_cookie("email", email.lower(), max_age=2592000); return resp

@app.get("/logout")
def logout():
    resp=RedirectResponse("/", 302); resp.delete_cookie("email"); return resp

@app.post("/new_delivery", response_class=HTMLResponse)
def new_delivery(req: Request, sender_name: str = Form(...), sku: str = Form(...), product: str = Form(...), qty: int = Form(...), truck_plate: str = Form("")):
    user=get_user(req)
    if not user: return RedirectResponse("/", 302)
    code=f"FJ-{datetime.now().strftime('%m%d')}-{str(uuid.uuid4())[:6].upper()}"
    conn=get_db()
    conn.execute("INSERT INTO deliveries VALUES (?,?,?,?,?,?,?,?,?)",(code, user[0], sender_name, sku.upper(), product, qty, truck_plate.upper(), "READY FOR WAREHOUSE", datetime.now().isoformat()))
    conn.commit(); conn.close()
    return RedirectResponse(f"/code/{code}", 302)

@app.get("/code/{code}", response_class=HTMLResponse)
def show_code(code: str):
    conn=get_db()
    row=conn.execute("SELECT code, sender_name, sku, product, qty, truck_plate, status, created, user_id FROM deliveries WHERE code=?", (code.upper(),)).fetchone()
    if not row:
        conn.close()
        return HTMLResponse("Code not found")
    user=conn.execute("SELECT name, company, phone, email FROM users WHERE id=?", (row[8],)).fetchone()
    conn.close()
    return f"""<html><head><meta name='viewport' content='width=device-width'><style>body{{font-family:sans-serif;padding:15px;text-align:center;background:#f5f7fa}} .card{{background:white;padding:20px;border-radius:12px;max-width:400px;margin:auto}} .code{{background:#0b5ed7;color:white;padding:20px;border-radius:12px;font-size:28px;font-weight:bold;letter-spacing:2px}}</style></head><body>
    <div class='card'><h3>Delivery CODE</h3><div class='code'>{row[0]}</div><p><img src='https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={row[0]}'></p>
    <div style='text-align:left;background:#f8f9fa;padding:12px;border-radius:8px'>
    <b>From:</b> {user[0] if user else ''} ({user[1] if user else ''})<br>Phone: {user[2] if user else ''}<br>
    <b>Sender on Parcel:</b> {row[1]}<br><b>Product:</b> {row[3]} ({row[2]})<br><b>Qty:</b> {row[4]}<br><b>Truck:</b> {row[5]}<br><b>Status:</b> {row[6]}<br><small>{row[7][:16]}</small>
    </div><p><b>Give this CODE to warehouse. They enter it in INTAKE system to see your details.</b></p><a href='/'>Back to Dashboard</a></div></body></html>"""

@app.get("/api/order/{code}")
def api(code: str):
    conn=get_db()
    row=conn.execute("SELECT code, sender_name, sku, product, qty, truck_plate, status, created, user_id FROM deliveries WHERE code=?", (code.upper(),)).fetchone()
    if not row:
        conn.close()
        return {"found": False}
    user=conn.execute("SELECT name, company, phone, email FROM users WHERE id=?", (row[8],)).fetchone()
    conn.close()
    return {"found": True, "code": row[0], "client_name": row[1], "sku": row[2], "product_name": row[3], "qty": row[4], "truck_plate": row[5], "status": row[6], "created": row[7], "account_name": user[0] if user else "", "company": user[1] if user else "", "phone": user[2] if user else "", "email": user[3] if user else ""}
