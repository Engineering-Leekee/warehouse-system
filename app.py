from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
import sqlite3
import os
from datetime import datetime
import pandas as pd

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "warehouse_secret_default_key_for_development")

# Database configuration for Render
DB_DIR = os.path.join(os.getcwd(), 'instance')
os.makedirs(DB_DIR, exist_ok=True)
DB_FILE = os.path.join(DB_DIR, "inventory.db")

# -------------------- DB INIT --------------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            part_number TEXT NOT NULL,
            location TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            date_in TEXT,
            last_updated TEXT,
            status TEXT DEFAULT 'Available'
        )
    """)
    conn.commit()
    conn.close()

init_db()

# -------------------- HELPERS --------------------
def query_db(query, args=(), one=False):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(query, args)
    rv = cur.fetchall()
    conn.commit()
    conn.close()
    return (rv[0] if rv else None) if one else rv

def update_quantity(part_number, location, change):
    row = query_db("SELECT * FROM inventory WHERE part_number=? AND location=?",
                   (part_number, location), one=True)
    if row:
        new_qty = row["quantity"] + change
        if new_qty < 0:
            return False
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        query_db("UPDATE inventory SET quantity=?, last_updated=? WHERE id=?",
                 (new_qty, now, row["id"]))
        return True
    return False

# -------------------- ROUTES --------------------
@app.route("/")
def index():
    rows = query_db("SELECT * FROM inventory ORDER BY part_number, location")
    inventory = {}
    for r in rows:
        part = r["part_number"]
        if part not in inventory:
            inventory[part] = []
        inventory[part].append(r)
    return render_template("index.html", inventory=inventory)

@app.route("/add", methods=["POST"])
def add_item():
    part_number = request.form["part_number"].strip()
    location = request.form["location"].strip()
    qty = int(request.form["quantity"])

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    existing = query_db("SELECT * FROM inventory WHERE part_number=? AND location=?",
                        (part_number, location), one=True)

    if existing:
        new_qty = existing["quantity"] + qty
        query_db("UPDATE inventory SET quantity=?, last_updated=? WHERE id=?",
                 (new_qty, now, existing["id"]))
    else:
        query_db("INSERT INTO inventory (part_number, location, quantity, date_in, last_updated, status) VALUES (?,?,?,?,?,?)",
                 (part_number, location, qty, now, now, "Available"))

    flash(f"Added {qty} of {part_number} at {location}", "success")
    return redirect(url_for("index"))

@app.route("/get_racks")
def get_racks():
    part_number = request.args.get("part_number", "").strip()
    rows = query_db("SELECT location, quantity, status FROM inventory WHERE part_number=? AND quantity>0",
                    (part_number,))
    return jsonify([dict(r) for r in rows])

@app.route("/remove_multiple", methods=["POST"])
def remove_multiple():
    part_number = request.form.get("part_number")
    remove_qtys = request.form.to_dict(flat=False)

    success = False
    for key, values in remove_qtys.items():
        if key.startswith("remove_qty["):
            location = key[len("remove_qty["):-1]
            try:
                qty = int(values[0])
            except:
                qty = 0
            if qty > 0:
                updated = update_quantity(part_number, location, -qty)
                if updated:
                    success = True

    if success:
        flash(f"Removed items from {part_number}", "success")
    else:
        flash("No items were removed (maybe invalid qty or Quarantine rack).", "error")

    return redirect(url_for("index"))

@app.route("/toggle_status", methods=["POST"])
def toggle_status():
    part_number = request.form["part_number"]
    location = request.form["location"]

    row = query_db("SELECT * FROM inventory WHERE part_number=? AND location=?",
                   (part_number, location), one=True)
    if row:
        new_status = "Quarantine" if (row["status"] or "Available") == "Available" else "Available"
        query_db("UPDATE inventory SET status=?, last_updated=? WHERE id=?",
                 (new_status, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), row["id"]))
        flash(f"{part_number} at {location} set to {new_status}", "success")
    else:
        flash("Part not found", "error")

    return redirect(url_for("index"))

# -------------------- EXPORT --------------------
@app.route("/export/csv")
def export_csv():
    rows = query_db("SELECT * FROM inventory")
    df = pd.DataFrame([dict(r) for r in rows])
    file = "inventory_export.csv"
    df.to_csv(file, index=False)
    return send_file(file, as_attachment=True)

@app.route("/export/excel")
def export_excel():
    rows = query_db("SELECT * FROM inventory")
    df = pd.DataFrame([dict(r) for r in rows])
    file = "inventory_export.xlsx"
    df.to_excel(file, index=False)
    return send_file(file, as_attachment=True)

# -------------------- MAIN --------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)