import base64
import binascii
import json
from socket import socket, AF_INET, SOCK_STREAM

def IsBase64(s):
    try:
        return base64.b64encode(base64.b64decode(s)) == s
    except Exception:
        return False

class PyConnector:
    def __init__(self, host="127.0.0.1", port=3239, buf_size=2048):
        self.host = host
        self.port = port
        self.buf_size = buf_size
        self.sock = socket(AF_INET, SOCK_STREAM)
        self.sock.connect((self.host, self.port))

    def send(self, data):
        data = json.dumps(data)
        self.sock.send(data.encode("utf-8"))

    def receive(self):
        data = self.sock.recv(self.buf_size)
        data_json = data.decode("utf-8")
        data_dict = json.loads(data_json)
        try:
            if type(data_dict["DATA"]["VALUE"]) == str:
                try:
                    encoded = data_dict["DATA"]["VALUE"].encode('utf-8')
                except AttributeError:
                    pass
                else:
                    if IsBase64(encoded):
                        data_dict["DATA"]["VALUE"] = base64.b64decode(encoded)
        except KeyError:
            pass
        except binascii.Error:
            pass
        return data_dict

    def close(self):
        self.sock.close()

    def message(self, channel_id: int=0, typ: str="", key: str="", value="", ttl: int=60):
        # Check if value is of type bytes
        if type(value) == bytes or type(value) == bytearray:
            value = base64.b64encode(value).decode("utf-8")

        return {
            "channel_id": channel_id,
            "type": typ,
            "key": key,
            "val": value,
            "ttl": ttl
        }

class Cache:
    def __init__(self, channel_id: int=0, host="127.0.0.1", port=3239, buf_size=2048):
        self.conn = PyConnector(host, port, buf_size)
        self.channel_id = channel_id

    def SetChannel(self, channel_id):
        self.channel_id = channel_id
        return self
    
    def Set(self, key: str, value, ttl: int=60):
        self.conn.send(self.conn.message(channel_id=self.channel_id, typ="SET", key=key, value=value, ttl=ttl))
        data = self.conn.receive()
        return data["STATUS"] == "OK"

    def Get(self, key: str):
        self.conn.send(self.conn.message(channel_id=self.channel_id, typ="GET", key=key))
        data = self.conn.receive()
        if data["STATUS"] == "OK":
            return data["DATA"]["VALUE"]
        return None

    def Delete(self, key: str):
        self.conn.send(self.conn.message(channel_id=self.channel_id, typ="DELETE", key=key))
        data = self.conn.receive()
        return data["STATUS"] == "OK"

    def HasKey(self, key: str):
        self.conn.send(self.conn.message(channel_id=self.channel_id, typ="HASKEY", key=key))
        data = self.conn.receive()
        return data["STATUS"] == "OK"
    
    def Keys(self):
        self.conn.send(self.conn.message(channel_id=self.channel_id, typ="KEYS"))
        data = self.conn.receive()
        return data["DATA"]["KEYS"]
    
    def SizeAll(self):
        self.conn.send(self.conn.message(channel_id=self.channel_id, typ="SIZEALL"))
        data = self.conn.receive()
        return data["DATA"]["SIZE_ALL"]
    
    def Size(self):
        self.conn.send(self.conn.message(channel_id=self.channel_id, typ="SIZE"))
        data = self.conn.receive()
        return data["DATA"]["SIZE"]

    def Clear(self):
        self.conn.send(self.conn.message(channel_id=self.channel_id, typ="CLEAR"))
        data = self.conn.receive()
        return data["STATUS"] == "OK"
    
    def KeysAll(self):
        self.conn.send(self.conn.message(channel_id=self.channel_id, typ="KEYSALL"))
        data = self.conn.receive()
        return data["DATA"]["KEYS_ALL"]

    def TTL(self, key: str):
        self.conn.send(self.conn.message(channel_id=self.channel_id, typ="TTL", key=key))
        data = self.conn.receive()
        return data["DATA"]["TTL"]
    
    def AllTTL(self):
        self.conn.send(self.conn.message(channel_id=self.channel_id, typ="TTL_ALL"))
        data = self.conn.receive()
        return data["DATA"]["TTL"]

    def Leave(self):
        self.conn.close()



if __name__ == "__main__":
    # Example
    cache = Cache()
    print("Setting...", cache.Set("test", b"test"))
    print("Getting...", cache.Get("test"))
    print("Deleting...", cache.Delete("test"))
    print("HasKey...", cache.HasKey("test"))
    print("Keys...", cache.Keys())
    print("Getting...", cache.Get("test"))
    print("Setting...", cache.Set("test", "VALUE"))
    print("HasKey...", cache.HasKey("test"))
    print("Keys...", cache.Keys())
    print("SizeAll...", cache.SizeAll())
    print("Size...", cache.Size())
    print("Clear...", cache.Clear())
    print("KeysAll...", cache.KeysAll())
    print("Setting...", cache.Set("test", "VALUE"))
    print("HasKey...", cache.HasKey("test"))
    print("Keys...", cache.Keys())
    print("TTl...", cache.TTL("test"))
    print("AllTTL...", cache.AllTTL())
    cache.Leave()


