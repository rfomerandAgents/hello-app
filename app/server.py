#!/usr/bin/env python3
"""Simple HTTP server for the Hello App."""

import http.server
import socketserver
import os

PORT = 8080
DIRECTORY = os.path.dirname(os.path.abspath(__file__))


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)


def main():
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"🚀 Server running at http://localhost:{PORT}")
        print("Press Ctrl+C to stop")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Server stopped")


if __name__ == "__main__":
    main()
