"""
Assignment 2 - Computer Networks
Calculator Proxy Server Implementation

Purpose:
========
This file implements a caching proxy server that sits between calculator clients
and the calculator server. The proxy caches calculation results to improve performance
and reduce server load by serving repeated requests from cache when possible.

Proxy Architecture:
==================
- Multi-threaded TCP proxy server
- Intelligent caching system with configurable cache control
- Transparent proxy operation (clients connect to proxy as if it were the server)
- Cache freshness validation based on timestamps and cache control headers

Caching Strategy:
================
The proxy implements HTTP-like caching semantics:
- Requests with cache_control=0 bypass cache (force reload)
- Cache entries have server-side and client-side expiration times
- Stale cache entries are refreshed from the server
- Cache keys are based on expression data and show_steps flag

Cache Management:
================
- In-memory cache storage using dictionary
- Cache entries keyed by (expression_data, show_steps) tuple
- Cache freshness determined by comparing age with cache_control values
- Support for indefinite caching when cache_control=MAX_CACHE_CONTROL

Usage Instructions:
==================
python proxy.py                           # Start proxy on default ports
python proxy.py -pp 8888                 # Proxy listens on port 8888
python proxy.py -sp 9999 -sh 192.168.1.5 # Connect to server on remote host

Proxy Flow:
==========
Client -> Proxy -> Server (if cache miss/stale)
Client <- Proxy <- Cache (if cache hit)
"""

import api
import argparse
import threading
import socket
import time
import math

# Global cache storage: maps (expression_data, show_steps) -> CalculatorHeader response
cache: dict[tuple[bytes, bool], api.CalculatorHeader] = {}

# Constant for indefinite cache control (maximum possible value)
INDEFINITE = api.CalculatorHeader.MAX_CACHE_CONTROL


def process_request(request: api.CalculatorHeader, server_address: tuple[str, int]) -> tuple[api.CalculatorHeader, int, int, bool, bool, bool]:
    """
    Processes client request with intelligent caching logic
    
    This function implements the core proxy logic, deciding whether to serve
    from cache or forward the request to the server based on cache control
    headers and cache freshness.
    
    Args:
        request: Client request header containing expression and cache preferences
        server_address: Address of the calculator server (host, port)
        
    Returns:
        tuple containing:
        - response: CalculatorHeader with calculation result
        - server_time_remaining: Seconds until server considers response stale
        - client_time_remaining: Seconds until client considers response stale  
        - cache_hit: Boolean indicating if response came from cache
        - was_stale: Boolean indicating if cached response was stale
        - cached: Boolean indicating if response was stored in cache
        
    Cache Logic:
    1. If request.cache_control=0, bypass cache (force reload)
    2. Check cache for matching entry (expression + show_steps)
    3. Validate cache freshness against server and client cache control
    4. If fresh, return cached response
    5. If stale/missing, forward to server and optionally cache result
    
    Raises:
        TypeError: If request is actually a response
        api.CalculatorServerError: If server connection fails and no cache available
        api.CalculatorClientError: If response unpacking fails
    """
    if not request.is_request:
        raise TypeError("Received a response instead of a request")

    data = request.data
    server_time_remaining = None
    client_time_remaining = None
    was_stale = False
    cached = False
    # Check if the data is in the cache, if the requests cache-control is 0 we must not use the cache and request a new response
    if ((data, request.show_steps) in cache) and (request.cache_control != 0):
        response = cache[(data, request.show_steps)]
        current_time = int(time.time())
        age = current_time - response.unix_time_stamp
        res_cc = response.cache_control if response.cache_control != INDEFINITE else math.inf
        req_cc = request.cache_control if request.cache_control != INDEFINITE else math.inf
        server_time_remaining = res_cc - age
        client_time_remaining = req_cc - age
        # response is still 'fresh' both for the client and the server
        if server_time_remaining > 0 and client_time_remaining > 0:
            return response, server_time_remaining, client_time_remaining, True, False, False
        else:  # response is 'stale'
            was_stale = True

    # Request is not in the cache or the response is 'stale' so we need to send a new request to the server and cache the response
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        try:
            server_socket.connect(server_address)
        except ConnectionRefusedError:
            raise api.CalculatorServerError(
                "Connection refused by server and the request was not in the cache/it was stale")
        server_socket.sendall(request.pack())

        response = server_socket.recv(api.BUFFER_SIZE)

        try:
            response = api.CalculatorHeader.unpack(response)
        except Exception as e:
            raise api.CalculatorClientError(
                f'Error while unpacking request: {e}') from e

        if response.is_request:
            raise TypeError("Received a request instead of a response")

        current_time = int(time.time())
        age = current_time - response.unix_time_stamp
        res_cc = response.cache_control if response.cache_control != INDEFINITE else math.inf
        req_cc = request.cache_control if request.cache_control != INDEFINITE else math.inf
        server_time_remaining = res_cc - age
        client_time_remaining = req_cc - age
        # Cache the response if all sides agree to cache it
        if request.cache_result and response.cache_result and (server_time_remaining > 0 and client_time_remaining > 0):
            cache[(data, request.show_steps)] = response
            cached = True

    return response, server_time_remaining, client_time_remaining, False, was_stale, cached


def proxy(proxy_address: tuple[str, int], server_address: tuple[str, int]) -> None:
    """
    Main proxy function that sets up proxy server and handles client connections
    
    This function creates a TCP proxy server that listens for client connections
    and forwards requests to the calculator server while managing caching.
    
    Args:
        proxy_address: Address for proxy to bind to (host, port)
        server_address: Address of the calculator server to forward requests to
        
    Proxy Architecture:
    - Listens for client connections on proxy_address
    - Each client connection handled by separate thread
    - Forwards requests to server_address when cache miss occurs
    - Maintains persistent cache across all client connections
    
    Socket Operations:
    1. Create TCP socket with IPv4
    2. Set SO_REUSEADDR for immediate restart capability
    3. Bind to proxy address and listen for connections
    4. Accept client connections and spawn handler threads
    5. Graceful shutdown on KeyboardInterrupt
    """
    # Create TCP socket using IPv4
    # AF_INET = Address Family for IPv4, SOCK_STREAM = TCP socket type
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as proxy_socket:
        # Allow immediate reuse of address (prevents "Address already in use" errors)
        proxy_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Bind proxy socket to specified address and start listening
        proxy_socket.bind(proxy_address)
        proxy_socket.listen()

        threads = []
        print(f"Listening on {proxy_address[0]}:{proxy_address[1]}")

        while True:
            try:
                # Accept incoming client connection
                client_socket, client_address = proxy_socket.accept()

                # Create dedicated thread for this client connection
                # Pass server address so handler knows where to forward requests
                thread = threading.Thread(target=client_handler, args=(
                    client_socket, client_address, server_address))
                thread.start()
                threads.append(thread)
            except KeyboardInterrupt:
                print("Shutting down...")
                break

        # Wait for all client handler threads to complete
        for thread in threads:
            thread.join()


def client_handler(client_socket: socket.socket, client_address: tuple[str, int], server_address: tuple[str, int]) -> None:
    """
    Handles individual client connection with caching proxy logic
    
    This function manages communication with a single client, processing requests
    through the caching layer and forwarding to the server when necessary.
    
    Args:
        client_socket: Socket for communication with the client
        client_address: Client's IP address and port
        server_address: Calculator server's address for request forwarding
        
    Process Flow:
    1. Receive client requests
    2. Process through caching layer (check cache, validate freshness)
    3. Forward to server if cache miss or stale
    4. Cache response if appropriate
    5. Send response back to client
    6. Log cache statistics (hit/miss/stale)
    
    Cache Statistics Logged:
    - Cache hit: Response served from cache
    - Cache miss (stale): Cached response was expired
    - Cache miss (cached): New response was cached
    - Cache miss (not cached): New response was not cached
    
    Error Handling:
    - Malformed requests: Send CLIENT_ERROR response
    - Server connection issues: Send SERVER_ERROR response
    - Proxy internal errors: Send SERVER_ERROR response
    """
    client_prefix = f"{{{client_address[0]}:{client_address[1]}}}"
    
    # Use context manager to ensure proper socket cleanup
    with client_socket:
        print(f"{client_prefix} Connection established")
        
        while True:
            # Receive data from client
            data = client_socket.recv(api.BUFFER_SIZE)
            if not data:
                # Client disconnected (empty data indicates connection closed)
                break
                
            try:
                # Unpack client request
                try:
                    request = api.CalculatorHeader.unpack(data)
                except Exception as e:
                    raise api.CalculatorClientError(
                        f'Error while unpacking request: {e}') from e

                print(f"{client_prefix} Got request of length {len(data)} bytes")

                # Process request through caching layer
                response, server_time_remaining, client_time_remaining, cache_hit, was_stale, cached = process_request(
                    request, server_address)

                # Log cache statistics for monitoring
                if cache_hit:
                    print(f"{client_prefix} Cache hit", end=" ,")
                elif was_stale:
                    print(f"{client_prefix} Cache miss, stale response", end=" ,")
                elif cached:
                    print(f"{client_prefix} Cache miss, response cached", end=" ,")
                else:
                    print(f"{client_prefix} Cache miss, response not cached", end=" ,")
                print(f"server time remaining: {server_time_remaining:.2f}, client time remaining: {client_time_remaining:.2f}")

                # Pack and send response back to client
                response = response.pack()
                print(f"{client_prefix} Sending response of length {len(response)} bytes")
                client_socket.sendall(response)
                
            except Exception as e:
                # Handle proxy internal errors
                print(f"Unexpected server error: {e}")
                error_response = api.CalculatorHeader.from_error(
                    api.CalculatorServerError("Internal proxy error", e), 
                    api.CalculatorHeader.STATUS_SERVER_ERROR, False, 0)
                client_socket.sendall(error_response.pack())

        print(f"{client_prefix} Connection closed")
        client_socket.close()

if __name__ == '__main__':
    # Parse command line arguments for proxy configuration
    arg_parser = argparse.ArgumentParser(description='A Calculator Proxy Server.')

    # Proxy server configuration
    arg_parser.add_argument('-pp', '--proxy_port', type=int, dest='proxy_port',
                            default=api.DEFAULT_PROXY_PORT, 
                            help='The port that the proxy listens on.')
    arg_parser.add_argument('-ph', '--proxy_host', type=str, dest='proxy_host',
                            default=api.DEFAULT_PROXY_HOST, 
                            help='The host that the proxy listens on.')
    
    # Target server configuration  
    arg_parser.add_argument('-sp', '--server_port', type=int, dest='server_port',
                            default=api.DEFAULT_SERVER_PORT, 
                            help='The port that the server listens on.')
    arg_parser.add_argument('-sh', '--server_host', type=str, dest='server_host',
                            default=api.DEFAULT_SERVER_HOST, 
                            help='The host that the server listens on.')

    args = arg_parser.parse_args()

    # Extract configuration values
    proxy_host = args.proxy_host
    proxy_port = args.proxy_port
    server_host = args.server_host
    server_port = args.server_port

    # Start proxy server
    proxy((proxy_host, proxy_port), (server_host, server_port))
