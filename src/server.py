import asyncio
import random
import struct
import math
from message import Message, RequestMessage, BitfieldMessage, recv_message, PieceMessage
from bitfield import Bitfield
from asyncio import StreamReader, StreamWriter
from manager import Manager


# Which accepts a callback that takes reader and writer
# Reason is so that we can reuse the Message class, which
# functions with reader/writer
class BitTorrentServer:
    def __init__(self, manager: Manager, me_id: str, filename: str) -> None:
        self.manager = manager
        self.me_id = me_id
        self.info_hash = manager.torrent.info_hash
        self.filename = filename

    async def handle_client(self, reader: StreamReader, writer: StreamWriter):
        # Connection to a client just opened. Let's begin by sending our handshake
        # and receiving the handshake of the client.
        try:
            our_handshake: bytes = struct.pack("!B19s8s20s20s", 19, b"BitTorrent protocol",
                                    b"\x00"*8, self.info_hash, bytes(self.me_id, 'utf-8'))
            print("length of our handshake", len(our_handshake))
            writer.write(our_handshake)
            client_handshake: bytes = await reader.readexactly(68) # Assume 68, get the handshake of the client
            await writer.drain() # await the send
            print("Handshake received from client")

        except:
            print("Handshake failed, terminating connection")
            return
        

        bitfield_message: BitfieldMessage = BitfieldMessage(b'\0' * math.ceil(self.manager.total_pieces / 8))
        for i in range(self.manager.total_pieces):
            if self.manager.have_piece(i):
                bitfield_message.bitfield.add_piece(i) # Add pieces that the manager has
        await bitfield_message.send(writer)

        print("Bitfield sent to client")

        # Store choked/unchoked, interested/uninterested
        peer_choked: bool = True
        me_choked: bool = True

        while True:

            print("Waiting for message from client")
            msg: Message = await recv_message(reader)
            print("Message received from client", msg.message_type)

            match msg.message_type:
                case 'CHOKE':
                    me_choked = True
                case 'UNCHOKE':
                    me_choked = False
                case 'INTERESTED':
            
                    msg: Message = Message('UNCHOKE')
                    await msg.send(writer)
                    
                    peer_choked = False

                case 'UNINTERESTED':
                    print("Client is uninterested")
                case 'REQUEST':
                    print("Client requested a piece")
                    if not peer_choked: 
                        print("Client is not choked, sending piece")

                        length = msg.length
                        piece_index = msg.index
                        block_offset = msg.begin
                        
                        print("piece index", piece_index)
                        print("block offset", block_offset)
                        print("length", length)

                        if not self.manager.have_piece(piece_index):
                            print("DO NOT HAVE PIECE")
                            continue

                        
                        start = piece_index * self.manager.torrent.info.piecelength + block_offset
                        end = start + length

                        print("start", start)
                        print("end", end)

                        chunk = retrieve_chunk(self.filename, start, end)    

                        print("chunk retrieved")
                        print("chunk length", len(chunk))
                        print("type chunk", type(chunk))
                        
                        try:
                            msg = PieceMessage(index=piece_index, begin=block_offset, block=chunk)
                        except Exception as e:
                            print("error: ", e)
                            return

                        print("Sending piece to client")
                        await msg.send(writer)
                    

                case _:
                    pass # Ignore other message types, we don't care about them


async def start_server(manager: Manager, me_id: str, filename: str, port: int):

    server_object: BitTorrentServer = BitTorrentServer(manager=manager, me_id=me_id, filename=filename)
    server: asyncio.Server = await asyncio.start_server(server_object.handle_client, '0.0.0.0', port)

    async with server:
        await server.serve_forever()

def retrieve_chunk(filename, start, end):
    with open(filename, 'rb') as file:
        data = file.read()
        chunk = data[start:end]
    return chunk
