import h2.connection
import h2.events
import socket


def test_http2_server(host="192.168.1.10", port=80):
    """
    Test HTTP/2 server starting with the preface, sending a request, and receiving a HEADER frame.
    """
    # Create a socket and connect to the server
    sock = socket.create_connection((host, port))
    conn = h2.connection.H2Connection()

    # Step 1: Send the HTTP/2 preface and initial SETTINGS frame
    conn.initiate_connection()
    sock.sendall(conn.data_to_send())
    print("Sent HTTP/2 connection preface and initial SETTINGS frame.")

    # Step 2: Wait for server's response and process SETTINGS frame
    response_data = sock.recv(4096)
    conn.receive_data(response_data)

    # Step 3: Open a new stream and send a request
    stream_id = conn.get_next_available_stream_id()
    conn.send_headers(
        stream_id=stream_id,
        headers=[
            (":method", "GET"),
            (":path", "/"),
            (":scheme", "http"),
            (":authority", host),
        ],
        end_stream=True,  # Indicate that there is no body
    )
    sock.sendall(conn.data_to_send())
    print(f"Sent HEADERS frame for stream {stream_id}.")

    # Step 4: Wait for server's response and process HEADER frame
    response_data = sock.recv(4096)
    conn.receive_data(response_data)

    for event in conn.events:
        if isinstance(event, h2.events.ResponseReceived):
            print(f"Received HEADER frame on stream {event.stream_id}:")
            for header in event.headers:
                print(f"  {header[0]}: {header[1]}")
        elif isinstance(event, h2.events.DataReceived):
            print(f"Received DATA frame on stream {event.stream_id}: {event.data.decode('utf-8')}")
        elif isinstance(event, h2.events.StreamEnded):
            print(f"Stream {event.stream_id} ended.")
        else:
            print(f"Unhandled event: {event}")

    # Step 5: Close the connection
    sock.close()
    print("Closed connection to the server.")


if __name__ == "__main__":
    test_http2_server("192.168.1.12", 80)
