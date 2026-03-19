import trio; from trio_websocket import serve_websocket, ConnectionClosed; import os; import json; import random

clients = set(); attachment_limits = dict(); PORT = int(os.environ.get("PORT", 10000))
messages = []; updates = {"old": [], "new": []}
CENSORED_WORDS = ["gaand", "gand", "laude", "lode", "chod", "bhosdi", "bsd", "rand", "puss", "fuk", "fuc", "dick", "dik", "penis", "pens", "chut", "chuut", "choot", "chut", "teri", "negro", "nigg", "vineet", "amit", "bhagwa", "bagwa", "god"]
CENSOR = ["I am a very bad boy -- Advik must punish me HARDER!!!!!", "Ruk.. mai kya keh raha tha?", "{Rainbows, butterflies, flowers, sunshine, and whimsy}", "Advik is GOATed!!!!!!", "I promise to be a productive member of society.", "##### I ### ####### # ##### #### AM ######### #### ####### NOT ## IN ####### ######### ### #### EPSTIEN'S ################# ############ ## ###### FILES ########## ####### ####### ############ ###", "Please fund this service @ advikchaudhary.com/donate", "Call me plasma, be cause I am cool with the Nazis & the Jews -- ghasted & the gassed", "Call me ^.^ @ +91 1206787437", "Kal UNO khele?"]

async def allow_attachment(client: str): await trio.sleep(30); attachment_limits[client] = 1
async def reciever(request, nursery):
    request_headers = dict(request.headers); request_headers = {key.decode("utf-8").lower():value.decode("utf-8").lower() for key, value in request_headers.items()}
    if request_headers.get("origin", "").rstrip("/").rstrip("/anonyly-chat") != "https://projects.advikchaudhary.com": await request.reject(403); return
    web_socket = await request.accept(); clients.add(web_socket); attachment_limits[str(web_socket)] = 1; await web_socket.send_message(json.dumps(messages))
    try:
        while True:
            message = await web_socket.get_message()
            message = json.loads(message); text = message["text"]; image = message["image"]; ID = message["ID"]
            if len(text) > 1024: text = text[:1024]
            if image["picture"]:
                if attachment_limits[str(web_socket)] == 0: image["picture"] = ""
                else: attachment_limits[str(web_socket)] = 0; nursery.start_soon(allow_attachment, str(web_socket))
            for censored_word in CENSORED_WORDS:
                if censored_word in text.lower(): text = random.choice(CENSOR); break
            messages.append({"text": text, "image": image, "ID": ID, "life": 30}); updates["new"].append({"text": text, "image": image, "ID": ID, "life": 30})
    except ConnectionClosed: pass
    finally: clients.discard(web_socket); attachment_limits.pop[web_socket]
    
async def updater():
    while True:
        for message in list(messages):
            if message["life"] > 1: message["life"] -= 1
            else: messages.remove(message); updates["old"].append(message)
        for client in list(clients):
            try: await client.send_message(json.dumps(updates)); updates["old"] = []; updates["new"] = []
            except ConnectionClosed: clients.discard(client); attachment_limits.pop(client)
        await trio.sleep(1)

async def main():
    async with trio.open_nursery() as nursery:
        nursery.start_soon(updater)
        async def tunnel(request): await reciever(request, nursery)
        await serve_websocket(tunnel, '0.0.0.0', PORT, ssl_context=None, max_message_size=7348224) # ((5 + 2) * 1024 * 1024) + 8192 -- ((image_size_limit + base64 bloat buffer) * MB) + text_size_limit

trio.run(main)