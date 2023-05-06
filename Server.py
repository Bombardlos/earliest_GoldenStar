import asyncio
import json

clients = {}

async def handle_client(reader, writer):
    global clients
    client_id = id(writer)
    clients[client_id] = (0, 0, 0)
    while True:
        try:
            data = await reader.read(1024)
            position_str = data.decode().strip()
            if not position_str:
                raise ConnectionError
            x, y, theta = map(int, position_str.split(","))
            clients[client_id] = (x, y, theta)

            # Make a copy without client's position
            clients_copy = clients.copy()
            if client_id in clients_copy:
                del clients_copy[client_id]

            # Send positions of all clients as JSON
            positions_dict = {}
            for i, pos in enumerate(clients_copy.values()):
                positions_dict[f"player_{i}"] = pos
            positions_str = json.dumps(positions_dict)
            writer.write(positions_str.encode())
            await writer.drain()

        except ConnectionError:
            print("Client disconnected")
            del clients[client_id]
            writer.close()
            await writer.wait_closed()
            break


async def main():
    server = await asyncio.start_server(handle_client, '127.0.0.1', 8888)
    print("Server running on port 8888")
    async with server:
        await server.serve_forever()

asyncio.run(main())
