"""
Calcolatore TCP — Server (esercizio 4)

=== Scelta del protocollo ===
TCP, perché:
  • un'operazione aritmetica è una transazione richiesta/risposta dove
    la consegna garantita è fondamentale: una risposta mancante sarebbe
    impossibile da distinguere da "risultato = 0".
  • le espressioni possono essere arbitrariamente lunghe — il flusso
    TCP gestisce la frammentazione in modo trasparente, mentre UDP
    richiederebbe la gestione manuale dei pacchetti.

=== Formato dei messaggi ===
  • Richiesta  (client → server): stringa testuale terminata da \n
        "3 + 4\n"   oppure   "10.5 / 2\n"
  • Risposta   (server → client): stringa testuale terminata da \n
        "7.0\n"     oppure   "ERRORE: divisione per zero\n"
  Tutti i valori numerici sono float in base 10.
  Operatori supportati: +  -  *  /

=== Messaggi malformati ===
  Se il client invia un'espressione non parsabile o con un operatore
  non supportato, il server risponde con "ERRORE: <descrizione>\n"
  e rimane in ascolto per il prossimo messaggio (non si disconnette).

=== Condizione di terminazione ===
  Il client invia "QUIT\n". Il server risponde "ARRIVEDERCI\n" e
  chiude la connessione. È il client a decidere quando smettere,
  poiché è lui che conosce quante operazioni vuole eseguire.


"""

import socket

# ── Configurazione ────────────────────────────────────────────────────────────
HOST       = "127.0.0.1"
PORT       = 65434
MAX_CLIENTS = 3   # dopo 3 sessioni il server si ferma


# ── Logica del calcolatore ────────────────────────────────────────────────────

OPERATORS = {
    "+": lambda a, b: a + b,
    "-": lambda a, b: a - b,
    "*": lambda a, b: a * b,
    "/": lambda a, b: a / b,
}


def evaluate(expression: str) -> str:
    """
    Valuta un'espressione aritmetica nella forma "numero operatore numero".

    Ritorna il risultato come stringa (es. "7.0") oppure una stringa
    di errore prefissata da "ERRORE:" in caso di input non valido.

    Scelte di design:
      • Usiamo il parsing manuale con split() invece di eval() per
        motivi di sicurezza: eval() eseguirebbe codice arbitrario.
      • I risultati sono restituiti come float per coerenza, anche
        quando il risultato è un intero (es. 3+4 → "7.0").
    """
    parts = expression.strip().split()

    if len(parts) != 3:
        return f"ERRORE: formato atteso 'numero operatore numero', ricevuto {expression!r}"

    left_str, op, right_str = parts

    if op not in OPERATORS:
        return f"ERRORE: operatore {op!r} non supportato (usa +, -, *, /)"

    try:
        left  = float(left_str)
        right = float(right_str)
    except ValueError:
        return f"ERRORE: operandi non numerici: {left_str!r}, {right_str!r}"

    if op == "/" and right == 0.0:
        return "ERRORE: divisione per zero"

    result = OPERATORS[op](left, right)
    return str(result)


# ── Gestione del client ───────────────────────────────────────────────────────

def recv_line(conn: socket.socket) -> str | None:
    """
    Legge caratteri fino a '\n' e restituisce la riga senza il newline.

    In TCP recv() può tornare parzialmente (TCP è uno stream, non
    un protocollo a messaggi). Leggere fino a '\n' garantisce di
    ricevere un messaggio completo prima di elaborarlo.
    """
    buf = b""
    while True:
        chunk = conn.recv(1)
        if not chunk:
            return None   # client disconnesso
        if chunk == b"\n":
            return buf.decode("utf-8").strip()
        buf += chunk


def handle_client(conn: socket.socket, addr: tuple) -> None:
    """
    Gestisce una sessione di calcolo con un singolo client TCP.

    Il server legge un'espressione per volta, la valuta e risponde.
    Il ciclo termina quando il client invia "QUIT" o si disconnette.
    """
    print(f"[Server] Connessione da {addr}")
    try:
        while True:
            line = recv_line(conn)
            if line is None:
                print(f"[Server] {addr} si è disconnesso.")
                break

            print(f"[Server] Ricevuto: {line!r}")

            if line.upper() == "QUIT":
                conn.sendall("ARRIVEDERCI\n".encode("utf-8"))
                print(f"[Server] {addr} ha richiesto la chiusura.")
                break

            result = evaluate(line)
            reply = result + "\n"
            conn.sendall(reply.encode("utf-8"))
            print(f"[Server] Risposta: {result!r}")

    finally:
        conn.close()


# ── Entry point ───────────────────────────────────────────────────────────────

def create_server_socket(host: str, port: int) -> socket.socket:
    """Crea e configura il socket in ascolto."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host, port))
    s.listen(1)
    print(f"[Server] Calcolatore TCP in ascolto su {host}:{port}")
    return s


def main() -> None:
    server_sock = create_server_socket(HOST, PORT)
    try:
        for _ in range(MAX_CLIENTS):
            conn, addr = server_sock.accept()
            handle_client(conn, addr)
        print("[Server] Sessioni completate. Chiusura.")
    finally:
        server_sock.close()


if __name__ == "__main__":
    main()
