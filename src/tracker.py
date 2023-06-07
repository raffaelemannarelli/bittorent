import bencode, socket
from peer import PeerData, Peer

# this file is responsible for handling getting the tracker list

def announce(torrent, peer_id, uploaded, downloaded, left, compact, event, port, ip):
    # connect to address from torrent url
    sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    url_no_http = torrent.announce.split("://")[1]
    torr_url = url_no_http.split(":")[0]
    torr_port = url_no_http.split(":")[1].split("/")[0]
    #print(torr_port)
    torr_ip = socket.gethostbyname(torr_url)
    #print("{}:{}".format(torr_url,torr_port))
    #print(torr_ip)

    # construct http get request
    # TODO: should first ensure port is free
    str = "GET /announce"
    #print(torrent.info_hash)
    hash_string = hex_string(list(torrent.info_hash))
    str += "?info_hash={}".format(hash_string)
    str += "&peer_id={}".format(peer_id)
    str += "&port={}".format(port)
    str += f"&uploaded={uploaded}"
    str += f"&downloaded={downloaded}"
    str += f"&left={left}"
    if compact:
        str += "&compact=1"
    str += f"&event={event}"
    str += " HTTP/1.1\r\n"
    # TODO: generalize this, but doesn't seem
    # to hurt communication with debian tracker
    str += f"host:cerf.cs.umd.edu:8000\r\n\r\n"
    #print(str)

    #print(str.encode('utf-8'))
    
    # send http get request
    sock.connect((torr_ip, int(torr_port)))
    sock.sendall(str.encode('utf-8'))

    buf = []
    
    # set longer than possible, until value known
    content_len = 1000000000
    r = 0

    while content_len - r > 0:
        block = sock.recv(content_len-r)
        #print(block)
        r += len(block)
        buf.append(block)            
        
        if content_len == 1000000000 and r > 78:
            temp = b''.join(buf)
            content_len = int(temp.split(b"Content-Length: ")[1].split(b"\r\n")[0]) + 102 # 102 was working???
            if compact:
                content_len = content_len - 1
                
    buf = b''.join(buf)
    sock.close()
    #print(buf)
    #print("got {} bytes".format(len(buf)))
    peer_res = buf.split(b"\r\n\r\n")[1]
    return PeerData(bencode.decode(peer_res), ip)


# # # # # # # # # # # # # # # # # # # # # #
# HELPER FUNCTIONS TO FORMAT HEX FOR URLS #
# # # # # # # # # # # # # # # # # # # # # #
def hex_string(arr):
    str = ""
    
    for i in arr:
        str += value_from_int(i)
    return str

def value_from_int(i):
    if i >= ord('0') and i <= ord('9'):
        return chr(i)
    if i >= ord('a') and i <= ord('z'):
        return chr(i)
    if i >= ord('A') and i <= ord('Z'):
        return chr(i)
    if i == ord('.') or i == ord('-') or i == ord('_') or i == ord('~'):
        return chr(i)
    if i == ord(' '):
        return '+'
    str = "%"
    str += letter_from_int(i//16)
    str += letter_from_int(i%16)
    return str

def letter_from_int(i):
    if (i >= 10 and i <= 16):
        return chr(ord('A')-10+i)
    if (i >= 0 and i <= 9):
        return chr(ord('0')+i)
