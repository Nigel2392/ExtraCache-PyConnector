# PyConnector
Python connector for the ExtraCache utility.

Optionally takes 4 values:
```
cache = Cache(channel_id, server_ip, port, buffer_size) 
```

Channel ID defaults to: 0
Server IP defaults to: 127.0.0.1
Server Port defaults to: 3239
Buffer size defaults to: 2048

Usage:
```
from PyConnector import Cache

cache = Cache()

# Set the cache
cache.Set("test", b"test")

# Get from cache
cache.Get("test")

# Delete key from cache
cache.Delete("test")

# Check if cache has key
cache.HasKey("test")

# Retrieve all keys
cache.Keys()

# Retrieve amount of all keys in all caches
cache.SizeAll()

# Retrieve amount of all keys in current cache
cache.Size()

# Clear entire cache
cache.Clear()

# Get all geys for all caches
cache.KeysAll()

# Get ttl for key
cache.TTL("test")

# Get ttl for all items
cache.AllTTL()

# Change channel
# cache.SetChannel(1)

# Disconnect from socket
cache.Leave()
```
