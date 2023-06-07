import bencode, asyncio, struct, asyncio
import message
# this file manages structures to hold peer data

MAX_BYTES = 16384

CHOKE_ID = 0
UNCHOKE_ID = 1
INTERESTED_ID = 2
NOT_INTERESTED_ID = 3
HAVE_ID = 4
BITFIELD_ID = 5
REQUEST_ID = 6
PIECE_ID = 7

class PeerData:
    def __init__(self, response, ip):
            self.interval = response['interval']
            self.peers = generate_list(response['peers'], ip)
    def __str__(self):
        return "response:\n  interval: "+str(self.interval)+"\n"+peer_list_str(self.peers)

class Peer:
    def __init__(self, peer, ip):
        self.ip = peer['ip'] if isinstance(peer, dict) else '.'.join(str(c) for c in peer[0:4])
        if (self.ip == ip):
            print("OWN IP")
            self.ip = '127.0.0.1'
        self.port = peer['port'] if isinstance(peer, dict) else int(peer[4]) << 8 | int(peer[5])
        self.peer_id = None
        self.choked = True
        self.interested = False
        self.reader = None
        self.writer = None
        self.throughput = 0
        self.bitmap_received = False
        
    def __str__(self):
        return "  peer: "+str(self.ip)+":"+str(self.port) + "\n"

    async def connect(self):
        print("connecting to "+str(self.ip)+":"+str(self.port))
        t = asyncio.open_connection(self.ip, self.port)
        try:
            self.reader, self.writer = await asyncio.wait_for(t, timeout=10)
        except:
            raise
        print("connected to "+str(self.ip)+":"+str(self.port))

    async def handshake(self, info_hash, peer_id):
        handshake = struct.pack("!B19s8s20s20s", 19, b"BitTorrent protocol",
                                b"\x00"*8, info_hash, bytes(peer_id, 'utf-8'))
        try:
            await self.write(handshake)
            r = await self.readexactly(68)
        except:
            raise
        # note: should probably verify fields
        pstrlen, pstr, reserved, info_hash, self.peer_id = struct.unpack(
            "!B19s8s20s20s", r)

    async def write(self, msg):
        try:
            self.writer.write(msg)
            await self.writer.drain()
        except:
            raise

    async def readexactly(self,len):
        try:
            r = await self.reader.readexactly(len)
            return r
        except:
            raise
        
    async def close(self):
        try:
            self.writer.close()
            await self.writer.wait_closed()
        except:
            print("error during close")
        
    async def read_msg(self):
        try:
            return await message.recv_message(self.reader)
        except:
            raise
                    
    async def send_interested(self):
        # print('sending interested')
        try:
            msg = message.Message('INTERESTED')
            await msg.send(self.writer)
        except:
            return

    async def send_cancel(self):
        # print('sending interested')
        try:
            msg = message.Message('CANCEL')
            await msg.send(self.writer)
        except:
            return
        
    async def send_msg_request(self, index, length):

        offset = 0

        try:
            while offset < length:
                chunk_size = min(MAX_BYTES, length - offset)
                msg = message.RequestMessage(index, offset, chunk_size)
                await msg.send(self.writer)
                offset += chunk_size
        except:
            print("Error sending piece requests")


# # # # # # # # # # #
# HELPER  FUNCTIONS #
# # # # # # # # # # #

def generate_list(peer_data, ip):
    if isinstance(peer_data, bytes):
        return [Peer(peer_data[6*x:6*x+6], ip) for x in range(int(len(peer_data) / 6))]
    else:
        list = []
        for i in range(len(peer_data)):
            list.append(Peer(peer_data[i], ip))
        return list

def peer_list_str(list):
    s = ""
    for i in range(len(list)):
        s += str(list[i])
    return s
