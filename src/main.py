#!/usr/bin/env python
# this files takes and processes the file input

import sys, bencode, asyncio, random, string, os
import torrent, manager
from tracker import announce
from manager import Manager
from threading import Thread
from torrent import class_from_dict
from download import start_download
from server import start_server

file = {}

def process_torrent_file(torrent, download_path, file, endgame, compact, me_id, port, ip):
        asyncio.run(start_download(torrent, download_path, file, endgame, compact, me_id, port, ip))
        


# our id for the tracker
me_id = ''.join(random.choice(string.ascii_letters)
                      for i in range(20))

torr_path = sys.argv[1]
download_path = sys.argv[2]

endgame = True if sys.argv[3] == "endgame" else False
compact = True if sys.argv[4] == "compact" else False
ip = sys.argv[5]
port = sys.argv[6]

with open(torr_path, 'rb') as torrent_file:
    torrent_dict = bencode.decode(torrent_file.read())
    torrent = class_from_dict(torrent_dict)
    torr_len = torrent.info.length
    file[torrent.info_hash] = Manager(torrent)
    manager = file[torrent.info_hash]

filename = download_path+"/"+torrent.info.name

# makes thread from command line input
t1 = Thread(target = process_torrent_file, args = (torrent, download_path, manager, endgame, compact, me_id, port, ip))
t1.start()
asyncio.run(start_server(manager, me_id, filename, port))

    #t1.join()
    #manager.left = 0
    #manager.downloaded = 3375104
    

# TODO: make thread to manager incoming connections and piece requests


#for line in sys.stdin:
#    line = line.rstrip("\n")
#    if "start" in line:
#        args = line.split(" ")
#        print('starting server')
#        announce(torrent, me_id, manager.uploaded, manager.downloaded, manager.left, compact, "completed", port, ip) 
#        asyncio.run(start_server(manager, me_id, filename))
#    elif "quit" in line:
#        print("quitting")
#        sys.exit()
#    else:
#        print("Incorrect input format")

