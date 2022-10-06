import base64
import binascii
import json
import socket

def IsBase64(s):
    try:
        return base64.b64encode(base64.b64decode(s)) == s
    except Exception:
        return False

# Message to send to the server
class Message:
    """
    This class will convert the data to json, so it can be sent to the server.
    Not every value needs to be set. The server will interpret the type, and use the values accordingly.
    """
    def __init__(self, channel_id: int=0, typ: str="", key: str="", value="", ttl: int=60):
        # Set the channel id
        self.channel_id = channel_id
        # Set type
        self.type = typ
        # Set up the key
        self.key = key
        # Set up value
        # If value contains bytes, encode it to base64. 
        # Json can't handle bytes.
        if type(value) == bytes or type(value) == bytearray:
            self.val = base64.b64encode(value).decode("utf-8")
        else:
            self.val = value
        # Set up the ttl
        self.ttl = ttl

    def to_json(self):
        return json.dumps(self.__dict__)

    def to_dict(self):
        return self.__dict__


class PyConnector:
    def __init__(self, host="127.0.0.1", port=3239, buf_size=2048):
        self.host = host
        self.port = port
        self.buf_size = buf_size
        self.connect()

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((self.host, self.port))
        except socket.error as e:
            raise ConnectionError("PyConnector could not connect to caching server.")

    def send(self, data: Message):
        if type(data) != Message:
            raise TypeError("Data must be of type PyConnector.Message")
        data: str = data.to_json()
        try:
            self.sock.send(data.encode("utf-8"))
        except socket.error as e:
            print("Socket error: {}".format(e))
            try:
                self.connect()
                self.sock.send(data.encode("utf-8"))
            except socket.error as e:
                print("Socket error: {}".format(e))
                return False

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
        return Message(channel_id, typ, key, value, ttl)

class Cache:
    """
    Class for managing the cache.
    Usage of multiple channels is allowed, every channel has it's own cache.
    Will connect to default server IP and port on localhost, if none provided.
    """
    def __init__(self, channel_id: int=0, host="127.0.0.1", port=3239, buf_size=2048):
        self.conn = PyConnector(host, port, buf_size)
        self.channel_id = channel_id

    def SetChannel(self, channel_id):
        """Set the current channel id"""
        self.channel_id = channel_id
        return self
    
    def Set(self, key: str, value, ttl: int=60):
        """Set a value in th currente cache"""
        self.conn.send(self.conn.message(channel_id=self.channel_id, typ="SET", key=key, value=value, ttl=ttl))
        data = self.conn.receive()
        return data["STATUS"] == "OK"

    def Get(self, key: str):
        """Get a value from the current cache"""
        self.conn.send(self.conn.message(channel_id=self.channel_id, typ="GET", key=key))
        data = self.conn.receive()
        if data["STATUS"] == "OK":
            return data["DATA"]["VALUE"]
        return None

    def Delete(self, key: str):
        """Delete a value from the current cache"""
        self.conn.send(self.conn.message(channel_id=self.channel_id, typ="DELETE", key=key))
        data = self.conn.receive()
        return data["STATUS"] == "OK"

    def HasKey(self, key: str):
        """Check if a key exists in the current cache"""
        self.conn.send(self.conn.message(channel_id=self.channel_id, typ="HASKEY", key=key))
        data = self.conn.receive()
        return data["STATUS"] == "OK"
    
    def Keys(self):
        """
        Get all keys in the current cache
        Requires a lot of memory, so use with caution.
        """
        old_bufsize = self.conn.buf_size
        self.conn.buf_size = 128_000 # 128kb buffer size
        self.conn.send(self.conn.message(channel_id=self.channel_id, typ="KEYS"))
        data = self.conn.receive()
        self.conn.buf_size = old_bufsize
        return data["DATA"]["KEYS"]
    
    def SizeAll(self):
        """Get the size of all caches (Multiple channels)"""
        self.conn.send(self.conn.message(channel_id=self.channel_id, typ="SIZEALL"))
        data = self.conn.receive()
        return data["DATA"]["SIZE_ALL"]
    
    def Size(self):
        """Get the size of the current cache"""
        self.conn.send(self.conn.message(channel_id=self.channel_id, typ="SIZE"))
        data = self.conn.receive()
        return data["DATA"]["SIZE"]

    def Clear(self):
        """Clear the current cache"""
        self.conn.send(self.conn.message(channel_id=self.channel_id, typ="CLEAR"))
        data = self.conn.receive()
        return data["STATUS"] == "OK"
    
    def KeysAll(self):
        """
        Get all keys in all caches (Multiple channels)
        Requires a lot of memory, use with caution.
        """
        old_bufsize = self.conn.buf_size
        self.conn.buf_size = 256_000 # 256kb buffer size
        self.conn.send(self.conn.message(channel_id=self.channel_id, typ="KEYSALL"))
        data = self.conn.receive()
        self.conn.buf_size = old_bufsize
        return data["DATA"]["KEYS_ALL"]

    def TTL(self, key: str):
        """Get the TTL of a key in the current cache"""
        self.conn.send(self.conn.message(channel_id=self.channel_id, typ="TTL", key=key))
        data = self.conn.receive()
        return data["DATA"]["TTL"]
    
    def AllTTL(self):
        """Get the TTL of all keys in the current cache"""
        self.conn.send(self.conn.message(channel_id=self.channel_id, typ="TTL_ALL"))
        data = self.conn.receive()
        return data["DATA"]["TTL"]

    def Leave(self):
        """Terminate current connection to server."""
        self.conn.close()


if __name__ == "__main__":
    # Example
    cache = Cache(buf_size=128_000) # 128 KB buffer size (default is 2048)
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
    print("Getting...", cache.Get("test"))
    print("AllTTL...", cache.AllTTL())
    for i in range(1000):
        print("Setting...", cache.Set("test"+str(i), "VALUE"+str(i)))
    import hashlib
    for i in range(1000):
        print("setting hashed...", cache.Set(hashlib.sha256(("test"+str(i)).encode('utf-8')).hexdigest(), "VALUE"+str(i), 120))
    cache.Leave()


