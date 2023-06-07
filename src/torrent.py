import hashlib, bencode

# this file defines torrent and info classes for more
# convenient storage

class Torrent:
    def __init__(self, torrent):
        self.info_hash = hash(bencode.bencode(torrent['info']))
        self.info = Info(torrent['info'])
        self.announce = torrent['announce']
    def __str__(self):
        return "torrent:\n"+str(self.info)+"  announce: "+self.announce
    
class Info:
    def __init__(self, info):
        self.piecelength = info['piece length']
        self.pieces = info['pieces']
        self.name = info['name']
        self.length = info['length']
    def __str__(self):
        return "  info: \n"+"    name: "+self.name+"\n"+"    length: "+str(self.length)+"\n"

def class_from_dict(torrent_file):
    return Torrent(torrent_file)
    
def hash(value):
    sha1 = hashlib.sha1()
    sha1.update(value)
    hex = sha1.digest()
    #print(hex)
    return hex
