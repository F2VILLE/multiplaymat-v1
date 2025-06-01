import socket
import threading
import pickle
import struct
import cv2
import signal
import sys
import argparse
from queue import Queue
import time

class WebcamStreamer:
    def __init__(self, receive_port=5000, send_port=5001, send_to_ip='127.0.0.1'):
        self.receive_port = receive_port
        self.send_port = send_port
        self.send_to_ip = send_to_ip
        
        
        self.running = False
        
        
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            raise RuntimeError("Could not open webcam")
            
        
        self.frame_queue = Queue(maxsize=1)
            
        
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def signal_handler(self, sig, frame):
        """Handle shutdown signals gracefully"""
        print("\nShutting down gracefully...")
        self.running = False
        self.cleanup()
        sys.exit(0)
        
    def cleanup(self):
        """Clean up resources"""
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()
        if hasattr(self, 'receive_socket'):
            self.receive_socket.close()
        if hasattr(self, 'send_socket'):
            self.send_socket.close()
        cv2.destroyAllWindows()
        
    def start(self):
        """Start the streaming threads"""
        self.running = True
        
        
        receive_thread = threading.Thread(target=self.receive_frames, daemon=True)
        receive_thread.start()
        
        
        send_thread = threading.Thread(target=self.send_frames, daemon=True)
        send_thread.start()
        
        
        self.display_frames()
        
    def receive_frames(self):
        """Socket server to receive frames"""
        self.receive_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.receive_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.receive_socket.bind(('0.0.0.0', self.receive_port))
        self.receive_socket.listen(1)
        
        print(f"Receiver started on port {self.receive_port}, waiting for connection...")
        conn, addr = self.receive_socket.accept()
        print(f"Connected by {addr}")
        
        data = b""
        payload_size = struct.calcsize(">L")
        
        while self.running:
            try:
                
                while len(data) < payload_size:
                    data += conn.recv(4096)
                    
                packed_msg_size = data[:payload_size]
                data = data[payload_size:]
                msg_size = struct.unpack(">L", packed_msg_size)[0]
                
                
                while len(data) < msg_size:
                    data += conn.recv(4096)
                    
                frame_data = data[:msg_size]
                data = data[msg_size:]
                
                
                frame = pickle.loads(frame_data)
                
                
                if self.frame_queue.full():
                    self.frame_queue.get_nowait()
                self.frame_queue.put(frame)
                    
            except (ConnectionResetError, BrokenPipeError):
                print("Connection lost")
                break
            except Exception as e:
                print(f"Receive error: {e}")
                break
                
        conn.close()
        
    def send_frames(self):
        """Socket client to send frames"""
        self.send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        print(f"Sender trying to connect to {self.send_to_ip}:{self.send_port}...")
        while self.running:
            try:
                self.send_socket.connect((self.send_to_ip, self.send_port))
                print("Sender connected!")
                break
            except ConnectionRefusedError:
                print(f"Could not connect to {self.send_to_ip}:{self.send_port}, retrying...")
                time.sleep(1)
                continue
            except Exception as e:
                print(f"Connection error: {e}")
                self.running = False
                return
                
        while self.running:
            try:
                ret, frame = self.cap.read()
                if not ret:
                    print("Failed to capture frame")
                    break
                    
                
                data = pickle.dumps(frame)
                
                
                message_size = struct.pack(">L", len(data))
                
                
                self.send_socket.sendall(message_size + data)
                
                
                time.sleep(0.01)
                
            except Exception as e:
                print(f"Send error: {e}")
                break
                
    def display_frames(self):
        """Display frames in the main thread"""
        while self.running:
            try:
                if not self.frame_queue.empty():
                    frame = self.frame_queue.get_nowait()
                    cv2.imshow("Received Stream", frame)
                
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    self.running = False
                    break
                    
            except Exception as e:
                print(f"Display error: {e}")
                break
                
        self.cleanup()
        
    def __del__(self):
        self.cleanup()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Webcam Streamer")
    parser.add_argument('--receive-port', type=int, default=5000, help="Port to receive frames on")
    parser.add_argument('--send-port', type=int, default=5001, help="Port to send frames to")
    parser.add_argument('--send-to-ip', type=str, default='127.0.0.1', help="IP address to send frames to")
    
    args = parser.parse_args()
    
    
    if args.receive_port == args.send_port:
        print("Error: Receive port and send port must be different")
        sys.exit(1)
    
    streamer = WebcamStreamer(
        receive_port=args.receive_port,
        send_port=args.send_port,
        send_to_ip=args.send_to_ip
    )
    
    streamer.start()