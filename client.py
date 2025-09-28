#!/usr/bin/env python3.13
# -*- coding=utf-8 -*-

import socket
import threading
from sys import argv, exit
from random import randint

SERVER = None
USERNAME = None
LISTEN_PORT = None

def disconnect(*args, sock=None, **kwargs):
    send_message(sock, f"DCON\n{USERNAME}")
    print("[INFO] Disconnected.")
    sock.shutdown() # pyright: ignore[reportOptionalMemberAccess]
    exit(*args, **kwargs)

def listen_loop(sock):
    while True:
        try:
            msg, _ = sock.recvfrom(4096)
            msg=msg.decode("utf-8")
            if msg=="OK":
                continue
            if msg.startswith("ERR"):
                match msg:
                    case "ERR:USER":
                        print("! User does not exist")
                    
                    case "ERR:UNKNOWN_CMD":
                        print("! Client error - malformed request")
                    
                    case "ERR:TOOK":
                        print("! Username took")
                        disconnect(1, sock=sock)
                continue
                    
            if msg=="EEND":
                print("Kicked off.")
                sock.shutdown()
                break
            print(f"\r{msg}", end="\n> ")
        except Exception as e:
            print(f"[ERR] Listener crashed: {e}")
            break

def send_message(sock, msg):
    sock.sendto(msg.encode("utf-8"), SERVER)

if len(argv) < 5:
    print(f"Usage: {argv[0]} <server_host> <server_port> <username> <client_port>")
    exit(1)

SERVER = (argv[1], int(argv[2]))
USERNAME = argv[3]
LISTEN_PORT = int(argv[4])

# --- Set up UDP socket ---
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", LISTEN_PORT))

# --- Start listener thread ---
threading.Thread(target=listen_loop, args=(sock,), daemon=True).start()

# --- Register with server ---
send_message(sock, f"CONN\n{USERNAME}")
print(f"[INFO] Connected as '{USERNAME}'. Type /quit to disconnect.")

try:
    while True:
        user_input = input("> ")
        if user_input.strip() == "/quit":
            disconnect(0, sock=sock)

        elif user_input.strip() == "/help":
            print("Commands:")
            print("/quit - exit kindly; you also may use Ctrl+C")
            print("/help - show this message")
            print("/recon - disconnect and reconnect w/ the same name")
            print("/name <new_name> - same as /recon but with a different name; you may use spaces in your new")
            print("  name at the cost of not being able to be DMed")
            print("/who - Get a listing of everyone")
            print("/roll ndx - roll n of a dice with x sides")
            print("/roll dx - same as /roll 1dx")
            print("/roll x - same as /roll dx")
            print()
            print("DMing:")
            print("Use @username message to send a private DM.")
            print("If the user doesn't exist, prints '! User does not exist'")
            print("It's unaccessable to every user except you and the reciptent - the server literally doesn't send it.")
            print("But the server logs it.")

        elif user_input.strip() == "/recon":
            send_message(sock, f"DCON\n{USERNAME}")
            send_message(sock, f"CONN\n{USERNAME}")

        elif user_input.strip() == "/name":
            try:
                _, name = user_input.split(" ", 1)
                send_message(sock, f"DCON\n{USERNAME}")
                USERNAME = name
                send_message(sock, f"CONN\n{USERNAME}")
            except ValueError:
                print("! Use format: /name new username\nSpaces are allowed")
        
        elif user_input.strip() == "/who":
            send_message(sock, f"ALLS\n{USERNAME}")

        elif user_input.strip().startswith("/roll"):
            _, die = tuple(user_input.strip().split())
            if (die[0].isdigit()) and ("d" in die):
                die = die.split("d")
                times = int(die[0])
                die = int(die[1])
                for _ in range(times):
                    roll = randint(1, die)
                    print(f"You got a {roll}!")
                    payload = f"GLOB\n{USERNAME}\nI rolled a d{die} and got {roll}!"
                    send_message(sock, payload)
            else:
                die = int(die.removeprefix("d"))
                roll = randint(1, die)
                print(f"You got a {roll}!")
                payload = f"GLOB\n{USERNAME}\nI rolled a d{die} and got {roll}!"
                send_message(sock, payload)

        elif user_input.startswith("@"):
            # Personal message: format @recipient message
            try:
                recipient, msg = user_input[1:].split(" ", 1)
                payload = f"PERS\n{USERNAME}\n{recipient}\n{msg}"
                send_message(sock, payload)
            except ValueError:
                print("! Use format: @username message")

        else:
            # Global broadcast
            payload = f"GLOB\n{USERNAME}\n{user_input}"
            send_message(sock, payload)

except (KeyboardInterrupt, EOFError):
    print("\n[INFO] Disconnected by Ctrl+C.")
    disconnect(0, sock=sock)