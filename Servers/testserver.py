#Flow== ESP32 --Websocket -- server --Websocket -- frontend(Using Two Ports)
import asyncio
import websockets
import os

# === Shared Data Store ===
connected_clients = set()
latest_data = {
    "temperature": 0.0,
    "tds": 0.0,
    "ph": 0.0
}

PORT_ESP32 = int(os.environ.get("PORT_ESP32", 5050))
PORT_FRONTEND = int(os.environ.get("PORT_FRONTEND", 5005))

# === Broadcast Data to All Frontend Clients ===
async def broadcast_to_clients(message):
    disconnected = set()
    for client in connected_clients:
        try:
            await client.send(message)
        except:
            disconnected.add(client)
    connected_clients.difference_update(disconnected)

# === Handles WebSocket Clients (Frontend) ===
async def frontend_handler(websocket):
    print("Frontend connected.")
    connected_clients.add(websocket)

    # Send latest data immediately
    await websocket.send(f"{latest_data['temperature']},{latest_data['tds']},{latest_data['ph']}")

    try:
        await asyncio.Future()  # Keep alive
    finally:
        connected_clients.remove(websocket)
        print("Frontend disconnected.")

# === Handles WebSocket From ESP32 ===
async def esp32_handler(websocket):
    print("ESP32 connected.")
    try:
        async for message in websocket:
            print(f"Received from ESP32: {message}")
            try:
                t, tds, ph = map(float, message.strip().split(","))
                latest_data["temperature"] = t
                latest_data["tds"] = tds
                latest_data["ph"] = ph
                await broadcast_to_clients(message)
            except ValueError:
                print("Invalid format from ESP32.")
    except:
        print("ESP32 disconnected.")

# === Main Server ===
async def main():
    print("Starting servers...")

    esp32_server = await websockets.serve(esp32_handler, "0.0.0.0", PORT_ESP32)
    frontend_server = await websockets.serve(frontend_handler, "0.0.0.0", PORT_FRONTEND)

    await asyncio.Future()  # Keep alive

asyncio.run(main())