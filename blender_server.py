import bpy
import socket
import threading

host, port = "127.0.0.1", 9001

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(1)
    print("✅ Blender Server in ascolto su", host, port)

    while True:
        conn, _ = server.accept()
        data = conn.recv(4096).decode()
        if not data:
            break
        try:
            exec(data)  # Esegue il codice ricevuto
            conn.send(b"Comando eseguito\n")
        except Exception as e:
            conn.send(f"❌ Errore: {e}\n".encode())
        conn.close()

# Avvia il server in un thread separato
thread = threading.Thread(target=start_server, daemon=True)
thread.start()
