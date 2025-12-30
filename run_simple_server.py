import http.server
import socketserver
import webbrowser

PORT = 8080

Handler = http.server.SimpleHTTPRequestHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"✅ Simple frontend served at http://localhost:{PORT}")
    print("📁 Open simple_frontend.html in your browser")
    webbrowser.open(f'http://localhost:{PORT}/simple_frontend.html')
    httpd.serve_forever()
