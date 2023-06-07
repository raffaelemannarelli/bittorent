import asyncio
from message import Message, RequestMessage, BitfieldMessage, recv_message
import message

async def send_handshake(reader, writer):

    # Constructing the handshake message
    protocol_name_length = b'\x13'  # 19 in decimal
    protocol_name = b'BitTorrent protocol'
    reserved_bytes = b'\x00' * 8  # 8 reserved bytes
    info_hash = b'\x00' * 20  # 20 reserved bytes
    peer_id = b'\x00' * 20  # 20 reserved bytes

    handshake = protocol_name_length + protocol_name + reserved_bytes + info_hash + peer_id
    writer.write(handshake)

    await writer.drain()



async def main():

    reader, writer = await asyncio.open_connection('127.0.0.1', 6881)

    print("sending handshake")
    await send_handshake(reader, writer)
    print('handshake sent')

    print("waiting for handshake")
    server_handshake: bytes = await reader.readexactly(68)
    print("handshake received")

    print("sending interested")
    msg = Message('INTERESTED')
    await msg.send(writer)
    print('interested sent')

    me_choked = True
    received_bitfield = False
    bitfield = []

    piece_index = 0
    offset = 0
    length = 16384


    while True:
        msg = await recv_message(reader)

        if msg.message_type == 'BITFIELD':
            bitfield = msg.bitfield
            received_bitfield = True

        elif msg.message_type == 'PIECE':
            print('received piece')

        elif msg.message_type == 'UNCHOKE':
            me_choked = False
            
        if not me_choked and received_bitfield:
            print('sending request')
            msg = RequestMessage(piece_index, offset, length)
            await msg.send(writer)
            print('request sent')
            

    writer.close()

if __name__ == '__main__':
    asyncio.run(main())