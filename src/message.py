from asyncio import StreamReader, StreamWriter
from typing import List
from bitfield import Bitfield
import struct

MESSAGE_TYPES: List[str] = [
    'CHOKE',
    'UNCHOKE',
    'INTERESTED',
    'NOT_INTERESTED',
    'HAVE',
    'BITFIELD',
    'REQUEST',
    'PIECE',
    'CANCEL',
    'PORT'
]

# TODO Added a length_prefix field, let the sublasses override, as the prefix will depend on the child class

class Message:
    def __init__(self, message_type: str):
        self.message_type = message_type
        self.length_prefix = 1
    def __str__(self):
        return "MESSAGE TYPE:"+str(self.message_type)
    def get_length(self):
        return 1
    def send_extra(self, writer: StreamWriter): # To be overridden
        return
    async def send(self, sender: StreamWriter):
        message_id: int = MESSAGE_TYPES.index(self.message_type)
        initial_bytes: bytes = struct.pack("!IB", self.length_prefix, message_id)
        try:
            sender.write(initial_bytes)
            self.send_extra(sender)
            await sender.drain()
        except:
            raise

class HaveMessage(Message):
    def __init__(self, piece_index: int):
        super().__init__('HAVE')
        self.piece_index: int = piece_index
        self.length_prefix: int = 5
    def __str__(self):
        return super().__str__()+f", INDEX: {self.piece_index}"
    def send_extra(self, writer: StreamWriter):
        writer.write(struct.pack("!I", self.piece_index))
        
class BitfieldMessage(Message):
    def __init__(self, bits: bytes):
        super().__init__('BITFIELD')
        self.bitfield: Bitfield = Bitfield(bits)
        self.length_prefix: int = 1 + len(bits)
    def __str__(self):
        return super().__str__()
    def send_extra(self, writer: StreamWriter):
        writer.write(self.bitfield.raw_bytes)

class RequestMessage(Message):
    def __init__(self, index: int, begin: int, length: int):
        super().__init__('REQUEST')
        self.index: int = index
        self.begin: int = begin
        self.length: int = length
        self.length_prefix: int = 13
    def __str__(self):
        return super().__str__()+f", INDEX: {self.index}, BEGIN {self.begin}, LENGTH {self.length}"
    def send_extra(self, writer: StreamWriter):
        s = struct.pack("!III", self.index, self.begin, self.length)
        writer.write(s) # DOUBLE CHECK IF PACK IS CORRECT
        
class CancelMessage(Message): # Request and cancel have same format
    def __init__(self, index: int, begin: int, length: int):
        super().__init__('CANCEL')
        self.index: int = index
        self.begin: int = begin
        self.length: int = length
    def __str__(self):
        return super().__str__()
    def send_extra(self, writer: StreamWriter):
        writer.write(struct.pack("!III", self.index, self.begin, self.length))

class PieceMessage(Message):
    def __init__(self, index: int, begin: int, block: bytes):
        super().__init__('PIECE')
        self.index: int = index
        self.begin: int = begin
        self.block: bytes = block
        self.length_prefix: int = 9 + len(block)
    def __str__(self):
        return super().__str__()+f", INDEX: {self.index}, BEGIN {self.begin}"
    def send_extra(self, writer: StreamWriter):
        writer.write(struct.pack("!II", self.index, self.begin))
        writer.write(self.block)

class PortMessage(Message):
    def __init__(self, port: int):
        super().__init__('PORT')
        self.port: int = port
    def __str__(self):
        return super().__str__()
    def send_extra(self, writer: StreamWriter):
        writer.write(struct.pack("!H", self.port))

async def recv_message(reader: StreamReader) -> Message:
    
    msg_len: int = 0
    while msg_len == 0: # Ignore keepalives, wait until we get one that isn't
        msg_len = int.from_bytes(await reader.readexactly(4), byteorder="big")

    # Get message, extract the type
    msg: bytes = await reader.readexactly(msg_len)
    # print("got while message")

    message_id: int = int(msg[0])

    # Unknown type, handle it
    if (message_id < 0 or message_id > len(MESSAGE_TYPES)):
        print("Unexpected message id " + str(message_id))
        return Message('UNKNOWN')
    
    message_type: str = MESSAGE_TYPES[message_id]

    # These types don't have any extra data
    if message_type in ['CHOKE', 'UNCHOKE', 'INTERESTED', 'NOT_INTERESTED']:
        return Message(message_type=message_type)
    
    # Have contains a piece index
    if message_type == 'HAVE':
        _, piece_index = struct.unpack("!BI", msg)
        return HaveMessage(piece_index)
    
    # Bitfield
    if message_type == 'BITFIELD':
        return BitfieldMessage(msg[1:])
    
    # Request
    if message_type == 'REQUEST':
        _, index, begin, length = struct.unpack("!BIII", msg)
        return RequestMessage(index=index, begin=begin, length=length)
    
    # Piece
    if message_type == 'PIECE':
        _, index, begin, block = struct.unpack("!BII" + str(msg_len - 9) + "s", msg)
        return PieceMessage(index=index, begin=begin, block=block)
    
    # Cancel, same format as request, different type output
    if message_type == 'CANCEL':
        _, index, begin, length = struct.unpack("!BIII", msg)
        return CancelMessage(index=index, begin=begin, length=length)
    
    # Port
    if message_type == 'PORT':
        _, port_number = struct.unpack("!BH", msg)
        return PortMessage(port=port_number)
    
    # Shouldn't ever happen, but here anyway
    print("Unexpected message id " + str(message_id))
    return Message('UNKNOWN')
