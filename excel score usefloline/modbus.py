import socket
import threading

def mock_modbus_server(ip, port, stop_signal):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((ip, port))
        s.listen()
        print(f"Mock Modbus server started on {ip}:{port}")

        while not stop_signal.is_set():
            conn, addr = s.accept()
            with conn:
                data = conn.recv(1024)
                if data:
                    # Simulate a response
                    conn.sendall(b'\x00\x01')  # Example response, adjust as needed

def start_mock_servers(ip_ports):
    stop_signal = threading.Event()
    threads = []
    for ip, port in ip_ports:
        thread = threading.Thread(target=mock_modbus_server, args=(ip, port, stop_signal))
        thread.start()
        threads.append(thread)
    return stop_signal, threads

# Example IP and port configuration
mock_ip_ports = [("127.0.0.1", 1502), ("127.0.0.1", 1503), ("127.0.0.1", 1504), ("127.0.0.1", 1505), ("127.0.0.1", 1506)]

stop_signal, threads = start_mock_servers(mock_ip_ports)
