"""
TCP Client — Ping Pong (esercizio 0)

Esercizio 0 – Refactoring con funzioni
    Il codice originale aveva tutta la logica dentro main(). Qui ogni
    responsabilità è estratta in una funzione dedicata:

      • create_client_socket()  – crea e connette il socket
      • send_ping()             – invia un singolo PING e riceve la risposta
      • run_ping_loop()         – orchestra il ciclo di 5 ping
      • main()                  – entry point, gestione teardown

    Questa struttura permette, per esempio, di importare send_ping()
    in un test unitario senza dover eseguire il loop completo.


"""

import socket
import time

# ── Configurazione ────────────────────────────────────────────────────────────
HOST       = "127.0.0.1"
PORT       = 65432
NUM_PINGS  = 5      # quante volte inviare PING
SLEEP_TIME = 0.5    # secondi di pausa tra un ping e il successivo


# ── Funzioni di supporto ──────────────────────────────────────────────────────

def create_client_socket(host: str, port: int) -> socket.socket:
    """
    Crea un socket TCP e completa il three-way handshake con il server.

    Separare la creazione della connessione da main() rende questa
    operazione riutilizzabile e facilita il test con server mock.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    print(f"[Client] Connesso a {host}:{port}")
    return sock


def send_ping(sock: socket.socket, ping_num: int) -> str:
    """
    Invia "PING" al server e restituisce la risposta ricevuta.

    Incapsulare il singolo ciclo richiesta/risposta qui rende il loop
    principale più pulito e la funzione testabile in isolamento.

    Parametri
    ----------
    sock     : socket già connesso
    ping_num : numero del ping corrente (usato solo per il log)

    Ritorna
    -------
    La risposta del server come stringa UTF-8.
    """
    message = "PING"
    print(f"\n[Client] Invio #{ping_num}: {message!r}")

    sock.sendall(message.encode("utf-8"))

    data = sock.recv(1024)
    reply = data.decode("utf-8")
    print(f"[Client] Risposta: {reply!r}")
    return reply


def run_ping_loop(sock: socket.socket, num_pings: int, sleep_time: float) -> None:
    """
    Esegue il ciclo di ping/pong per num_pings iterazioni.

    Separare il loop da main() permette di cambiare facilmente il
    numero di ping o la pausa senza toccare la logica di setup/teardown.
    """
    for i in range(1, num_pings + 1):
        send_ping(sock, i)
        time.sleep(sleep_time)


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    sock = create_client_socket(HOST, PORT)
    try:
        run_ping_loop(sock, NUM_PINGS, SLEEP_TIME)
    finally:
        print("\n[Client] Tutti i ping inviati. Chiudo la connessione.")
        sock.close()


if __name__ == "__main__":
    main()
