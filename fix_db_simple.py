import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# Disable foreign keys temporarily
cursor.execute('PRAGMA foreign_keys = OFF;')

# Update invalid industry values to NULL
cursor.execute('UPDATE accounts_employerprofile SET industry = NULL WHERE industry IN ("Soha haqida ma`lumot", "");')

# Commit the changes
conn.commit()

# Re-enable foreign keys
cursor.execute('PRAGMA foreign_keys = ON;')

# Check the results
cursor.execute('SELECT id, industry FROM accounts_employerprofile WHERE industry IS NULL;')
rows = cursor.fetchall()
print(f'After update: {len(rows)} profiles have NULL industry')

conn.close()
