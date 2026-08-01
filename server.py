import os
import json
import sqlite3
import datetime
import urllib.parse
from http.server import SimpleHTTPRequestHandler, HTTPServer

DB_FILE = 'database.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            website TEXT,
            service TEXT,
            message TEXT,
            date TEXT
        )
    ''')
    conn.commit()
    conn.close()

class CustomHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        # Handle /admin route
        if self.path == '/admin':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute('SELECT * FROM contacts ORDER BY id DESC')
            rows = c.fetchall()
            conn.close()
            
            html = """
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <title>Admin Dashboard - WebSio</title>
                <style>
                    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: #F3F4F6; margin: 0; padding: 20px; color: #111; }
                    .container { max-width: 1200px; margin: 0 auto; background: #fff; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
                    h1 { margin-top: 0; font-size: 24px; color: #111; }
                    table { width: 100%; border-collapse: collapse; margin-top: 20px; }
                    th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #E5E7EB; }
                    th { background-color: #F9FAFB; font-weight: 600; color: #6B7280; text-transform: uppercase; font-size: 12px; }
                    td { font-size: 14px; }
                    .empty { text-align: center; color: #6B7280; padding: 40px; font-style: italic; }
                    .badge { background: #E0E7FF; color: #4338CA; padding: 4px 8px; border-radius: 999px; font-size: 12px; font-weight: 500; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Contact Submissions Dashboard</h1>
                    <table>
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Name</th>
                                <th>Email</th>
                                <th>Website</th>
                                <th>Service</th>
                                <th>Message</th>
                            </tr>
                        </thead>
                        <tbody>
            """
            if not rows:
                html += '<tr><td colspan="6" class="empty">No contact submissions yet.</td></tr>'
            else:
                for r in rows:
                    date = r[6] if r[6] else 'N/A'
                    name = r[1]
                    email = f'<a href="mailto:{r[2]}">{r[2]}</a>' if r[2] else ''
                    website = f'<a href="{r[3]}" target="_blank">{r[3]}</a>' if r[3] else ''
                    service = f'<span class="badge">{r[4]}</span>' if r[4] else ''
                    message = r[5].replace('\\n', '<br>') if r[5] else ''
                    html += f'<tr><td>{date}</td><td>{name}</td><td>{email}</td><td>{website}</td><td>{service}</td><td>{message}</td></tr>'
            
            html += """
                        </tbody>
                    </table>
                </div>
            </body>
            </html>
            """
            self.wfile.write(html.encode('utf-8'))
            return

        # Simple URL rewriting for directories without trailing slash
        

        # Call the parent class for standard file serving
        return super().do_GET()

    def do_POST(self):
        if self.path == '/api/contact':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'Invalid JSON')
                return

            name = data.get('name', '')
            email = data.get('email', '')
            website = data.get('website', '')
            service = data.get('service', '')
            message = data.get('message', '')
            date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute('INSERT INTO contacts (name, email, website, service, message, date) VALUES (?, ?, ?, ?, ?, ?)',
                      (name, email, website, service, message, date_str))
            conn.commit()
            conn.close()

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'success'}).encode('utf-8'))
            return

        self.send_response(404)
        self.end_headers()

if __name__ == '__main__':
    init_db()
    PORT = 8080
    server = HTTPServer(('', PORT), CustomHandler)
    print(f"Custom server running on http://localhost:{PORT}")
    print(f"Admin Dashboard available at http://localhost:{PORT}/admin")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
