import http.server
import socketserver
html_directory="D:\Phone_Street\templates\Home.html"
port=8080
Handler=http.server.SimpleHTTPRequestHandler
with socketserver.TCPServer(("D:\Phone_Street\templates\Home.html",port),Handler) as httpd:
    print(f"Serving HTML from {html_directory} at http://localhost:{port}")
    httpd.serve_forever()