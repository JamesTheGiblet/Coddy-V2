# Coddy/core/websocket_server.py
import asyncio
import websockets # Install with: pip install websockets
import json
import logging
from typing import Set, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Set of connected WebSocket clients
CONNECTED_CLIENTS: Set[websockets.WebSocketServerProtocol] = set()

# WebSocket server configuration
WEBSOCKET_HOST = "localhost"
WEBSOCKET_PORT = 8080

async def register_client(websocket: websockets.WebSocketServerProtocol):
    """Adds a new client to the set of connected clients."""
    CONNECTED_CLIENTS.add(websocket)
    logging.info(f"New WebSocket client connected: {websocket.remote_address}. Total clients: {len(CONNECTED_CLIENTS)}")

async def unregister_client(websocket: websockets.WebSocketServerProtocol):
    """Removes a client from the set of connected clients."""
    CONNECTED_CLIENTS.remove(websocket)
    logging.info(f"WebSocket client disconnected: {websocket.remote_address}. Total clients: {len(CONNECTED_CLIENTS)}")

async def broadcast_message(message: Dict[str, Any]):
    """
    Sends a JSON message to all connected WebSocket clients.
    The message should be a dictionary with 'type' and 'text' fields.
    """
    if not CONNECTED_CLIENTS:
        logging.info(f"No WebSocket clients connected to broadcast message: {message.get('text', 'N/A')}")
        return

    message_json = json.dumps(message)
    # Send message to all connected clients, handling potential disconnection
    disconnected_clients = []
    for websocket in CONNECTED_CLIENTS:
        try:
            await websocket.send(message_json)
        except websockets.exceptions.ConnectionClosedOK:
            logging.warning(f"Client {websocket.remote_address} was already closed when attempting to send. Marking for unregistration.")
            disconnected_clients.append(websocket)
        except Exception as e:
            logging.error(f"Error sending message to {websocket.remote_address}: {e}")
            disconnected_clients.append(websocket)
    
    for client in disconnected_clients:
        await unregister_client(client) # Unregister clients that disconnected during broadcast
    
    logging.info(f"Broadcasted message (type: {message.get('type')}, text: '{message.get('text', 'N/A')[:50]}...') to {len(CONNECTED_CLIENTS) - len(disconnected_clients)} clients.")


async def websocket_handler(websocket: websockets.WebSocketServerProtocol):
    """
    Handles incoming WebSocket connections and messages.
    Messages received here from one client will be broadcast to all others.
    This also registers/unregisters clients.
    """
    await register_client(websocket)
    try:
        # Keep the connection open and listen for messages
        # Here, we assume clients might send messages for specific actions, which we'll process.
        # For a log stream, we expect the React UI to send 'cli_input' messages.
        async for message_str in websocket:
            logging.info(f"Received message from {websocket.remote_address}: {message_str}")
            try:
                message = json.loads(message_str)
                # If the UI sends a command (type 'cli_input'), we'll print it to stdout
                # so the Python CLI (if running in the same process, or a consumer) can pick it up.
                # For this setup, we're assuming the Python CLI is a separate process.
                # A more robust solution would involve a message queue or a dedicated HTTP endpoint
                # for the UI to send commands to the Python CLI.
                if message.get("type") == "cli_input" and "command" in message:
                    # In this setup, we're broadcasting commands received from the UI back.
                    # This might be useful for a multi-user dashboard, but not for direct CLI execution.
                    # For direct CLI execution, you'd need a way to send this 'command' to the actual CLI process.
                    # For now, let's echo it and demonstrate it being received.
                    logging.info(f"UI Command Received: {message['command']}")
                    # You could optionally broadcast this back to confirm receipt or to other UIs
                    # await broadcast_message({"type": "cli_command_received", "text": f"Command received by WS server: {message['command']}"})
                else:
                    # Broadcast any other messages received from clients (e.g., UI) to other clients
                    await broadcast_message({"type": message.get("type", "unknown_client_message"), "text": message.get("text", message_str)})
            except json.JSONDecodeError:
                logging.warning(f"Received non-JSON message from client: {message_str}")
                await broadcast_message({"type": "warning", "text": f"Received non-JSON from UI: {message_str}"})
    except websockets.exceptions.ConnectionClosed:
        logging.info(f"Client {websocket.remote_address} disconnected cleanly.")
    except Exception as e:
        logging.error(f"WebSocket handler error for {websocket.remote_address}: {e}")
    finally:
        await unregister_client(websocket)

async def start_websocket_server():
    """Starts the WebSocket server."""
    logging.info(f"Starting WebSocket server on ws://{WEBSOCKET_HOST}:{WEBSOCKET_PORT}")
    async with websockets.serve(websocket_handler, WEBSOCKET_HOST, WEBSOCKET_PORT):
        await asyncio.Future()  # Run forever

# For testing the broadcast functionality from external Python scripts
async def send_to_websocket_server(message_data: Dict[str, Any]):
    """
    Connects to the local WebSocket server and sends a single message.
    Used by other Python modules (like CLI) to send logs to the UI.
    """
    uri = f"ws://{WEBSOCKET_HOST}:{WEBSOCKET_PORT}"
    try:
        async with websockets.connect(uri) as websocket:
            await websocket.send(json.dumps(message_data))
            logging.info(f"Sent message to WebSocket server: {message_data.get('text', 'N/A')[:50]}...")
    except ConnectionRefusedError:
        logging.error(f"Could not connect to WebSocket server at {uri}. Is it running?")
    except Exception as e:
        logging.error(f"Error sending message via WebSocket: {e}")

if __name__ == "__main__":
    # To run this server: python Coddy/core/websocket_server.py
    # This should be run in a separate terminal and kept running.
    # Ensure 'websockets' library is installed: pip install websockets
    print(f"Starting Coddy WebSocket Logstream Server on ws://{WEBSOCKET_HOST}:{WEBSOCKET_PORT}")
    try:
        asyncio.run(start_websocket_server())
    except KeyboardInterrupt:
        logging.info("WebSocket server stopped by user.")
    except Exception as e:
        logging.critical(f"Unhandled exception in WebSocket server: {e}")
