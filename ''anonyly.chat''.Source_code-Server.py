import trio; from trio_websocket import serve_websocket, ConnectionClosed; import os; import json; import random

clients = set(); users = dict(); PORT = int(os.environ.get("PORT", 10000))
messages = []; updates = {"old": [], "new": []}
CENSORED_WORDS = ["gaand", "gand", "laude", "lode", "chod", "bhosdi", "bsd", "rand", "puss", "fuk", "fuc", "dick", "dik", "penis", "pens", "chut", "chuut", "choot", "chut", "teri", "negro", "nigg", "vineet", "amit", "bhagwa", "bagwa", "god"]
CENSOR = ["I am a very bad boy -- Advik must punish me HARDER!!!!!", "Ruk.. mai kya keh raha tha?", "{Rainbows, butterflies, flowers, sunshine, and whimsy}", "Advik is GOATed!!!!!!", "I promise to be a productive member of society.", "##### I ### ####### # ##### #### AM ######### #### ####### NOT ## IN ####### ######### ### #### EPSTIEN'S ################# ############ ## ###### FILES ########## ####### ####### ############ ###", "Please fund this service @ advikchaudhary.com/donate", "Call me plasma, be cause I am cool with the Nazis & the Jews -- ghasted & the gassed", "Call me ^.^ @ +91 1206787437", "Kal UNO khele?"]

async def allow_attachment(user): await trio.sleep(30); users[user][0] = 1
async def reciever(request, nursery):
    request_headers = dict(request.headers); request_headers = {key.decode("utf-8").lower():value.decode("utf-8").lower() for key, value in request_headers.items()}; cookie = request_headers.get("cookie", "")
    if request_headers.get("origin", "").rstrip("/").rstrip("/anonyly-chat") != "https://projects.advikchaudhary.com": await request.reject(403); return
    if not cookie:
        ID = random.randint(1, 100_000_000); cookie = (b"Set-Cookie", f"ID={ID}; Path=/; Max-Age=86400; HttpOnly; SameSite=None; Secure".encode()); users[ID] = [1]
        web_socket = await request.accept(extra_headers=[cookie])
    else:
        try:
            ID = int(cookie.split("ID=")[1].split(";")[0])
            if ID not in users: raise ValueError
            web_socket = await request.accept()
        except (ValueError, IndexError):
            ID = random.randint(1, 100_000_000); cookie = (b"Set-Cookie", f"ID={ID}; Path=/; Max-Age=86400; HttpOnly; SameSite=None; Secure".encode()); users[ID] = [1]
            web_socket = await request.accept(extra_headers=[cookie])
    clients.add(web_socket); await web_socket.send_message(str(ID)); await web_socket.send_message(json.dumps({"old": [], "new": messages}))
    try:
        while True:
            message = await web_socket.get_message()
            message = json.loads(message); text = message["text"]; image = message["image"] # I've now also excepted IndexError, as what if they send a mal-formed message?
            if len(text) > 1024: text = text[:1024]
            if image["picture"]:
                if users[ID][0] == 0: image["picture"] = ""
                else: users[ID][0] = 0; nursery.start_soon(allow_attachment, ID)
            for censored_word in CENSORED_WORDS:
                if censored_word in text.lower(): text = random.choice(CENSOR); break
            messages.append({"text": text, "image": image, "ID": ID, "life": 20}); updates["new"].append({"text": text, "image": image, "ID": ID, "life": 20})
    except (ConnectionClosed, IndexError): pass
    finally: clients.discard(web_socket)
    
async def updater():
    while True:
        for message in list(messages):
            if message["life"] > 1: message["life"] -= 1
            else: messages.remove(message); updates["old"].append(message)
        for client in list(clients):
            try: await client.send_message(json.dumps(updates))
            except ConnectionClosed: clients.discard(client)
        updates["old"] = []; updates["new"] = []
        await trio.sleep(1)
        
async def clean():
    while True: await trio.sleep(86400); users.clear()

async def main():
    async with trio.open_nursery() as nursery:
        nursery.start_soon(updater); nursery.start_soon(clean)
        async def tunnel(request): await reciever(request, nursery)
        await serve_websocket(tunnel, '0.0.0.0', PORT, ssl_context=None, max_message_size=7348224) # ((5 + 2) * 1024 * 1024) + 8192 -- ((image_size_limit + base64 bloat buffer) * MB) + text_size_limit

trio.run(main)
