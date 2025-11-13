import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# First, alter the table to make industry nullable
cursor.execute('PRAGMA foreign_keys = OFF;')

# Alter the column to be nullable (SQLite doesn't support ALTER COLUMN directly, so we need to recreate)
cursor.execute('''
CREATE TABLE accounts_employerprofile_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name VARCHAR(255) NOT NULL,
    company_logo VARCHAR(100),
    company_description TEXT NOT NULL,
    company_email VARCHAR(254) NOT NULL,
    company_phone VARCHAR(128),
    company_website VARCHAR(200) NOT NULL,
    company_linkedin VARCHAR(200) NOT NULL,
    company_telegram VARCHAR(200) NOT NULL,
    company_size VARCHAR(20) NOT NULL,
    industry VARCHAR(255),
    founded_year INTEGER,
    headquarters VARCHAR(255) NOT NULL,
    jobs_posted INTEGER UNSIGNED NOT NULL,
    total_views INTEGER UNSIGNED NOT NULL,
    is_verified BOOL NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    user_id BIGINT NOT NULL REFERENCES accounts_customuser(id) DEFERRABLE INITIALLY DEFERRED
);
''')

# Copy data from old table to new table
cursor.execute('''
INSERT INTO accounts_employerprofile_new
SELECT * FROM accounts_employerprofile;
''')

# Drop old table
cursor.execute('DROP TABLE accounts_employerprofile;')

# Rename new table
cursor.execute('ALTER TABLE accounts_employerprofile_new RENAME TO accounts_employerprofile;')

# Now update the invalid values
cursor.execute("UPDATE accounts_employerprofile SET industry = NULL WHERE industry IN ('Soha haqida ma`lumot', '');")

# Commit the changes
conn.commit()

# Re-enable foreign keys
cursor.execute('PRAGMA foreign_keys = ON;')

# Check the results
cursor.execute('SELECT id, industry FROM accounts_employerprofile WHERE industry IS NULL;')
rows = cursor.fetchall()
print(f'After update: {len(rows)} profiles have NULL industry')

conn.close()
