"""
Assignment 2 - Computer Networks
Calculator Client Implementation

Purpose:
========
This file implements a TCP client that connects to a calculator server or proxy 
and sends mathematical expressions for computation. The client can build complex 
expressions, send them using a custom protocol, and process the responses.

Protocol Structure:
==================
The client sends requests using the protocol defined in api.py:
- Unix Time Stamp (32 bits): Time when the request is sent
- Total Length (16 bits): Total length of the packet
- Flags (3 bits): Flags for Cache, Steps, and packet Type
- Status Code (10 bits): Status code (relevant only for responses)
- Cache Control (16 bits): Cache behavior control
- Data: The encoded mathematical expression

Client Features:
===============
1. Interactive selection of expressions from a predefined list
2. Sending and receiving multiple requests in sequence until exit is chosen
3. Display of calculation results with or without solution steps
4. Handling of network errors and calculation errors
5. Support for connection to server directly or through proxy

Usage Instructions:
==================
python client.py                    # Connect to default server (port 9999)
python client.py -p 9998           # Connect to proxy (port 9998)
python client.py -H 192.168.1.100  # Connect to server on different machine
"""

import socket
import api
import argparse
import api

# region Predefined Mathematical Constants and Operators

# Mathematical constants for building expressions
pi_c = api.NAMED_CONSTANTS.PI       # Pi constant (3.14159...)
tau_c = api.NAMED_CONSTANTS.TAU     # Tau constant (2*Pi)
e_c = api.NAMED_CONSTANTS.E         # Euler's number (2.71828...)

# Binary operators for mathematical expressions
add_b = api.BINARY_OPERATORS.ADD    # Addition operator (+)
sub_b = api.BINARY_OPERATORS.SUB    # Subtraction operator (-)
mul_b = api.BINARY_OPERATORS.MUL    # Multiplication operator (*)
div_b = api.BINARY_OPERATORS.DIV    # Division operator (/)
mod_b = api.BINARY_OPERATORS.MOD    # Modulo operator (%)
pow_b = api.BINARY_OPERATORS.POW    # Power operator (**)

# Unary operators for mathematical expressions
neg_u = api.UNARY_OPERATORS.NEG     # Negation operator (-)
pos_u = api.UNARY_OPERATORS.POS     # Positive operator (+)

# Mathematical functions
sin_f = api.FUNCTIONS.SIN           # Sine function
cos_f = api.FUNCTIONS.COS           # Cosine function
tan_f = api.FUNCTIONS.TAN           # Tangent function
sqrt_f = api.FUNCTIONS.SQRT         # Square root function
log_f = api.FUNCTIONS.LOG           # Natural logarithm function
max_f = api.FUNCTIONS.MAX           # Maximum function
min_f = api.FUNCTIONS.MIN           # Minimum function
pow_f = api.FUNCTIONS.POW           # Power function
rand_f = api.FUNCTIONS.RAND         # Random number function

# endregion


def process_response(response: api.CalculatorHeader) -> None:
    """
    Processes a response from the server and displays it to the user
    
    Args:
        response: Protocol header received from the server
        
    Raises:
        api.CalculatorClientError: In case of client error or invalid response
        api.CalculatorServerError: In case of server error
        
    The function checks the status code and handles accordingly:
    - STATUS_OK (200): Displays the result and calculation steps (if requested)
    - STATUS_CLIENT_ERROR (400): Raises client error
    - STATUS_SERVER_ERROR (500): Raises server error
    """

    if response.is_request:
        raise api.CalculatorClientError("Got a request instead of a response")
    if response.status_code == api.CalculatorHeader.STATUS_OK:
        result, steps = api.data_to_result(response)
        print("Result:", result)
        if steps:
            print("Steps:")
            expr, first, *rest = steps
            print(f"{expr} = {first}", end="\n"*(not bool(rest)))
            if rest:
                print(
                    "".join(map(lambda v: f"\n{' ' * len(expr)} = {v}", rest)))
    elif response.status_code == api.CalculatorHeader.STATUS_CLIENT_ERROR:
        err = api.data_to_error(response)
        raise api.CalculatorClientError(err)
    elif response.status_code == api.CalculatorHeader.STATUS_SERVER_ERROR:
        err = api.data_to_error(response)
        raise api.CalculatorServerError(err)
    else:
        raise api.CalculatorClientError(
            f"Unknown status code: {response.status_code}")


def client(server_address: tuple[str, int], expression: [api.Expression], show_steps: bool = False, cache_result: bool = False, cache_control: int = api.CalculatorHeader.MAX_CACHE_CONTROL) -> None:
    """
    Main client function - connects to server and sends expressions for calculation
    
    Args:
        server_address: Server address (IP, Port)
        expression: List of expressions to send
        show_steps: Whether to display calculation steps (default: False)
        cache_result: Whether to request caching (default: False)
        cache_control: Maximum cache time in seconds (default: 65535)
        
    Process:
    1. Create TCP socket
    2. Connect to server/proxy
    3. For each expression:
       - Build request in custom protocol
       - Send request
       - Receive and process response
    4. Close connection
    
    The function handles network errors and protocol errors
    """

    server_prefix = f"{{{server_address[0]}:{server_address[1]}}}"
    # Create TCP socket using IPv4 and establish connection
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect(server_address)
        print(f"{server_prefix} Connection established")
        
        # Process each expression in the list
        for expression in expression:
            try:
                # Build request packet according to custom protocol
                request = api.CalculatorHeader.from_expression(
                    expression, show_steps, cache_result, cache_control)

                # Pack request into bytes and send to server
                request = request.pack()
                print(f"{server_prefix} Sending request of length {len(request)} bytes")
                client_socket.sendall(request)

                # Receive response from server
                response = client_socket.recv(api.BUFFER_SIZE)
                print(f"{server_prefix} Got response of length {len(response)} bytes")
                
                # Unpack and process the response
                response = api.CalculatorHeader.unpack(response)
                process_response(response)

            except api.CalculatorError as e:
                # Handle calculator-specific errors
                print(f"{server_prefix} Got error: {str(e)}")
            except Exception as e:
                # Handle unexpected errors
                print(f"{server_prefix} Unexpected error: {str(e)}")
    print(f"{server_prefix} Connection closed")


if __name__ == "__main__":
    # Parse command line arguments
    arg_parser = argparse.ArgumentParser(description="A Calculator Client.")

    arg_parser.add_argument("-p", "--port", type=int,
                            default=api.DEFAULT_SERVER_PORT, help="The port to connect to.")
    arg_parser.add_argument("-H", "--host", type=str,
                            default=api.DEFAULT_SERVER_HOST, help="The host to connect to.")

    args = arg_parser.parse_args()

    host = args.host
    port = args.port

    # Predefined mathematical expressions for demonstration
    # These expressions showcase different capabilities of the calculator
    
    # Example expressions: (uncomment one of them for your needs)
    # (1) '(sin(max(2, 3 * 4, 5, 6 * ((7 * 8) / 9), 10 / 11)) / 12) * 13' = -0.38748277824137206
    expr0 = mul_b(div_b(sin_f(max_f(2, mul_b(3, 4), 5, mul_b(
        6, div_b(mul_b(7, 8), 9)), div_b(10, 11))), 12), 13)  # Complex trigonometric expression

    # (2) '(max(2, 3) + 3)' = 6
    expr1 = add_b(max_f(2, 3), 3)  # Simple max function usage

    # (3) '3 + ((4 * 2) / ((1 - 5) ** (2 ** 3)))' = 3.0001220703125
    expr2 = add_b(3, div_b(mul_b(4, 2), pow_b(sub_b(1, 5), pow_b(2, 3))))  # Nested power operations

    # (4) '((1 + 2) ** (3 * 4)) / (5 * 6)' = 17714.7
    expr3 = div_b(pow_b(add_b(1, 2), mul_b(3, 4)), mul_b(5, 6))  # Power and division

    # (5) '-(-((1 + (2 + 3)) ** -(4 + 5)))' = 9.92290301275212e-08
    expr4 = neg_u(neg_u(pow_b(add_b(1, add_b(2, 3)), neg_u(add_b(4, 5)))))  # Negative exponents

    # (6) 'max(2, (3 * 4), log(e), (6 * 7), (9 / 8))' = 42
    expr5 = max_f(2, mul_b(3, 4), log_f(e_c), mul_b(6, 7), div_b(9, 8))  # Max with logarithm

    # Configuration settings for sending requests:
    show_steps = True      # Request calculation steps to be shown
    cache_result = True    # Request result to be cached
    # Maximum age of cached response that the client is willing to accept (in seconds)
    cache_control = 2**16 - 1

    # Interactive user interface for expression selection
    print("Available expressions:")
    print("1: Expression 0 - Complex trigonometric expression")
    print("2: Expression 5 - Max function with logarithm")
    print("Type 'stop' to exit")

    # Main loop - continues until user chooses to exit
    while True:
        choice = input("\nEnter expression number (1 or 2) or 'stop': ").strip()

        if choice.lower() == 'stop':
            break

        if choice == '1':
            expr = expr0
        elif choice == '2':
            expr = expr5
        else:
            print("Invalid choice. Please enter 1, 2 or 'stop'")
            continue

        # Send the selected expression to server/proxy
        client((host, port), [expr], show_steps, cache_result, cache_control)
    print("\nClient socket closed, end of process")