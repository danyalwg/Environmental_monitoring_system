import network
import espnow
import json

# --- Initialization ----------------------------------------------------------
# Initialize the station interface (STA mode)
_sta = network.WLAN(network.STA_IF)
_sta.active(True)

# Initialize ESP-NOW and activate it
_e = espnow.ESPNow()
_e.active(True)


# --- Peer Management ---------------------------------------------------------
def add_peer(peer_mac):
    """
    Add a peer to the ESP-NOW instance.
    
    :param peer_mac: Receiver's MAC address as bytes, e.g. b'\x14\x2b\x2f\xc4\xc7\x5c'
    """
    try:
        _e.add_peer(peer_mac)
        print("Added peer:", peer_mac)
    except Exception as ex:
        print("Failed to add peer:", ex)


# --- Data Transmission -------------------------------------------------------
def send_packet(packet, peer_mac=None):
    """
    Convert a dictionary to a JSON string and send it via ESP-NOW.
    
    :param packet: The dictionary to send (e.g., your sensor packet).
    :param peer_mac: Optional; if not provided, uses the first peer in _e.peers().
    """
    # Convert the dictionary into a JSON string
    json_str = json.dumps(packet)
    
    # If no peer is provided, try using the first added peer.
    if peer_mac is None:
        peers = list(_e.peers())
        if not peers:
            print("No peers available to send!")
            return
        peer_mac = peers[0]
    
    try:
        # Send the JSON data as bytes
        _e.send(peer_mac, json_str.encode())
        print("Sent packet to", peer_mac)
    except Exception as ex:
        print("Error sending packet:", ex)


# --- Data Reception ----------------------------------------------------------
def receive_packet():
    """
    Block until a packet is received via ESP-NOW.
    
    :return: A tuple (sender_mac, packet_dict) where packet_dict is the decoded JSON data.
             If decoding fails, packet_dict is None.
    """
    sender_mac, msg = _e.recv()  # This is a blocking call.
    if msg:
        try:
            json_str = msg.decode()
            packet = json.loads(json_str)
            return sender_mac, packet
        except Exception as ex:
            print("Error decoding JSON packet:", ex)
            return sender_mac, None
    return None, None
