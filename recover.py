import socket
import json
import sys

# --- Configuration ---
HOST = '0.0.0.0'
PORT = 60010

def create_handshake_response_json(our_ip):
    """
    Creates a JSON payload that EXACTLY mimics the original companion app
    to ensure the client accepts the handshake.
    """
    return {
        "acceptedPacketSize": 24576,
        "appInfo": {
            # Mimic the original app's identity
            "appName": "Voice Recorder Companion",
            "appPackage": "pl.mobimax.voicerecorder",
            "appVersionCode": 18061026,
        },
        "canReceiveFile": True,
        "canSendFile": True,
        "device": {
            "batteryLevel": 0, # Match original log
            "deviceIpAddress": our_ip,
            "deviceName": "Python SM-S928U1", # Mimic original
            "deviceType": "phone",
            "exd": "mobile",
            "manufacturerName": "samsung",
            "sys": "android",
        },
        "ipAddress": our_ip
    }

def generate_ack_header(client_header: bytes) -> bytes:
    """
    Generates the correct 8-byte ACK header based on the received client header.
    The rule for this remains the same and does not involve the length.
    """
    if len(client_header) != 8:
        raise ValueError("Client header must be 8 bytes long")
    
    ack = bytearray(client_header)
    ack[0] = 0x07
    ack[4] = client_header[0]
    return bytes(ack)

def recv_all(sock, n):
    """Helper function to ensure we receive exactly n bytes from a socket."""
    data = bytearray()
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data.extend(packet)
    return bytes(data)

def recv_message(sock):
    """
    Reads a full message (header + payload) from the socket.
    The payload length is determined by the last 2 bytes of the header.
    Returns a tuple of (header, payload).
    """
    header = recv_all(sock, 8)
    if not header:
        return None, None
    
    # The last 2 bytes of the header are the payload length (big-endian)
    payload_len = int.from_bytes(header[6:8], 'big')
    
    payload = recv_all(sock, payload_len)
    if not payload:
        return header, None
        
    return header, payload

def handle_connection(conn, addr):
    """Handles the entire file transfer for a single connection."""
    print(f"[+] Connection from {addr[0]}:{addr[1]}")
    
    try:
        # 1. Receive Client Handshake
        print("[*] Waiting for client handshake...")
        client_handshake_header, client_handshake_payload = recv_message(conn)
        if not client_handshake_payload:
            raise ConnectionError("Client disconnected during handshake.")
        
        client_info = json.loads(client_handshake_payload)
        client_packet_size = client_info.get('acceptedPacketSize', 1024)
        print(f"[*] Received handshake from: {client_info['device']['deviceName']} (packet size: {client_packet_size})")

        # 2. Send Server Handshake Response (with correct length)
        print("[*] Sending our handshake response...")
        our_handshake_json = create_handshake_response_json(addr[0])
        response_payload = json.dumps(our_handshake_json, separators=(',', ':')).encode('utf-8')
        payload_len_bytes = len(response_payload).to_bytes(2, 'big')
        
        # The first 6 bytes are static for the handshake response
        response_header = b'\x07\x00\x00\x01\x01\x00' + payload_len_bytes
        
        conn.sendall(response_header + response_payload)
        print("[+] Handshake complete.")

        # 3. Receive File Metadata
        print("[*] Waiting for file metadata...")
        meta_header, meta_payload = recv_message(conn)
        if not meta_payload:
            raise ConnectionError("Client disconnected before sending metadata.")
            
        file_info = json.loads(meta_payload)
        file_name = file_info['fileName']
        file_size = file_info['fileSize']
        print(f"[*] Receiving file: {file_name} ({file_size} bytes)")

        # 4. Send Metadata ACK
        meta_ack_header = generate_ack_header(meta_header)
        conn.sendall(meta_ack_header)
        print(f"[+] Acknowledged metadata. Starting download...")

        # 5. Receive File Data Loop
        bytes_received = 0
        with open(file_name, 'wb') as file_to_write:
            while bytes_received < file_size:
                data_header, chunk_data = recv_message(conn)
                if not chunk_data:
                    raise ConnectionError("Connection lost during data transfer.")

                file_to_write.write(chunk_data)
                bytes_received += len(chunk_data)

                # Send ACK for the received chunk
                data_ack_header = generate_ack_header(data_header)
                conn.sendall(data_ack_header)
                
                progress = (bytes_received / file_size) * 100
                print(f"\r[*] Progress: {bytes_received}/{file_size} bytes ({progress:.2f}%)", end="")

        print("\n[+] File download complete!")

    except (ConnectionResetError, ConnectionAbortedError):
        print("\n[-] Client disconnected unexpectedly.")
    except Exception as e:
        print(f"\n[!] An error occurred: {e}")
    finally:
        conn.close()
        print(f"[-] Connection with {addr[0]} closed.")

def main():
    """Main function to set up the listening socket."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print(f"[*] Listening on {HOST}:{PORT}...")
        
        while True:
            try:
                conn, addr = s.accept()
                handle_connection(conn, addr)
                print(f"\n[*] Ready for another connection on {HOST}:{PORT}...")
            except KeyboardInterrupt:
                print("\n[*] Shutting down server.")
                break

if __name__ == '__main__':
    main()
