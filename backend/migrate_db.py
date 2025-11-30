"""
Database migration script to add new profile fields
"""
import sqlite3
import os

DB_PATH = "agrosky.db"

def migrate():
    """Add new profile fields to users table"""
    if not os.path.exists(DB_PATH):
        print("❌ Database file not found!")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get current columns
    cursor.execute("PRAGMA table_info(users)")
    existing_columns = [row[1] for row in cursor.fetchall()]
    print(f"📊 Existing columns: {existing_columns}")
    
    # Define new columns
    new_columns = {
        'full_name': 'TEXT',
        'farm_name': 'TEXT',
        'country': 'TEXT',
        'region': 'TEXT',
        'phone_number': 'TEXT',
        'preferred_units': 'TEXT DEFAULT "hectares"',
        'primary_crops': 'TEXT',  # Will store JSON
        'farming_type': 'TEXT',
        'irrigation_method': 'TEXT'
    }
    
    # Add missing columns
    added_count = 0
    for col_name, col_type in new_columns.items():
        if col_name not in existing_columns:
            try:
                sql = f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"
                print(f"➕ Adding column: {col_name}")
                cursor.execute(sql)
                added_count += 1
            except Exception as e:
                print(f"⚠️  Error adding {col_name}: {e}")
    
    conn.commit()
    conn.close()
    
    if added_count > 0:
        print(f"\n✅ Migration complete! Added {added_count} columns.")
    else:
        print("\n✅ All columns already exist!")
    
    # Verify
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(users)")
    final_columns = [row[1] for row in cursor.fetchall()]
    print(f"\n📊 Final columns: {final_columns}")
    conn.close()

if __name__ == "__main__":
    migrate()
