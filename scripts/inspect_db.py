import sqlite3

def main():
    conn = sqlite3.connect("shivi_local.db")
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall() if not r[0].startswith("sqlite_")]
    counts = {}
    for t in tables:
        cur.execute(f"SELECT count(*) FROM {t}")
        counts[t] = cur.fetchone()[0]
    print("Database Table Counts:", counts)

if __name__ == "__main__":
    main()
