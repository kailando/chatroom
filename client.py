#!/usr/bin/env python3.15

import socket
import threading
from sys import argv, exit
from random import randint

SERVER = None
USERNAME = None
LISTEN_PORT = None

def listen_loop(sock):
    while True:
        try:
            msg, _ = sock.recvfrom(4096)
            msg=msg.decode("utf-8")
            if msg=="OK" or msg.startswith("ERR"):
                continue
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
            send_message(sock, f"DCON\n{USERNAME}")
            print("[INFO] Disconnected.")
            break

        elif user_input.strip() == "/recon":
            send_message(sock, f"DCON\n{USERNAME}")
            send_message(sock, f"CONN\n{USERNAME}")

        elif user_input.strip() == "/who":
            send_message(sock, "ALLS")

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
                print("[ERR] Use format: @username message")

        else:
            # Global broadcast
            payload = f"GLOB\n{USERNAME}\n{user_input}"
            send_message(sock, payload)

except KeyboardInterrupt:
    send_message(sock, f"DCON\n{USERNAME}")
    print("\n[INFO] Disconnected by Ctrl+C.")
