import websockets
import asyncio
import re
from googleapiclient import discovery

# Toxicity check
API_KEY = "AIzaSyCRYcuuDaLeqcxwwLLfSoghICibk6wnnxU"

# Server data
PORT = 7890
print("Server listening on Port " + str(PORT))

connected = set()
ban_list = []

def toxicmeter(msg):
    try:
        client = discovery.build(
            "commentanalyzer",
            "v1alpha1",
            developerKey=API_KEY,
            discoveryServiceUrl="https://commentanalyzer.googleapis.com/$discovery/rest?version=v1alpha1",
            static_discovery=False,
        )

        analyze_request = {
            'comment': {'text': msg},
            'requestedAttributes': {'TOXICITY': {}}
        }

        response = client.comments().analyze(body=analyze_request).execute()
        return response["attributeScores"]["TOXICITY"]["summaryScore"]["value"] * 100
        # print(json.dumps(response, indent=2))
    except Exception as e:
        print(e)




async def echo(websocket, path):
    client_id = websocket.remote_address[0]

    if client_id in ban_list:
        await websocket.close()
    else:
        print("A client just connected")
        connected.add(websocket)

        # Handle incoming messages
        try:
            async for message in websocket:
                print(f"{client_id} > {message}")

                if "kundanika" in str(message).lower():
                    ban_list.append(client_id)
                    await websocket.close()
                    print("A client has been banned")

                safe_msg = re.sub(re.compile('<.*.?>'), '', message)

                percentage = round(toxicmeter(message), 2)
                # Send a response to all connected clients except sender
                for conn in connected:
                    if conn != websocket:
                        await conn.send(f"<p>{client_id} > {safe_msg} <i style=\"font-size: 5;\">[Toxicity {percentage} %]</i></p>")

        # Handle disconnecting clients
        except websockets.exceptions.ConnectionClosed as e:
            print("A client just disconnected")
        finally:
            connected.remove(websocket)




# Start the server
start_server = websockets.serve(echo, "https://websocket-chatroom-tawny.vercel.app/", PORT)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
