import sqlite3, json, os

db_path = os.environ.get('HERMES_KANBAN_DB', '/opt/data/kanban/boards/dora-rag/kanban.db')
print(f'DB: {db_path}')
print(f'EXISTS: {os.path.exists(db_path)}')
db = sqlite3.connect(db_path)
db.row_factory = sqlite3.Row

# List tables
tables = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print(f'TABLES: {tables}')

# Get task
row = db.execute('SELECT * FROM tasks WHERE id = ?', ('t_9b94ae6b',)).fetchone()
if row:
    print(json.dumps(dict(row), indent=2, default=str))
else:
    print('Task not found - checking available tasks')
    for r in db.execute('SELECT id, title, status FROM tasks LIMIT 20'):
        print(json.dumps(dict(r), default=str))

# Get comments
print('\n--- COMMENTS ---')
for r in db.execute('SELECT * FROM comments WHERE task_id = ?', ('t_9b94ae6b',)):
    print(json.dumps(dict(r), indent=2, default=str))

db.close()
