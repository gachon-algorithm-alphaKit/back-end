import sqlite3
conn = sqlite3.connect('db.sqlite3')
with open('schema.txt', 'w') as f:
    for row in conn.execute('SELECT sql FROM sqlite_master WHERE type="table" AND name IN ("core_place", "core_campusedge", "core_placealias")'):
        f.write(row[0] + '\n\n')
