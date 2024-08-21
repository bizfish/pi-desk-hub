from http.server import BaseHTTPRequestHandler, HTTPServer
import hub_constants

# Simulate the state of the LED
led_state = "LOW"


class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global led_state

        # Parse the path to determine the action
        if self.path == "/L":
            led_state = "LOW"
            self.respond({"status": "LED set to LOW"})
            print("LOW")
        elif self.path == "/H":
            led_state = "HIGH"
            self.respond({"status": "LED set to HIGH"})
            print("HIGH")
        else:
            self.respond({"status": "Invalid request"}, 404)
            print("INVALID")

    def respond(self, content, status_code=200):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(str(content).encode())


def run(server_class=HTTPServer, handler_class=RequestHandler):
    server_address = ("", hub_constants.SERVER_PORT)
    httpd = server_class(server_address, handler_class)
    print(f"Starting server on port {hub_constants.SERVER_PORT}...")
    httpd.serve_forever()


if __name__ == "__main__":
    run()
