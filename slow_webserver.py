from datetime import datetime
from pathlib import Path
import http.server
import io
import logging
import os
import sys
import threading
import time

class SlowWebServer:
    """
    Wrapper around http.server to implement a slowed HTTP server for testing
    """
    PORT = 8080
    ADDRESS = "127.0.0.1"
    # bytes per second
    # Note: we don't currently fragment the response, as such ensure that
    #       a wait will be shorter than the socket's timeout
    BPS = 100_000.0

    class SlowHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
        class _SlowSocketWriter(io.BufferedIOBase):
            """
            A simple socket writer class to implement a bytes-per-second throttle
            Source of this comes from: https://github.com/python/cpython/blob/adedcfa06b553242d8033f6d9bebbcb3bc0dbb4d/Lib/socketserver.py#L839-L842
            """
            slow_state = {"current_bytes": 0, "last_checkpoint_bytes": 0, "last_checkpoint_time": datetime.now()}

            def __init__(self, sock):
                self._sock = sock
                self.slow_state["last_checkpoint_time"] = datetime.now()
                super().__init__()

            def write(self, b):
                with memoryview(b) as view:
                    self.slow_state["current_bytes"] += view.nbytes
                    bytes_delta = self.slow_state["current_bytes"] - self.slow_state["last_checkpoint_bytes"]
                    logging.getLogger("SlowSocketWriter").debug(self.slow_state)
                    delta_sec = (datetime.now() - self.slow_state["last_checkpoint_time"]).microseconds
                    sleep_sec = (bytes_delta / delta_sec) / (SlowWebServer.BPS / 1000) / 1000

                    logging.getLogger("SlowSocketWriter").info(f"Will be sleeping roughly {sleep_sec} seconds")
                    time.sleep(sleep_sec)

                    self.slow_state["last_checkpoint_time"] = datetime.now()
                    self.slow_state["last_checkpoint_bytes"] = self.slow_state["current_bytes"]
                    logging.getLogger("SlowSocketWriter").debug("Done sleeping")

                self._sock.sendall(b)
                with memoryview(b) as view:
                    return view.nbytes

        def setup(self):
            """
            Override http.server.SimpleHTTPRequestHandler.setup() to use our custom slow socket writer
            """
            self.connection = self.request
            if self.timeout is not None:
                self.connection.settimeout(self.timeout)
            if self.disable_nagle_algorithm:
                self.connection.setsockopt(socket.IPPROTO_TCP,
                                           socket.TCP_NODELAY, True)
            self.rfile = self.connection.makefile('rb', self.rbufsize)
            if self.wbufsize == 0:
                self.wfile = self._SlowSocketWriter(self.connection)
            else:
                self.wfile = self.connection.makefile('wb', self.wbufsize)

    # Implement methods to implement a context-manager https: // docs.python.org / 3 / reference / datamodel.html  # context-managers
    def __init__(self):
        handler = self.SlowHTTPRequestHandler
        logging.getLogger("SlowWebServer").info("Creating Web Server")
        self._server = http.server.HTTPServer((self.ADDRESS, self.PORT), handler)

    def __enter__(self):
        logging.getLogger("SlowWebServer").info("Starting Web Server")
        httpthread = threading.Thread(target=self._server.serve_forever)
        httpthread.start()
        return (self)

    def __exit__(self, exc_type, exc_value, traceback):
        logging.getLogger("SlowWebServer").info("Stopping Web Server")
        killerthread = threading.Thread(target=self._server.shutdown)
        killerthread.start()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.stderr.write("Need the bytes per-second you want to serve at as an integer.\n")
        sys.exit(2)
    bps = int(sys.argv[1])
    cwd = os.path.abspath(os.getcwd())
    print(f"Serving {cwd} at {bps:,} bytes per-second") 
    print(f"Server is reachable at http://{SlowWebServer.ADDRESS}:{SlowWebServer.PORT}") 
    SlowWebServer.BPS = bps
    handler = SlowWebServer.SlowHTTPRequestHandler
    http.server.HTTPServer((SlowWebServer.ADDRESS, SlowWebServer.PORT), handler).serve_forever()

