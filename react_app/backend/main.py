from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Form
import asyncio
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Keep track of currently active WebSocket clients
active_connections = set()

# Example tree data structure matching frontend expectations
ARTIFICIAL_TREE = {
    "node_id":
    "google.com",
    "title":
    "google.com",
    "type":
    "root",
    "method":
    None,
    "description":
    "Root domain",
    "children": [{
        "node_id":
        "google.com/mail.google.com",
        "title":
        "mail.google.com",
        "type":
        "subdomain",
        "method":
        None,
        "description":
        "Gmail service",
        "children": [{
            "node_id": "google.com/mail.google.com/api/mail/v1/messages",
            "title": "/api/mail/v1/messages",
            "type": "api",
            "method": "GET",
            "description": "Gmail messages API",
            "children": []
        }, {
            "node_id": "google.com/mail.google.com/api/mail/v1/send",
            "title": "/api/mail/v1/send",
            "type": "api",
            "method": "POST",
            "description": "Email sending endpoint",
            "children": []
        }]
    }, {
        "node_id":
        "google.com/drive.google.com",
        "title":
        "drive.google.com",
        "type":
        "subdomain",
        "method":
        None,
        "description":
        "Google Drive service",
        "children": [{
            "node_id": "google.com/drive.google.com/api/drive/v3/files",
            "title": "/api/drive/v3/files",
            "type": "api",
            "method": "GET",
            "description": "Drive files API",
            "children": []
        }, {
            "node_id": "google.com/drive.google.com/api/drive/v3/upload",
            "title": "/api/drive/v3/upload",
            "type": "api",
            "method": "POST",
            "description": "File upload endpoint",
            "children": []
        }]
    }]
}


@app.post("/upload-spec")
async def upload_spec(website_url: str = Form(...),
                      file: UploadFile = File(...)):
    """
    Receives the file and website_url.
    Just stores them for now (no actual processing in demo).
    """
    file_content = await file.read()
    print("Received file:", file.filename)
    print("Website URL:", website_url)

    return JSONResponse({
        "message":
        "File received. You can now call /start-stream to begin streaming.",
        "filename": file.filename,
        "website_url": website_url
    })


@app.get("/start-stream")
async def start_stream():
    """
    Called by the client to trigger the streaming of tree data.
    """
    await stream_tree(ARTIFICIAL_TREE)
    return {"message": "Streaming started!"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint that clients connect to.
    Broadcasts nodes one at a time to simulate real-time discovery.
    """
    await websocket.accept()
    active_connections.add(websocket)
    print("Client connected:", websocket.client)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        print("Client disconnected:", websocket.client)
        active_connections.remove(websocket)


async def broadcast(node: dict):
    """
    Send node data to all connected WebSocket clients.
    """
    to_remove = []
    for conn in active_connections:
        try:
            # Send the node data formatted as expected by frontend
            await conn.send_json({
                "node_id":
                node["node_id"],
                "title":
                node["title"],
                "type":
                node["type"],
                "method":
                node.get("method"),
                "description":
                node.get("description"),
                "children":
                [child["node_id"] for child in node.get("children", [])]
            })
        except Exception as e:
            print("Error sending message:", e)
            to_remove.append(conn)

    for conn in to_remove:
        active_connections.remove(conn)


async def stream_tree(node: dict):
    """
    Recursively traverse the tree and broadcast each node.
    Each node is sent with its node_id and children's node_ids.
    """
    # First broadcast this node
    await broadcast(node)
    await asyncio.sleep(0.5)  # Delay between nodes for visualization effect

    # Then recursively process children
    for child in node.get("children", []):
        await stream_tree(child)

    # If this is the root node (no parent), close connections after streaming
    if node["type"] == "root":
        print("Tree streaming complete. Closing WebSocket connections.")
        await close_all_connections()


async def close_all_connections():
    """Close all active WebSocket connections."""
    for conn in list(active_connections):
        try:
            await conn.close()
        except Exception as e:
            print("Error closing WebSocket:", e)
    active_connections.clear()
