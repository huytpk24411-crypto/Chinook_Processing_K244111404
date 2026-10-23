"""Run the HTML/CSS browser interface using the same MySQL and ML services."""
import argparse
import threading
import webbrowser
from web.application import WebApplication
from web.server import create_server


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--no-browser', action='store_true')
    parser.add_argument('--connect', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    application = WebApplication()
    try:
        server = create_server(application, args.port)
    except OSError:
        application.close()
        print('Port unavailable. Close the running copy or use --port 8766.')
        return 1
    url = f'http://127.0.0.1:{server.server_port}/'
    print(f'Chinook web: {url}', flush=True)
    print('Keep this terminal open. Press Ctrl+C to stop.', flush=True)
    application.connect()
    if not args.no_browser:
        threading.Timer(.6, webbrowser.open, args=(url,)).start()
    try:
        server.serve_forever(poll_interval=.2)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        application.close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
