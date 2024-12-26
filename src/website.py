class SimpleWebsite:
    def __init__(self):
        # Define your routes and methods
        self.routes = {
            "/": self.index,
            "/about": self.about,
            "/contact": self.contact,
            "/echo": self.echo,
            "/json": self.json_response,
            "/html": self.html_response,
            "/upload": self.upload_data,
        }

    def handle_request(self, request_headers, request_data):
        """
        Processes an incoming request and generates a response.
        
        Parameters:
        - request_headers (dict): The HTTP/2 request headers.
        - request_data (bytes): The request body data (if any).

        Returns:
        - response_headers (list of tuples): The HTTP/2 response headers.
        - response_data (bytes): The response body.
        """
        method = request_headers.get(":method", "GET")
        path = request_headers.get(":path", "/")

        # Determine content type from headers (if provided by the client)
        content_type = request_headers.get("content-type", "text/plain")

        # Handle routing based on path and method
        if path in self.routes:
            route_handler = self.routes[path]
            return route_handler(method, request_data, content_type)
        else:
            return self.not_found(method, request_data, content_type)

    def index(self, method, body, content_type):
        """Handles the root route ("/")."""
        return self.create_response(200, "Welcome to the Simple HTTP/2 Website! Navigate to /about, /contact, /json, or /html.")

    def about(self, method, body, content_type):
        """Handles the /about route."""
        return self.create_response(200, "About: This is a simple HTTP/2 website for testing different HTTP/2 features.")

    def contact(self, method, body, content_type):
        """Handles the /contact route."""
        return self.create_response(200, "Contact: Reach us at contact@example.com")

    def echo(self, method, body, content_type):
        """Handles the /echo route (for POST requests)."""
        if method == "POST" and body:
            return self.create_response(200, f"Echoed data: {body.decode('utf-8')}")
        else:
            return self.create_response(400, "Echo requires a POST request with data.")

    def json_response(self, method, body, content_type):
        """Handles the /json route and returns a JSON response."""
        if method == "GET":
            import json
            response_data = json.dumps({"message": "This is a JSON response", "status": "success"})
            return self.create_response(200, response_data, content_type="application/json")
        else:
            return self.create_response(405, "Method Not Allowed: Use GET for /json.")

    def html_response(self, method, body, content_type):
        """Handles the /html route and returns an HTML response with links."""
        if method == "GET":
            html_content = """
            <html>
                <head><title>Test HTML Page</title></head>
                <body>
                    <h1>Welcome to the HTML page</h1>
                    <p>This page has multiple links:</p>
                    <ul>
                        <li><a href="/about">About</a></li>
                        <li><a href="/contact">Contact</a></li>
                        <li><a href="/json">JSON Example</a></li>
                    </ul>
                </body>
            </html>
            """
            return self.create_response(200, html_content, content_type="text/html")
        else:
            return self.create_response(405, "Method Not Allowed: Use GET for /html.")
        
    def upload_data(self, method, body, content_type):
        """
        Handles the /upload route for uploading large data payloads.
        
        Parameters:
        - method (str): The HTTP method (e.g., POST).
        - body (bytes): The request body containing the data.
        - content_type (str): The content type of the request.

        Returns:
        - A tuple of (response_headers, response_data).
        """
        if method == "POST":
            if body:
                data_size = len(body)
                print(f"Received {data_size} bytes of data")
                print(body.decode("utf-8"))
                return self.create_response(
                    200, 
                    f"Data received successfully. Size: {data_size} bytes.",
                    content_type="text/plain"
                )
            else:
                return self.create_response(
                    400, 
                    "No data received. Please send a non-empty body.",
                    content_type="text/plain"
                )
        else:
            return self.create_response(
                405, 
                "Method Not Allowed: Use POST for /upload.",
                content_type="text/plain"
            )

    def not_found(self, method, body, content_type):
        """Handles non-existent routes."""
        return self.create_response(404, f"Page not found for {method} request on the given path.")

    def create_response(self, status_code, body, content_type="text/plain"):
        """
        Creates a response with the provided status code and body by calling construct_response.
        
        Parameters:
        - status_code (int): The HTTP status code (e.g., 200, 404).
        - body (str): The response body as a string.
        - content_type (str): The content type of the response (default: text/plain).

        Returns:
        - response_headers (list of tuples): The HTTP/2 response headers.
        - response_data (bytes): The response body as bytes.
        """
        response_data = body.encode("utf-8")
        response_headers = [
            (":status", str(status_code)),
            ("content-type", content_type),
            ("content-length", str(len(response_data))),
        ]
        return response_headers, response_data