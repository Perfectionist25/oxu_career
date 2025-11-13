import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# Disable foreign key constraints temporarily
cursor.execute('PRAGMA foreign_keys = OFF;')

# Check current invalid values
cursor.execute('SELECT id, industry FROM accounts_employerprofile WHERE industry IN ("Soha haqida ma`lumot", "")')
rows = cursor.fetchall()
print('Invalid industry values before update:', rows)

# Update invalid values to NULL
cursor.execute('UPDATE accounts_employerprofile SET industry = NULL WHERE industry IN ("Soha haqida ma`lumot", "")')
conn.commit()

# Re-enable foreign key constraints
cursor.execute('PRAGMA foreign_keys = ON;')

# Verify the update
cursor.execute('SELECT id, industry FROM accounts_employerprofile WHERE industry IS NULL')
rows = cursor.fetchall()
print('After update:', len(rows), 'profiles have NULL industry')

conn.close()
