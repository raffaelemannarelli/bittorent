import asyncio, random
from bitfield import Bitfield
# Manages our pieces recieved, tells us
# what we have
# what we need
class Manager:

    def __init__(self, torrent):
        self.torrent = torrent
        self.peer_bitfield = {}
        self.total_pieces = len(torrent.info.pieces)//20
        self.our_bitfield = [0]*self.total_pieces 
        self.pending_pieces = []
        self.queue = list(range(self.total_pieces))
        self.complete = False # boolean telling us if file is complete
        self.uploaded = 0
        self.downloaded = 0
        self.left = torrent.info.length

    # Adding peer to our dictionary once we recieve its bitmap
    def add_peer(self, peer_id, bitfield):
        self.peer_bitfield[peer_id] = bitfield
    
    def remove_peer(self, peer_id):
        if peer_id in self.peer_bitfield:
            del self.peer_bitfield[peer_id]

    # Updating in response to Have message
    def update_peer(self, peer_id, index):
        if peer_id in self.peer_bitfield:
            self.peer_bitfield[peer_id].add_piece(index)

    def get_random_pending(self):
        try:
            return random.choice(self.pending_pieces)
        except:
            return None
            
    # determine what the next request will be for given peer
    def next_request(self, peer_id):
        try:
            for index, piece_number in enumerate(self.queue):
                if self.peer_bitfield[peer_id].has_piece(piece_number) == True:
                    val = self.queue.pop(index)
                    self.pending_pieces.append(val)
                    return val
            return -1
        except: 
            print("error; piece probably not found")

    def update_me(self, index):
        self.our_bitfield[index] = 1
        self.downloaded += self.torrent.info.piecelength
        self.left -= self.torrent.info.piecelength
        

    def return_to_queue(self, index):
        try:
            self.pending_pieces.remove(val)
        except:
            return
        self.queue.append(index)

    def downloaded_piece(self, val):
        try:
            self.pending_pieces.remove(val)
        except:
            return
        self.update_me(val)

    def have_piece(self, val):
        if (self.our_bitfield[val] == 1):
            return True
        return False
        
    def download_done(self):
        if (self.complete):
            return True
        for i in self.our_bitfield:
            if i == 0:
                return False
        self.complete = True
        return True
        
