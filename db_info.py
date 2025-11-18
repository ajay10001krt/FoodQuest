import sqlite3

def show_db_structure(db_path="database/foodquest.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("\n📌 DATABASE STRUCTURE\n")

    # Fetch all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    if not tables:
        print("No tables found in database.")
        return

    for (table_name,) in tables:
        print(f"\n==============================")
        print(f"🗂 TABLE: {table_name}")
        print("==============================")

        # Get columns info
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()

        print("\n  📌 Columns:")
        for col in columns:
            cid, name, col_type, notnull, default, pk = col
            print(f"     - {name} ({col_type})"
                  f"{' NOT NULL' if notnull else ''}"
                  f"{' PRIMARY KEY' if pk else ''}"
                  f"{f' DEFAULT {default}' if default else ''}")

        # Get foreign keys
        cursor.execute(f"PRAGMA foreign_key_list({table_name})")
        fks = cursor.fetchall()

        if fks:
            print("\n  🔗 Foreign Keys:")
            for fk in fks:
                id, seq, table, from_col, to_col, on_update, on_delete, match = fk
                print(f"     - {from_col} → {table}({to_col})")
        else:
            print("\n  🔗 Foreign Keys: None")

    conn.close()
    print("\nDone.\n")

if __name__ == "__main__":
    show_db_structure()