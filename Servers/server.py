#Flow== ESP32 --TCP Socket -- server --Websocket -- frontend
import asyncio
import websockets

connected_clients = set()  # Store connected WebSocket clients

# Handles incoming WebSocket connections
async def websocket_handler(websocket):
    print("WebSocket client connected.")
    connected_clients.add(websocket)
    try:
        await asyncio.Future()  # Keep connection open
    finally:
        connected_clients.remove(websocket)
        print("WebSocket client disconnected.")

# Handles data received from ESP32 via TCP
async def handle_esp32_data():
    server = await asyncio.start_server(handle_tcp_connection, "0.0.0.0", 5050)
    print("TCP server (ESP32) started on port 5050")
    async with server:
        await server.serve_forever()

# Handles a single TCP connection from ESP32
async def handle_tcp_connection(reader, writer):
    addr = writer.get_extra_info('peername')
    print(f"ESP32 connected from {addr}")

    while True:
        try:
            data = await reader.read(1024)
            if not data:
                break

            decoded_data = data.decode().strip()
            print(f"Received from ESP32: {decoded_data}")

            # Broadcast to WebSocket clients
            for client in connected_clients.copy():
                try:
                    await client.send(decoded_data)
                except:
                    connected_clients.remove(client)
                    print("Error sending to WebSocket client. Removed.")

        except ConnectionResetError:
            print("ESP32 disconnected.")
            break

    writer.close()
    await writer.wait_closed()

# Main entrypoint: runs both TCP and WebSocket servers
async def main():
    print("WebSocket server started on ws://localhost:5005")
    await asyncio.gather(
        websockets.serve(websocket_handler, "0.0.0.0", 5005),
        handle_esp32_data()
    )

asyncio.run(main())
