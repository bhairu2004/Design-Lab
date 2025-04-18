#Flow== ESP32 --Websocket -- server --Websocket -- frontend(Using single Ports)
import asyncio
import websockets
import os

connected_frontends = set()
latest_data = {
    "temperature": 0.0,
    "tds": 0.0,
    "ph": 0.0
}

PORT = int(os.environ.get("PORT", 5050))

async def broadcast_to_frontends(message):
    disconnected = set()
    for client in connected_frontends:
        try:
            await client.send(message)
        except:
            disconnected.add(client)
    connected_frontends.difference_update(disconnected)

async def handler(websocket):
    if websocket.request.path == "/frontend":
        print("Frontend connected.")
        connected_frontends.add(websocket)
        await websocket.send(f"{latest_data['temperature']},{latest_data['tds']},{latest_data['ph']}")
        try:
            await asyncio.Future()  # Keep alive
        finally:
            connected_frontends.remove(websocket)
            print("Frontend disconnected.")
    elif websocket.request.path == "/esp32":
        print("ESP32 connected.")
        try:
            async for message in websocket:
                print(f"Received from ESP32: {message}")
                try:
                    t, tds, ph = map(float, message.strip().split(","))
                    latest_data["temperature"] = t
                    latest_data["tds"] = tds
                    latest_data["ph"] = ph
                    await broadcast_to_frontends(message)
                except ValueError:
                    print("Invalid format from ESP32.")
        except:
            print("ESP32 disconnected.")
    else:
        print("Unknown path. Closing connection.")
        await websocket.close()

async def main():
    print(f"Starting server on port {PORT}...")
    async with websockets.serve(handler, "0.0.0.0", PORT):
        await asyncio.Future()  # Keep alive

if __name__ == "__main__":
    asyncio.run(main())
