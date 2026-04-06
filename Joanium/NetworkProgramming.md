---
name: NetworkProgramming
description: Build network clients, servers, proxies, and protocol implementations. Use when the user asks about TCP/UDP sockets, HTTP/2, gRPC, WebSockets from scratch, DNS resolution, TLS/SSL, packet capture, network diagnostics, or implementing custom application protocols.
---

You are an expert in network programming, covering TCP/UDP sockets, protocol design, HTTP/1.1/2/3, gRPC, DNS, TLS, proxy implementation, and network diagnostics across Node.js, Python, and Go.

The user provides a network programming task: building a TCP/UDP server, implementing an HTTP client, writing a proxy, debugging network issues, implementing a custom protocol, or working with raw sockets and packet inspection.

## Networking Fundamentals

**OSI Layers (relevant levels)**

- Layer 4 (Transport): TCP (reliable, ordered, connection-based), UDP (unreliable, unordered, connectionless)
- Layer 5-6 (Session/Presentation): TLS/SSL
- Layer 7 (Application): HTTP, gRPC, DNS, SMTP, WebSocket

**TCP vs UDP**

| Property    | TCP                                 | UDP                                |
| ----------- | ----------------------------------- | ---------------------------------- |
| Connection  | 3-way handshake                     | Connectionless                     |
| Reliability | Guaranteed delivery, retransmission | Best-effort                        |
| Ordering    | In-order delivery                   | May arrive out of order            |
| Overhead    | Higher (headers, ACKs)              | Minimal                            |
| Use cases   | HTTP, SSH, email, file transfer     | Video streaming, DNS, gaming, VoIP |

## TCP Sockets

**Node.js TCP Server**

```js
const net = require('net');

const server = net.createServer((socket) => {
  const remoteAddr = `${socket.remoteAddress}:${socket.remotePort}`;
  console.log(`Connected: ${remoteAddr}`);

  socket.setEncoding('utf8');
  socket.setTimeout(30000); // 30s idle timeout

  let buffer = '';

  socket.on('data', (chunk) => {
    buffer += chunk;
    // Protocol: messages delimited by '\n'
    const lines = buffer.split('\n');
    buffer = lines.pop(); // Incomplete message stays in buffer

    for (const line of lines) {
      if (!line.trim()) continue;
      try {
        const message = JSON.parse(line);
        handleMessage(socket, message);
      } catch {
        socket.write(JSON.stringify({ error: 'Invalid JSON' }) + '\n');
      }
    }
  });

  socket.on('timeout', () => {
    socket.write(JSON.stringify({ error: 'Idle timeout' }) + '\n');
    socket.destroy();
  });

  socket.on('error', (err) => console.error(`Socket error [${remoteAddr}]:`, err.message));
  socket.on('close', () => console.log(`Disconnected: ${remoteAddr}`));
});

function handleMessage(socket, message) {
  const response = processCommand(message);
  socket.write(JSON.stringify(response) + '\n');
}

server.listen(8080, '0.0.0.0', () => {
  console.log('TCP server listening on :8080');
});
```

**Node.js TCP Client**

```js
const net = require('net');

const client = net.createConnection({ port: 8080, host: 'localhost' }, () => {
  console.log('Connected to server');
  sendMessage({ action: 'ping', timestamp: Date.now() });
});

client.setEncoding('utf8');
let buffer = '';

client.on('data', (chunk) => {
  buffer += chunk;
  const lines = buffer.split('\n');
  buffer = lines.pop();
  for (const line of lines) {
    if (line.trim()) console.log('Server:', JSON.parse(line));
  }
});

function sendMessage(msg) {
  client.write(JSON.stringify(msg) + '\n');
}
```

**Python TCP Server (asyncio)**

```python
import asyncio
import json

class ProtocolServer:
    def __init__(self):
        self.clients: dict[str, asyncio.StreamWriter] = {}

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        addr = writer.get_extra_info('peername')
        client_id = f"{addr[0]}:{addr[1]}"
        self.clients[client_id] = writer
        print(f"Connected: {client_id}")

        try:
            while True:
                try:
                    line = await asyncio.wait_for(reader.readline(), timeout=30.0)
                except asyncio.TimeoutError:
                    writer.write(b'{"error":"timeout"}\n')
                    break

                if not line:  # Client disconnected
                    break

                try:
                    message = json.loads(line.decode().strip())
                    response = await self.process_message(message)
                    writer.write((json.dumps(response) + '\n').encode())
                    await writer.drain()
                except json.JSONDecodeError:
                    writer.write(b'{"error":"invalid_json"}\n')
        finally:
            del self.clients[client_id]
            writer.close()
            await writer.wait_closed()
            print(f"Disconnected: {client_id}")

    async def process_message(self, msg: dict) -> dict:
        action = msg.get('action')
        if action == 'ping':
            return {'action': 'pong', 'timestamp': msg.get('timestamp')}
        return {'error': 'unknown_action'}

    async def start(self, host='0.0.0.0', port=8080):
        server = await asyncio.start_server(self.handle_client, host, port)
        print(f"Server listening on {host}:{port}")
        async with server:
            await server.serve_forever()

asyncio.run(ProtocolServer().start())
```

## UDP

```python
import asyncio

class UDPProtocol(asyncio.DatagramProtocol):
    def __init__(self):
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data: bytes, addr: tuple):
        message = data.decode()
        print(f"Received from {addr}: {message}")
        # Echo back
        self.transport.sendto(f"Echo: {message}".encode(), addr)

    def error_received(self, exc):
        print(f"Error: {exc}")

async def main():
    loop = asyncio.get_event_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        UDPProtocol, local_addr=('0.0.0.0', 9000)
    )
    print("UDP server on :9000")
    try:
        await asyncio.sleep(3600)
    finally:
        transport.close()

asyncio.run(main())
```

## HTTP Client (raw fetch + retry)

```js
async function fetchWithRetry(url, options = {}, maxRetries = 3) {
  const { retryDelay = 1000, retryOn = [429, 500, 502, 503, 504], ...fetchOptions } = options;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      const response = await fetch(url, {
        signal: AbortSignal.timeout(10000), // 10s timeout
        ...fetchOptions,
      });

      if (!retryOn.includes(response.status)) {
        if (!response.ok) throw new Error(`HTTP ${response.status}: ${await response.text()}`);
        return response;
      }

      if (attempt === maxRetries)
        throw new Error(`Max retries exceeded. Last status: ${response.status}`);

      const retryAfter = parseInt(response.headers.get('retry-after') || '0') * 1000;
      await sleep(Math.max(retryAfter, retryDelay * Math.pow(2, attempt)));
    } catch (err) {
      if (attempt === maxRetries) throw err;
      if (err.name === 'AbortError' || err.name === 'TimeoutError') {
        await sleep(retryDelay * Math.pow(2, attempt));
        continue;
      }
      throw err; // Don't retry non-transient errors
    }
  }
}
```

## gRPC

**Proto Definition**

```protobuf
syntax = "proto3";
package chat;

service ChatService {
  rpc SendMessage (MessageRequest) returns (MessageResponse);
  rpc StreamMessages (Empty) returns (stream MessageResponse);
  rpc Chat (stream MessageRequest) returns (stream MessageResponse);
}

message MessageRequest {
  string content = 1;
  string user_id = 2;
}

message MessageResponse {
  string id = 1;
  string content = 2;
  string user_id = 3;
  int64 timestamp = 4;
}

message Empty {}
```

**Node.js gRPC Server**

```js
const grpc = require('@grpc/grpc-js');
const protoLoader = require('@grpc/proto-loader');

const packageDef = protoLoader.loadSync('chat.proto', { keepCase: true, defaults: true });
const proto = grpc.loadPackageDefinition(packageDef).chat;

const server = new grpc.Server();

server.addService(proto.ChatService.service, {
  sendMessage: (call, callback) => {
    const { content, user_id } = call.request;
    const response = {
      id: crypto.randomUUID(),
      content: `Echo: ${content}`,
      user_id,
      timestamp: Date.now(),
    };
    callback(null, response);
  },

  streamMessages: (call) => {
    const interval = setInterval(() => {
      call.write({ id: crypto.randomUUID(), content: 'Live update', timestamp: Date.now() });
    }, 1000);
    call.on('cancelled', () => clearInterval(interval));
  },
});

server.bindAsync('0.0.0.0:50051', grpc.ServerCredentials.createInsecure(), () => {
  console.log('gRPC server running on :50051');
});
```

## TLS / SSL

**Node.js HTTPS Server**

```js
const https = require('https');
const fs = require('fs');

const server = https.createServer(
  {
    key: fs.readFileSync('private.key'),
    cert: fs.readFileSync('certificate.crt'),
    ca: fs.readFileSync('ca-bundle.crt'), // Optional: chain
    minVersion: 'TLSv1.2',
    ciphers: 'TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256',
  },
  (req, res) => {
    res.writeHead(200);
    res.end('Secure!\n');
  },
);

server.listen(443);
```

**Self-Signed Cert (Dev)**

```bash
# Generate key + self-signed cert
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes \
  -subj "/C=US/ST=CA/L=SF/O=Dev/CN=localhost"

# Include SANs (for modern browsers)
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes \
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"
```

## Network Diagnostics

```bash
# TCP connection test
nc -zv host 443  # Test if port is open
curl -v --max-time 5 https://api.example.com/health  # Full HTTP trace

# DNS resolution
dig +short api.example.com          # A record
dig +short api.example.com MX       # Mail exchange
dig @8.8.8.8 api.example.com        # Query specific DNS server

# Network path analysis
traceroute api.example.com          # Linux/macOS hop-by-hop
tracert api.example.com             # Windows

# Connection monitoring
ss -tnp                             # All TCP connections with process (Linux)
netstat -an | grep LISTEN           # All listening ports

# Packet capture
tcpdump -i any -n port 8080 -w capture.pcap   # Capture port 8080
tcpdump -r capture.pcap -X                     # Read and print hex+ASCII

# Bandwidth test
iperf3 -s                                      # Server
iperf3 -c server-host -p 5201 -t 30           # Client (30s TCP test)
```

## Custom Protocol Design

**Principles**

- Choose a clear framing strategy: length-prefix, delimiter (e.g., `\n`), or fixed-size header
- Version the protocol from day 1: include a version byte/field in every message
- Separate control messages from data messages
- Design for extension: include a flags field or opcode space for future use

**Binary Length-Prefix Protocol**

```js
// Message format: [4-byte length LE][payload bytes]
function encodeMessage(payload) {
  const data = Buffer.from(JSON.stringify(payload), 'utf8');
  const header = Buffer.allocUnsafe(4);
  header.writeUInt32LE(data.length, 0);
  return Buffer.concat([header, data]);
}

// Streaming decoder
function createMessageDecoder(onMessage) {
  let buffer = Buffer.alloc(0);
  return (chunk) => {
    buffer = Buffer.concat([buffer, chunk]);
    while (buffer.length >= 4) {
      const length = buffer.readUInt32LE(0);
      if (buffer.length < 4 + length) break; // Wait for more data
      const payload = JSON.parse(buffer.slice(4, 4 + length).toString());
      onMessage(payload);
      buffer = buffer.slice(4 + length);
    }
  };
}
```
