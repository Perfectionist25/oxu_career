import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# Check table structure
cursor.execute('PRAGMA table_info(accounts_employerprofile);')
rows = cursor.fetchall()
print("Table structure:")
for row in rows:
    print(row)

# Check current data
cursor.execute('SELECT id, industry FROM accounts_employerprofile LIMIT 10;')
rows = cursor.fetchall()
print("\nFirst 10 industry values:")
for row in rows:
    print(row)

conn.close()
