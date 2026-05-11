"""
UDP Server — Ping Pong (esercizi 0, 1 e 3)

Esercizio 0 – Refactoring con funzioni
    La logica è ora suddivisa in:
      • create_server_socket() – crea e fa il bind del socket
      • build_reply()          – costruisce la risposta (ora con contatore)
      • maybe_drop()           – decide se simulare una perdita
      • handle_datagram()      – elabora un singolo datagramma in arrivo
      • main()                 – loop principale e setup

Esercizio 1 – Contatore di messaggi
    Il server mantiene un contatore (ping_count) che tiene traccia di
    quanti PING ha ricevuto. Ogni risposta PONG include il contatore:
    "PONG #1", "PONG #2", ...

    Dove vive il contatore? È una variabile locale di main() passata
    per riferimento tramite una lista mutabile [count]. In questo modo
    non usiamo variabili globali mantenendo comunque lo stato.

    Cosa succede al riavvio? Se il server viene riavviato il contatore
    riparte da zero, perché è in memoria volatile. Il client può notare
    la discontinuità (es. riceve "PONG #1" mentre si aspettava "PONG #6").

Esercizio 3 – Simulazione di canale inaffidabile
    DROP_PROBABILITY (default 0.3 = 30%) controlla la probabilità che
    il server "perda" la risposta senza inviarla.
    Quando un pacchetto viene droppato il server stampa un messaggio
    esplicativo e non chiama sendto().

    Sul client: il timeout di 2 s di recvfrom() diventa essenziale —
    senza di esso il client rimarrebbe bloccato indefinitamente su ogni
    pacchetto perso.


"""

import socket
import random

# ── Configurazione ────────────────────────────────────────────────────────────
HOST             = "127.0.0.1"
PORT             = 65433
DROP_PROBABILITY = 0.3   # 0.0 = nessuna perdita, 1.0 = tutti i pacchetti persi


# ── Funzioni di supporto ──────────────────────────────────────────────────────

def create_server_socket(host: str, port: int) -> socket.socket:
    """
    Crea un socket UDP e lo associa all'indirizzo specificato.

    In UDP non c'è listen() né accept(): il socket è subito pronto a
    ricevere datagrammi dopo il bind().
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((host, port))
    print(f"[Server] In ascolto per datagrammi UDP su {host}:{port} ...")
    print("[Server] Premi Ctrl+C per fermare.\n")
    return sock


def build_reply(message: str, ping_count: int) -> str:
    """
    Restituisce la risposta appropriata per il messaggio ricevuto.

    Esercizio 1: se il messaggio è PING, la risposta include il contatore
    corrente, es. "PONG #3". In questo modo il client può verificare
    quanti PING il server ha ricevuto dall'avvio.
    """
    if message == "PING":
        return f"PONG #{ping_count}"
    return f"Sconosciuto: {message!r}"


def maybe_drop() -> bool:
    """
    Restituisce True se questo datagramma deve essere simulato come perso.

    Esercizio 3: usa DROP_PROBABILITY per replicare il comportamento di
    una rete inaffidabile. Su localhost i pacchetti non si perdono mai
    realmente, quindi questa funzione è l'unico modo per studiare
    l'effetto della perdita di pacchetti sul client.
    """
    return random.random() < DROP_PROBABILITY


def handle_datagram(
    sock: socket.socket,
    data: bytes,
    client_addr: tuple,
    ping_count: int
) -> None:
    """
    Elabora un singolo datagramma UDP:
      1. decodifica il messaggio
      2. costruisce la risposta (con contatore)
      3. decide se droppare (esercizio 3)
      4. invia la risposta o logga il drop

    Parametri
    ----------
    sock        : socket del server
    data        : payload grezzo del datagramma
    client_addr : (ip, porta) del mittente
    ping_count  : numero di PING ricevuti finora (usato per la risposta)
    """
    message = data.decode("utf-8").strip()
    print(f"[Server] Ricevuto {message!r} da {client_addr}")

    reply = build_reply(message, ping_count)

    # Esercizio 3: simula la perdita del pacchetto di risposta
    if maybe_drop():
        print(f"[Server] Risposta droppata (perdita simulata) — il client andrà in timeout\n")
        return  

    sock.sendto(reply.encode("utf-8"), client_addr)
    print(f"[Server] Inviato {reply!r} a {client_addr}\n")


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    sock = create_server_socket(HOST, PORT)
    ping_count = 0  

    try:
        while True:
            data, client_addr = sock.recvfrom(1024)

            message = data.decode("utf-8").strip()
            if message == "PING":
                ping_count += 1

            handle_datagram(sock, data, client_addr, ping_count)

    except KeyboardInterrupt:
        print(f"\n[Server] Fermato. Totale PING ricevuti: {ping_count}")
    finally:
        sock.close()


if __name__ == "__main__":
    main()
