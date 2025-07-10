# 🧮 Advanced Calculator Network System

A sophisticated multi-threaded TCP-based calculator system implementing custom protocol communication, intelligent caching proxy, and complex mathematical expression evaluation.

## 📋 Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Technical Implementation](#technical-implementation)
- [Protocol Specification](#protocol-specification)
- [Installation & Usage](#installation--usage)
- [Network Analysis](#network-analysis)
- [Performance Analysis](#performance-analysis)
- [Demo & Screenshots](#demo--screenshots)
- [Technical Skills Demonstrated](#technical-skills-demonstrated)

## 🎯 Overview

This project demonstrates advanced network programming concepts through a complete client-server-proxy architecture for mathematical expression evaluation. The system showcases:

- **Custom TCP Protocol Design** - Binary protocol with header fields for cache control, flags, and status codes
- **Multi-threaded Server Architecture** - Concurrent client handling using Python threading
- **Intelligent Caching Proxy** - HTTP-like caching semantics with freshness validation
- **Complex Mathematical Engine** - Recursive expression evaluation with step-by-step solutions
- **Network Traffic Analysis** - Wireshark packet captures for protocol verification

## 🏗️ Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│    Proxy    │────▶│   Server    │
│  (TCP/IP)   │     │  (Caching)  │     │(Calculator) │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   Cache     │
                    │  Storage    │
                    └─────────────┘
```

### Components:

1. **Calculator Client** - Interactive expression builder and request sender
2. **Calculator Server** - Multi-threaded mathematical expression processor
3. **Caching Proxy** - Intelligent middleware with cache management
4. **Custom Protocol** - Binary communication protocol with advanced features

## ✨ Features

### 🖥️ Client Features
- **Interactive Expression Selection** - Choose from predefined complex mathematical expressions
- **Real-time Communication** - TCP socket-based communication with server/proxy
- **Flexible Configuration** - Command-line arguments for host/port configuration
- **Error Handling** - Comprehensive error handling for network and calculation errors

### 🖧 Server Features
- **Multi-threaded Architecture** - Handle multiple concurrent client connections
- **Advanced Mathematical Engine** - Support for:
  - Basic arithmetic operations (+, -, *, /, %, **)
  - Trigonometric functions (sin, cos, tan)
  - Mathematical functions (sqrt, log, max, min, pow)
  - Named constants (π, τ, e)
  - Unary operations (negation, positive)
- **Step-by-step Solutions** - Optional detailed calculation steps
- **Robust Error Handling** - Graceful error responses with appropriate status codes

### 🔄 Proxy Features
- **Intelligent Caching** - HTTP-like caching with configurable TTL
- **Cache Freshness Validation** - Server-side and client-side cache control
- **Performance Optimization** - Reduce server load through smart caching
- **Transparent Operation** - Clients connect to proxy as if it were the server
- **Cache Statistics** - Detailed logging of cache hits/misses

## 🛠️ Technical Implementation

### Programming Concepts Demonstrated:
- **Socket Programming** - TCP client/server implementation
- **Multi-threading** - Concurrent request handling
- **Binary Protocol Design** - Custom network protocol with bit-level field packing
- **Object-Oriented Design** - Clean class hierarchies for expressions and operators
- **Recursive Algorithms** - Mathematical expression evaluation
- **Caching Algorithms** - Cache freshness and validation logic
- **Error Handling** - Comprehensive exception handling and error propagation

### Key Technologies:
- **Python 3.x** - Core implementation language
- **Socket Library** - Network communication
- **Threading** - Concurrent processing
- **Struct** - Binary data packing/unpacking
- **Pickle** - Object serialization
- **Argparse** - Command-line interface

## 📡 Protocol Specification

### Header Format (12 bytes):
```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                        Unix Time Stamp                        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|          Total Length         | Res.|C|S|T|    Status Code    |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|         Cache Control         |            Padding            |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

### Field Descriptions:
- **Unix Time Stamp** (32 bits) - Packet transmission time
- **Total Length** (16 bits) - Complete packet size (12-8192 bytes)
- **Flags** (3 bits) - Cache(C), Steps(S), Type(T) control bits
- **Status Code** (10 bits) - HTTP-like status codes (200, 400, 500)
- **Cache Control** (16 bits) - Cache TTL in seconds (0-65535)
- **Data** (≤8180 bytes) - Serialized mathematical expressions/results

## 🚀 Installation & Usage

### Prerequisites:
```bash
Python 3.7+
Wireshark (for network analysis)
```

### Quick Start:

1. **Start the Calculator Server:**
```bash
python server.py                    # Default port 9999
python server.py -p 8888           # Custom port
python server.py -H 0.0.0.0        # Listen on all interfaces
```

2. **Start the Caching Proxy:**
```bash
python proxy.py                     # Default: proxy:9998, server:9999
python proxy.py -pp 8888 -sp 7777  # Custom proxy and server ports
```

3. **Run the Client:**
```bash
python client.py                    # Connect to server (port 9999)
python client.py -p 9998           # Connect to proxy (port 9998)
python client.py -H 192.168.1.100  # Connect to remote server
```

### Example Mathematical Expressions:
```python
# Complex trigonometric expression
sin(max(2, 3*4, 5, 6*((7*8)/9), 10/11)) / 12 * 13

# Nested power operations  
3 + ((4*2) / ((1-5) ** (2**3)))

# Logarithmic with constants
max(2, 3*4, log(e), 6*7, 9/8)
```

## 📊 Network Analysis

### Wireshark Captures Included:
- **הקלטה 1.pcapng** - Basic client-server communication
- **הקלטה 2.pcapng** - Proxy caching behavior analysis  
- **הקלטה 3.pcapng** - Multi-client concurrent connections

### Analysis Points:
- TCP handshake establishment
- Custom protocol header parsing
- Cache hit/miss patterns
- Connection multiplexing
- Error handling protocols

## ⚡ Performance Analysis

### Caching Effectiveness:
- **Cache Hit Ratio** - Measured across multiple identical requests
- **Response Time Reduction** - Comparison of cached vs. computed responses
- **Server Load Reduction** - Impact of proxy on server resource utilization

## 📸 Demo & Screenshots

*Screenshots included in `צילומי מסך.docx` showing:*
- Client interactive interface
- Server console with multi-client handling
- Proxy cache statistics
- Wireshark protocol analysis
- Mathematical expression evaluation steps

## 🎓 Technical Skills Demonstrated

### Network Programming:
- ✅ TCP Socket Programming
- ✅ Custom Binary Protocol Design
- ✅ Multi-threaded Server Architecture
- ✅ Network Traffic Analysis with Wireshark
- ✅ Proxy Server Implementation

### Software Engineering:
- ✅ Object-Oriented Design Patterns
- ✅ Error Handling and Exception Management
- ✅ Code Documentation and Comments
- ✅ Modular Architecture Design
- ✅ Command-Line Interface Design

### Computer Science Fundamentals:
- ✅ Recursive Algorithm Implementation
- ✅ Caching and Performance Optimization
- ✅ Concurrent Programming and Threading
- ✅ Data Serialization and Deserialization
- ✅ Mathematical Expression Parsing and Evaluation

---

## 📝 Assignment Context

This project was developed as part of Computer Networks course (תקשורת רשתות) demonstrating practical implementation of networking concepts including:
- Socket programming fundamentals
- Protocol design and implementation
- Caching strategies and proxy servers
- Network performance analysis
- Real-world networking scenarios

**Academic Excellence:** This implementation goes beyond basic requirements by including comprehensive error handling, detailed documentation, performance analysis, and real network traffic captures for verification.

---

## Author

**Ido cohen**  
*idocohen963@gmail.com*  
[GitHub](https://github.com/idocohen963)  
[LinkedIn](https://www.linkedin.com/in/ido-cohen-14b8772b9/)
