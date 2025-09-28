#!/usr/bin/env python3.13
# -*- coding=utf-8 -*-
# pyright: reportAttributeAccessIssue=false

import socketserver
from sys import argv, exit

class Handler(socketserver.BaseRequestHandler):
    def handle(self):
        # UDPServer: self.request == (data_bytes, client_address)
        data_bytes, sock = self.request
        client_address = self.client_address
        data = data_bytes.decode("utf-8").splitlines(keepends=False)

        cmd = data[0]

        if cmd == "CONN":
            username = data[1]
            print(f"New user named '{username}'")
            # Store the client address tuple, NOT the socket!
            if not username in list(self.server.data["connected_users"].keys()):
                self.server.data["connected_users"][username] = client_address
                self.server.socket.sendto(b"OK", client_address)
            else:
                self.server.socket.sendto(b"ERR:TOOK", client_address)

        elif cmd == "DCON":
            username = data[1]
            print(f"'{username}' disconnected")
            try:
                del self.server.data["connected_users"][username]
                self.server.socket.sendto(b"OK", client_address)
            except KeyError:
                self.server.socket.sendto(b"ERR:USER", client_address)

        elif cmd == "GLOB":
            sender = data[1]
            msg_text = '\n'.join(data[2:])
            msg_raw = f"[{sender}]: {msg_text}"
            msg = msg_raw.encode("utf-8")
            print(msg_raw)
            for _, addr in self.server.data["connected_users"].items():
                #if name != sender:
                    self.server.socket.sendto(msg, addr)

        elif cmd == "PERS":
            sender = data[1]
            recipient = data[2]
            msg_text = '\n'.join(data[3:])
            msg_raw = f"[{sender} -> {recipient}]: {msg_text}"
            msg = msg_raw.encode("utf-8")
            print(msg_raw)
            try:
                addr = self.server.data["connected_users"][recipient]
                self.server.socket.sendto(msg, addr)
                self.server.socket.sendto(msg, )
            except KeyError:
                self.server.socket.sendto(b"ERR:USER", client_address)

        elif cmd == "ALLS":
            print(f"person listing to {data[1]}")
            self.server.socket.sendto(("\n".join(self.server.data["connected_users"].keys())).encode("utf-8"), client_address)

        # Too OP, hacked clients could ALLS -> KICK and clear the server, and I deleted modbot
        #elif cmd == "KICK":
        #    username = data[1]
        #    print(f"'{username}' disconnected")
        #    try:
        #        del self.server.data["connected_users"][username]
        #        self.server.socket.sendto(b"EEND", client_address)
        #    except KeyError:
        #        self.server.socket.sendto(b"ERR:USER", client_address)

        else:
            self.server.socket.sendto(b"ERR:UNKNOWN_CMD", client_address)


class DataUDPServer(socketserver.UDPServer):
    def __init__(self, server_address, handler_class):
        self.data = {"connected_users": {}}
        super().__init__(server_address, handler_class)


if len(argv) < 3:
    print(f"Usage: {argv[0]} <host> <port>")
    exit(1)

host, port = argv[1], int(argv[2])
print(f"Server listening on {host}:{port}")

server = DataUDPServer((host, port), Handler)
try:
    server.serve_forever()
except BaseException:
    server.server_close()
    server.shutdown()
