from django.db import connection
cursor = connection.cursor()
cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
tables = [row[0] for row in cursor.fetchall() if 'job' in row[0].lower()]
print(tables)
