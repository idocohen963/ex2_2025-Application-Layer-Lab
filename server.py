"""
Assignment 2 - Computer Networks
Calculator Server Implementation

Purpose:
========
This file implements a multi-threaded TCP server that receives mathematical expressions
from clients, performs complex calculations, and returns results with optional step-by-step
solutions. The server handles multiple concurrent client connections using threading.

Server Architecture:
===================
- Multi-threaded TCP server using socket programming
- Each client connection is handled by a separate thread
- Supports caching policies for optimized performance
- Implements custom protocol for communication with clients

Protocol Handling:
=================
The server receives requests using the protocol defined in api.py:
- Unpacks incoming binary data into CalculatorHeader objects
- Processes mathematical expressions recursively
- Returns results with optional calculation steps
- Handles errors gracefully with appropriate status codes

Key Features:
============
1. Multi-threaded architecture for concurrent client handling
2. Recursive expression evaluation with step tracking
3. Support for various mathematical operations (arithmetic, trigonometric, logarithmic)
4. Error handling and appropriate status code responses
5. Configurable caching policies

Mathematical Operations Supported:
================================
- Basic arithmetic: +, -, *, /, %, **
- Trigonometric functions: sin, cos, tan
- Mathematical functions: sqrt, log, max, min, pow
- Constants: pi, tau, e
- Unary operations: negation, positive

Usage Instructions:
==================
python server.py                    # Start server on default port (9999)
python server.py -p 8888           # Start server on port 8888
python server.py -H 0.0.0.0        # Start server on all network interfaces
"""

import numbers
import api
import argparse
import socket
import threading

# Server configuration constants
CACHE_POLICY = True  # Whether to cache responses or not
CACHE_CONTROL = 2 ** 16 - 1  # Maximum time that response can be cached (in seconds)


def calculate(expression: api.Expr, steps: list[str] = []) -> tuple[numbers.Real, list[api.Expression]]:
    """
    Recursively calculates the result of a mathematical expression and tracks calculation steps
    
    This function implements a recursive descent calculator that processes different types
    of mathematical expressions and builds a step-by-step solution path.
    
    Args:
        expression: The mathematical expression to evaluate (from api.py types)
        steps: List to accumulate calculation steps (modified in-place)
        
    Returns:
        tuple: (final_result, list_of_expression_steps)
        
    Raises:
        TypeError: If an unknown expression type is encountered
        
    Expression Types Handled:
    - Constant/NamedConstant: Direct value return
    - BinaryExpr: Two-operand operations (+, -, *, /, %, **)
    - UnaryExpr: Single-operand operations (-, +)
    - FunctionCallExpr: Function calls (sin, cos, max, etc.)
    
    The function builds a complete step-by-step solution by:
    1. Recursively evaluating sub-expressions
    2. Recording intermediate results
    3. Combining results according to operator precedence
    """
    expr = api.type_fallback(expression)
    const = None
    if isinstance(expr, api.Constant) or isinstance(expr, api.NamedConstant):
        const = expr
    elif isinstance(expr, api.BinaryExpr):
        left_steps, right_steps = [], []
        left, left_steps = calculate(expr.left_operand, left_steps)
        for step in left_steps[:-1]:
            steps.append(api.BinaryExpr(
                step, expr.operator, expr.right_operand))
        right, left_steps = calculate(expr.right_operand, right_steps)
        for step in right_steps[:-1]:
            steps.append(api.BinaryExpr(left, expr.operator, step))
        steps.append(api.BinaryExpr(left, expr.operator, right))
        const = api.Constant(expr.operator.function(left, right))
        steps.append(const)
    elif isinstance(expr, api.UnaryExpr):
        operand_steps = []
        operand, operand_steps = calculate(expr.operand, operand_steps)
        for step in operand_steps[:-1]:
            steps.append(api.UnaryExpr(expr.operator, step))
        steps.append(api.UnaryExpr(expr.operator, operand))
        const = api.Constant(expr.operator.function(operand))
        steps.append(const)
    elif isinstance(expr, api.FunctionCallExpr):
        args = []
        for arg in expr.args:
            arg_steps = []
            arg, arg_steps = calculate(arg, arg_steps)
            for step in arg_steps[:-1]:
                steps.append(api.FunctionCallExpr(expr.function, *
                (args + [step] + expr.args[len(args) + 1:])))
            args.append(arg)
        steps.append(api.FunctionCallExpr(expr.function, *args))
        const = api.Constant(expr.function.function(*args))
        steps.append(const)
    else:
        raise TypeError(f"Unknown expression type: {type(expr)}")
    return const.value, steps


def process_request(request: api.CalculatorHeader) -> api.CalculatorHeader:
    """
    Processes a client request and builds an appropriate response
    
    This function takes a CalculatorHeader request, extracts the mathematical expression,
    performs the calculation, and builds a response with the result and optional steps.
    
    Args:
        request: CalculatorHeader object containing the client request
        
    Returns:
        CalculatorHeader: Response object with calculation result or error information
        
    Process:
    1. Validates that the received packet is actually a request
    2. Extracts the mathematical expression from request data
    3. Calls calculate() to perform the computation
    4. Formats the response with results and optional calculation steps
    5. Handles errors by returning appropriate error responses
    
    Error Handling:
    - Client errors (400): Invalid expression format, malformed request
    - Server errors (500): Unexpected calculation errors, system issues
    """
    result, steps = None, []
    try:
        if request.is_request:
            # Extract mathematical expression from request data
            expr = api.data_to_expression(request)
            # Perform the calculation and get steps
            result, steps = calculate(expr, steps)
        else:
            raise TypeError("Received a response instead of a request")
    except Exception as e:
        # Return error response for any calculation or parsing errors
        return api.CalculatorHeader.from_error(e, api.CalculatorHeader.STATUS_CLIENT_ERROR, CACHE_POLICY, CACHE_CONTROL)

    # Format calculation steps if requested by client
    if request.show_steps:
        steps = [api.stringify(step, add_brackets=True) for step in steps]
    else:
        steps = []

    # Return successful response with result and optional steps
    return api.CalculatorHeader.from_result(result, steps, CACHE_POLICY, CACHE_CONTROL)


def server(host: str, port: int) -> None:
    """
    Main server function that sets up TCP socket and handles client connections
    
    This function creates a TCP server socket, binds it to the specified address,
    and enters a loop to accept and handle client connections using threading.
    
    Args:
        host: IP address to bind the server to (e.g., "127.0.0.1" or "0.0.0.0")
        port: Port number to listen on (e.g., 9999)
        
    Server Architecture:
    - Uses IPv4 TCP sockets (AF_INET, SOCK_STREAM)
    - SO_REUSEADDR option allows immediate restart after shutdown
    - Multi-threaded: each client connection handled by separate thread
    - Graceful shutdown on KeyboardInterrupt (Ctrl+C)
    
    Socket Operations:
    1. Create socket with IPv4 and TCP
    2. Set SO_REUSEADDR to reuse address immediately
    3. Bind socket to host:port
    4. Listen for incoming connections
    5. Accept connections and spawn handler threads
    """
    # Create TCP socket using IPv4
    # AF_INET = Address Family for IPv4
    # SOCK_STREAM = Socket Type for TCP (SOCK_DGRAM would be UDP)
    # Context manager ensures socket is properly closed
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        # SO_REUSEADDR allows socket to bind to address that was recently used
        # This prevents "Address already in use" errors during development
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Bind socket to specified address and start listening
        server_socket.bind((host, port))           # Bind to host:port
        server_socket.listen(1)                    # Listen for connections (backlog=1)

        threads = []
        print(f"Listening on {host}:{port}")

        while True:
            try:
                # Accept incoming client connection
                # Returns new socket for this client and client's address
                client_socket, address = server_socket.accept()

                # Create new thread to handle this client
                # Each client gets dedicated thread for concurrent processing
                thread = threading.Thread(target=client_handler, args=(client_socket, address))
                thread.start()
                threads.append(thread)
            except KeyboardInterrupt:
                print("Shutting down...")
                break

        # Wait for all client handler threads to complete before exit
        for thread in threads:
            thread.join()


def client_handler(client_socket: socket.socket, client_address: tuple[str, int]) -> None:
    """
    Handles individual client connection in a dedicated thread
    
    This function manages the communication with a single client, processing
    multiple requests over the same connection until the client disconnects.
    
    Args:
        client_socket: Socket object for communication with this specific client
        client_address: Tuple containing client's IP address and port number
        
    Process:
    1. Accept and maintain connection with client
    2. Receive data packets from client
    3. Unpack and validate requests
    4. Process mathematical expressions
    5. Send responses back to client
    6. Handle connection termination gracefully
    
    Error Handling:
    - Malformed packets: Send CLIENT_ERROR response
    - Calculation errors: Send CLIENT_ERROR response  
    - Server errors: Send SERVER_ERROR response
    - Connection issues: Log and terminate connection
    
    The function operates in a loop, processing multiple requests from the same
    client until the connection is closed or an error occurs.
    """
    client_addr = f"{client_address[0]}:{client_address[1]}"
    client_prefix = f"{{{client_addr}}}"
    
    # Use context manager to ensure socket is properly closed
    with client_socket:
        print(f"Connection established with {client_addr}")
        
        while True:
            # Receive data from client (blocking call)
            data = client_socket.recv(api.BUFFER_SIZE)
            if not data:
                # Client closed connection (empty data indicates disconnection)
                break
                
            try:
                # Unpack binary data into CalculatorHeader object
                try:
                    request = api.CalculatorHeader.unpack(data)
                except Exception as e:
                    raise api.CalculatorClientError(
                        f'Error while unpacking request: {e}') from e

                print(f"{client_prefix} Got request of length {len(data)} bytes")

                # Process the mathematical expression and generate response
                response = process_request(request)

                # Pack response into binary format and send to client
                response = response.pack()
                print(f"{client_prefix} Sending response of length {len(response)} bytes")
                client_socket.sendall(response)

            except Exception as e:
                # Handle unexpected server errors
                print(f"Unexpected server error: {e}")
                error_response = api.CalculatorHeader.from_error(
                    e, api.CalculatorHeader.STATUS_SERVER_ERROR, CACHE_POLICY, CACHE_CONTROL)
                client_socket.sendall(error_response.pack())

        print(f"{client_prefix} Connection closed")
        client_socket.close()


if __name__ == '__main__':
    # Parse command line arguments for server configuration
    arg_parser = argparse.ArgumentParser(description='A Calculator Server.')

    arg_parser.add_argument('-p', '--port', type=int,
                            default=api.DEFAULT_SERVER_PORT, 
                            help='The port to listen on.')
    arg_parser.add_argument('-H', '--host', type=str,
                            default=api.DEFAULT_SERVER_HOST, 
                            help='The host to listen on.')

    args = arg_parser.parse_args()

    host = args.host
    port = args.port

    # Start the server with specified host and port
    server(host, port)
