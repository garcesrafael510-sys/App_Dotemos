import sqlite3
import os

DB_PATH = r"d:\Documents\APPTextil\proy_textil\TEXTILES_XYZ_SCHEDULER\data\textil_scheduler.db"

def check():
    if not os.path.exists(DB_PATH):
        print(f"DB not found at {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("--- BOM_MASTER REFERENCIAS ---")
    cursor.execute("SELECT DISTINCT REFERENCIA FROM BOM_MASTER")
    print(cursor.fetchall())
    
    print("\n--- ORDERS_LOG ITEMS ---")
    cursor.execute("SELECT OP_UNIQUE_ID, DETALLE_JSON FROM ORDERS_LOG")
    rows = cursor.fetchall()
    for row in rows:
        print(f"Order: {row[0]} | Detail: {row[1]}")
    
    conn.close()

if __name__ == "__main__":
    check()
