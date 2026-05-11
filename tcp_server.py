"""
TCP Server — Ping Pong (esercizi 0 e 2)

Esercizio 0 – Refactoring con funzioni
    Il codice originale aveva tutta la logica dentro main(). Qui ogni
    responsabilità è estratta in una funzione dedicata, rendendo il
    codice più leggibile, testabile e riutilizzabile.

Esercizio 2 – Server multi-client
    Il server originale gestiva un solo client e poi terminava.
    Questa versione supporta:
      • modalità sequenziale: dopo che un client si disconnette il
        server torna ad aspettare il prossimo (MAX_CLIENTS connessioni).
      • modalità parallela (bonus): ogni client viene gestito in un
        Thread separato, così più client possono essere connessi
        contemporaneamente.

Cambia USE_THREADS = True per attivare la modalità parallela.

"""

import socket
import threading

# ── Configurazione ────────────────────────────────────────────────────────────
HOST = "127.0.0.1"
PORT = 65432
MAX_CLIENTS = 5      
USE_THREADS  = False 


# ── Funzioni di supporto ──────────────────────────────────────────────────────

def create_server_socket(host: str, port: int) -> socket.socket:
    """
    Crea, configura, fa il bind e mette in ascolto il socket del server.

    Separare questa logica da main() significa che possiamo cambiare
    facilmente host/port o riusare la funzione in altri script.
    """
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server_sock.bind((host, port))

    
    server_sock.listen(5)
    print(f"[Server] In ascolto su {host}:{port} ...")
    return server_sock


def build_reply(message: str) -> str:
    """
    Restituisce la risposta corretta per un dato messaggio in ingresso.

    Centralizzare la logica di risposta qui rende banale aggiungere
    nuovi comandi senza toccare il loop di comunicazione.
    """
    if message == "PING":
        return "PONG"
    return f"Messaggio sconosciuto: {message!r}"


def handle_client(conn: socket.socket, addr: tuple) -> None:
    """
    Gestisce l'intera sessione con un singolo client.

    Riceve messaggi finché il client non chiude la connessione, poi
    chiude il socket lato server. Questa funzione viene chiamata sia
    in modalità sequenziale che dal thread in modalità parallela.

    Parametri
    ----------
    conn : socket già "connesso" restituito da accept()
    addr : (ip, porta) del client remoto
    """
    print(f"[Server] Connessione accettata da {addr}")
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                # recv() restituisce b"" quando il client chiude la connessione
                print(f"[Server] {addr} ha chiuso la connessione.")
                break

            message = data.decode("utf-8").strip()
            print(f"[Server] Ricevuto da {addr}: {message!r}")

            reply = build_reply(message)
            conn.sendall(reply.encode("utf-8"))
            print(f"[Server] Inviato a {addr}: {reply!r}")
    finally:
        conn.close()


# ── Modalità sequenziale ──────────────────────────────────────────────────────

def run_sequential(server_sock: socket.socket, max_clients: int) -> None:
    """
    Serve i client uno alla volta.

    Dopo che un client si disconnette, il server torna subito a
    chiamare accept() per attendere il prossimo. Si ferma dopo
    aver servito max_clients client.

    Ragionamento: la soluzione più semplice quando il carico è basso
    e non c'è necessità di concorrenza.
    """
    for client_num in range(1, max_clients + 1):
        print(f"\n[Server] In attesa del client {client_num}/{max_clients} ...")
        conn, addr = server_sock.accept()
        handle_client(conn, addr)

    print("\n[Server] Limite di client raggiunto. Server in chiusura.")


# ── Modalità parallela (bonus threading) ─────────────────────────────────────

def run_threaded(server_sock: socket.socket, max_clients: int) -> None:
    """
    Serve più client in parallelo usando un thread per ognuno.

    Il thread principale rimane bloccato su accept(); ogni nuova
    connessione viene delegata immediatamente a un nuovo Thread,
    così il server può accettare il client successivo senza aspettare
    che il precedente finisca.

    Ragionamento: semplice da implementare, adatto a carichi moderati.
    Per carichi elevati preferire asyncio o un thread-pool.
    """
    threads = []
    clients_accepted = 0

    while clients_accepted < max_clients:
        print(f"\n[Server] In attesa di un client ({clients_accepted}/{max_clients} serviti) ...")
        conn, addr = server_sock.accept()
        clients_accepted += 1

        
        t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    print("\n[Server] Tutti i client sono stati serviti.")


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    server_sock = create_server_socket(HOST, PORT)
    try:
        if USE_THREADS:
            print("[Server] Modalità: parallela (threading)")
            run_threaded(server_sock, MAX_CLIENTS)
        else:
            print("[Server] Modalità: sequenziale")
            run_sequential(server_sock, MAX_CLIENTS)
    finally:
        server_sock.close()
        print("[Server] Socket principale chiuso.")


if __name__ == "__main__":
    main()
