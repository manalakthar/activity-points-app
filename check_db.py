import sqlite3
conn = sqlite3.connect('database.db')
conn.row_factory = sqlite3.Row

print('=== ADMINS ===')
admins = conn.execute('SELECT admin_id, name, email, password FROM admins').fetchall()
for a in admins:
    print('  id=%s, name=%s, email=%s, password=%s' % (a['admin_id'], a['name'], a['email'], a['password']))

print()
print('=== MENTORS ===')
mentors = conn.execute('SELECT mentor_id, name, email, password FROM mentors').fetchall()
for m in mentors:
    print('  id=%s, name=%s, email=%s, password=%s' % (m['mentor_id'], m['name'], m['email'], m['password']))

print()
print('=== COORDINATORS ===')
coords = conn.execute('SELECT coordinator_id, name, email, password, role FROM coordinators').fetchall()
for c in coords:
    print('  id=%s, name=%s, email=%s, password=%s, role=%s' % (c['coordinator_id'], c['name'], c['email'], c['password'], c['role']))

print()
print('=== STUDENTS (first 5) ===')
students = conn.execute('SELECT student_id, name, email, password FROM students LIMIT 5').fetchall()
for s in students:
    print('  id=%s, name=%s, email=%s, password=%s' % (s['student_id'], s['name'], s['email'], s['password']))

conn.close()
