import trio; from trio_websocket import serve_websocket, ConnectionClosed; import os; import json; import random

clients = set(); users = dict(); PORT = int(os.environ.get("PORT", 10000))
messages = []; updates = {"old": [], "new": []}
CENSORED_WORDS = ["gaand", "gand", "laude", "lode", "chod", "bhosdi", "bsd", "rand", "puss", "fuk", "fuc", "dick", "dik", "penis", "pens", "chut", "chuut", "choot", "chut", "teri", "negro", "nigg", "vineet", "amit", "bhagwa", "bagwa", "god"]
CENSOR = ["I am a very bad boy -- Advik must punish me HARDER!!!!!; So, I can re-turn to be a gooooddd boooyyy~", "Ruk.. mai kya keh raha tha?", "{Rainbows, butterflies, flowers, sunshine, and whimsy}", "Advik is GOATed!!!!!!", "I promise to be a productive member of society.", "##### I ### ####### # ##### #### AM ######### #### ####### NOT ## IN ####### ######### ### #### EPSTIEN'S ################# ############ ## ###### FILES ########## ####### ####### ############ ###", "Please fund this service @ advikchaudhary.com/donate", "Call me plasma, be cause I am cool with the Nazis & the Jews -- ghasted & the gassed", "Call me ^.^ @ +91 1206787437", "Kal UNO khele?"]
print("variables defined", flush=True)

async def allow_attachment(user): await trio.sleep(30); users[user][0] = 1; print(f"allowed attachment for {user}", flush=True)
async def reciever(request, nursery):
    request_headers = dict(request.headers); request_headers = {key.decode("utf-8").lower():value.decode("utf-8").lower() for key, value in request_headers.items()}; cookie = request_headers.get("cookie", "").lower(); print(f"raw cookie: {cookie}", flush=True)
    if request_headers.get("origin", "").rstrip("/").rstrip("/anonyly-chat") != "https://projects.advikchaudhary.com": await request.reject(403); print("rejected alien", flush=True); return
    if not cookie:
        print("raw cookie is blank -- no cookie. Creating cookie and sending it back", flush=True)
        ID = random.randint(1, 100_000_000); cookie = (b"Set-Cookie", f"ID={ID}; Path=/; Max-Age=86400; HttpOnly; SameSite=None; Secure".encode()); users[ID] = [1]; print("ID registered", flush=True); print(users, flush=True)
        web_socket = await request.accept(extra_headers=[cookie]); print("connection formed", flush=True)
    else:
        print("raw cookie has some thing", flush=True)
        try:
            ID = int(cookie.split("id=")[1].split(";")[0])
            print("ID valid", flush=True)
            if ID not in users: print("ID incorrect", flush=True); raise ValueError
            web_socket = await request.accept(); print("connection formed", flush=True)
        except (ValueError, IndexError):
            print("ID invalid or incorrect. Creating cookie and sending it back", flush=True)
            ID = random.randint(1, 100_000_000); cookie = (b"Set-Cookie", f"ID={ID}; Path=/; Max-Age=86400; HttpOnly; SameSite=None; Secure".encode()); users[ID] = [1]; print("ID registered", flush=True); print(users, flush=True)
            web_socket = await request.accept(extra_headers=[cookie]); print("connection formed", flush=True)
    clients.add(web_socket); await web_socket.send_message(str(ID)); await web_socket.send_message(json.dumps({"old": [], "new": messages})); print("web_socket registered, updated with ID & messages", flush=True)
    try:
        while True:
            message = await web_socket.get_message()
            message = json.loads(message); text = message["text"]; image = message["image"]
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
        print("initiated updater & cleaner", flush=True)
        async def tunnel(request): await reciever(request, nursery)
        await serve_websocket(tunnel, '0.0.0.0', PORT, ssl_context=None, max_message_size=7348224) # ((5 + 2) * 1024 * 1024) + 8192 -- ((image_size_limit + base64 bloat buffer) * MB) + text_size_limit
        print("serve_websocket", flush=True)

trio.run(main)
