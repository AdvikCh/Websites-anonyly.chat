import trio; from trio_websocket import serve_websocket, ConnectionClosed; import os; import json; import random

clients = set(); PORT = int(os.environ.get("PORT", 10000))
messages = []
CENSORED_WORDS = ["gaand", "gand", "laude", "lode", "chod", "bhosdi", "bsd", "rand", "puss", "fuk", "fuc", "dick", "dik", "penis", "pens", "chut", "chuut", "choot", "chut", "teri", "negro", "nigg", "vineet", "amit", "bhagwa", "bagwa", "god"]
CENSOR = ["I am a very bad boy -- Advik must punish me ~harder!!!!", "Ruk.. mai kya keh raha tha?", "Rainbows, butterflies, flowers, sunshine, and whimsy", "Advik is GOATed!!!!!!", "I promise to be a productive member of society.", "##### I ### ####### # ##### #### AM ######### #### ####### NOT ## IN ####### ######### ### #### EPSTIEN'S ################# ############ ## ###### FILES ########## ####### ####### ############ ###", "Please donate @ advikchaudhary.com/donate", "Call me plasma, be cause I am cool with the Nazis & the Jews -- gassed & the ghasted"]

async def updater():
    while True:
        for message in list(messages):
            if message["life"] > 1: message["life"] -= 1
            else: messages.remove(message)
        for client in list(clients):
            try: await client.send_message(json.dumps(messages)) # Yes.. this is unoptimal, and sends all messages for every new message written, but, is unoptimal in the scale of KB -- most network speeds are fine with this level of wastage; This is a TODO
            except ConnectionClosed: clients.discard(client)
        await trio.sleep(1)

async def reciever(request):
    request_headers = dict(request.headers)
    if request_headers.get("origin", "").rstrip("/").rstrip("/anonyly-chat") != "https://projects.advikchaudhary.com" and request_headers.get("Origin", "").rstrip("/").rstrip("/anonyly-chat") != "https://projects.advikchaudhary.com" and request_headers.get("ORIGIN", "").rstrip("/").rstrip("/anonyly-chat") != "https://projects.advikchaudhary.com": await request.reject(403); return
    web_socket = await request.accept(); clients.add(web_socket); web_socket.send_message(json.dumps(messages))
    try:
        while True:
            data = await web_socket.get_message()
            data = json.loads(data); message = data["message"]; ID = data["ID"]
            if len(message) > 1024: message = message[0:1025]
            for censored_word in CENSORED_WORDS:
                if censored_word in message.lower(): message = random.choice(CENSOR); break
            messages.append({"message": message, "ID": ID, "life": 30})
    except ConnectionClosed: pass
    finally: clients.discard(web_socket)

async def main():
    async with trio.open_nursery() as nursery:
        nursery.start_soon(updater)
        await serve_websocket(reciever, '0.0.0.0', PORT, ssl_context=None, max_message_size=8192)

trio.run(main)