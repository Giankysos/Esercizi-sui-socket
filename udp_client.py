"""
UDP Client — Ping Pong (esercizi 0, 1 e 3)

Esercizio 0 – Refactoring con funzioni
    La logica è ora suddivisa in:
      • create_client_socket() – crea il socket e imposta il timeout
      • send_ping()            – invia un datagramma e attende la risposta
      • run_ping_loop()        – orchestra il ciclo
      • main()                 – entry point e teardown

Esercizio 1 – Stampa la risposta completa
    Il client stampa la stringa intera ricevuta dal server, incluso il
    contatore (es. "PONG #3"), così il contatore è visibile nell'output.

Esercizio 3 – Gestione del timeout
    Con DROP_PROBABILITY > 0 sul server, alcuni datagrammi di risposta
    non arriveranno mai. Il timeout di 2 s su recvfrom() converte
    l'attesa infinita in un'eccezione socket.timeout gestita:
      • il client stampa un messaggio descrittivo
      • continua al ping successivo senza crashare
    Questo dimostra perché il timeout è indispensabile in UDP.


"""

import socket
import time

# ── Configurazione ────────────────────────────────────────────────────────────
HOST        = "127.0.0.1"
PORT        = 65433
NUM_PINGS   = 5
SLEEP_TIME  = 0.5
TIMEOUT     = 2.0   # secondi prima che recvfrom() sollevi socket.timeout
BUFFER_SIZE = 1024


# ── Funzioni di supporto ──────────────────────────────────────────────────────

def create_client_socket(timeout: float) -> socket.socket:
    """
    Crea un socket UDP e imposta il timeout su recvfrom().

    Ragionamento: in UDP non esiste connessione, quindi il socket è
    pronto all'uso subito dopo la creazione. Il timeout è essenziale
    perché senza di esso recvfrom() bloccherebbe per sempre in caso di
    perdita del pacchetto di risposta (esercizio 3).
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)
    return sock


def send_ping(
    sock: socket.socket,
    host: str,
    port: int,
    ping_num: int
) -> str | None:
    """
    Invia un datagramma PING e attende la risposta.

    Ritorna la risposta come stringa se arriva entro il timeout,
    oppure None se la risposta non arriva in tempo (pacchetto perso).

    Parametri
    ----------
    sock     : socket UDP già configurato
    host     : indirizzo IP del server
    port     : porta del server
    ping_num : numero del ping corrente (per il log)
    """
    message = "PING"
    print(f"[Client] Invio #{ping_num}: {message!r}")

    # sendto() include la destinazione perché UDP non ha connessione persistente
    sock.sendto(message.encode("utf-8"), (host, port))

    try:
        data, server_addr = sock.recvfrom(BUFFER_SIZE)
        # Esercizio 1: decode e stampa l'intera risposta (es. "PONG #3")
        reply = data.decode("utf-8")
        print(f"[Client] Risposta da {server_addr}: {reply!r}")
        return reply

    except socket.timeout:
        # Esercizio 3: il timeout ci dice che la risposta non è arrivata.
        # Questo accade quando il server ha simulato la perdita del pacchetto.
        # Continuiamo al prossimo ping invece di crashare.
        print(f"[Client] Timeout — nessuna risposta per il ping #{ping_num} (pacchetto perso)")
        return None


def run_ping_loop(
    sock: socket.socket,
    host: str,
    port: int,
    num_pings: int,
    sleep_time: float
) -> None:
    """
    Esegue il ciclo di ping e raccoglie le statistiche.

    Conta le risposte ricevute e i timeout per dare un riepilogo
    finale — utile per osservare l'effetto di DROP_PROBABILITY.
    """
    received = 0
    lost = 0

    for i in range(1, num_pings + 1):
        reply = send_ping(sock, host, port, i)
        if reply is not None:
            received += 1
        else:
            lost += 1
        time.sleep(sleep_time)

    print(f"\n[Client] Riepilogo: {received}/{num_pings} risposte ricevute, {lost} timeout.")


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    print(f"[Client] Socket UDP pronto. Invio a {HOST}:{PORT}\n")
    sock = create_client_socket(TIMEOUT)
    try:
        run_ping_loop(sock, HOST, PORT, NUM_PINGS, SLEEP_TIME)
    finally:
        print("[Client] Chiusura socket.")
        sock.close()


if __name__ == "__main__":
    main()
