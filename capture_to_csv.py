#!/usr/bin/env python3
"""
capture_to_csv.py
Modo: --live (scapy) ou --simulate (sintético)
Gera output.csv com colunas:
timestamp_window_start,cliente_ip,protocolo,bytes_entrada,bytes_saida
"""

import argparse
import csv
import datetime
import time
import threading
from collections import defaultdict, namedtuple

# Se for usar captura real, descomente import scapy abaixo e instale scapy
# from scapy.all import sniff, IP, TCP, UDP, Raw

WindowKey = namedtuple("WindowKey", ["window_start", "cliente_ip", "protocolo"])

def window_start_for_timestamp(ts, window_size=5):
    # ts: float seconds since epoch
    w = int(ts) - (int(ts) % window_size)
    return datetime.datetime.fromtimestamp(w)

class Aggregator:
    def __init__(self, window_size=5):
        self.window_size = window_size
        # map WindowKey -> [bytes_in, bytes_out]
        self.lock = threading.Lock()
        self.buf = defaultdict(lambda: [0,0])  # [bytes_entrada, bytes_saida]

    def add_packet(self, ts, src_ip, dst_ip, proto, length, server_ip):
        # Determine direction
        window = window_start_for_timestamp(ts, self.window_size)
        if dst_ip == server_ip:  # packet incoming to server (cliente -> server)
            cliente = src_ip
            with self.lock:
                key = WindowKey(window, cliente, proto)
                self.buf[key][0] += length
        elif src_ip == server_ip:  # packet outgoing from server (server -> cliente)
            cliente = dst_ip
            with self.lock:
                key = WindowKey(window, cliente, proto)
                self.buf[key][1] += length
        else:
            # packet not involving server_ip -- ignore
            pass

    def flush_older_than(self, cutoff_ts, output_csv_path):
        cutoff_window = window_start_for_timestamp(cutoff_ts, self.window_size)
        rows = []
        with self.lock:
            keys_to_remove = []
            for key, val in self.buf.items():
                # key.window_start is datetime
                if key.window_start <= cutoff_window:
                    rows.append( (key.window_start.isoformat(sep=' '), key.cliente_ip, key.protocolo, val[0], val[1]) )
                    keys_to_remove.append(key)
            for k in keys_to_remove:
                del self.buf[k]
        if rows:
            write_csv_rows(output_csv_path, rows, append=True)

def write_csv_rows(path, rows, append=True):
    header = ['timestamp_window_start','cliente_ip','protocolo','bytes_entrada','bytes_saida']
    mode = 'a' if append else 'w'
    first = False
    try:
        if mode == 'w':
            first = True
        else:
            # check if file exists and has content
            try:
                with open(path,'r',newline='') as f:
                    first = (f.readline() == '')
            except FileNotFoundError:
                first = True
        with open(path, mode, newline='') as f:
            writer = csv.writer(f)
            if first:
                writer.writerow(header)
            for r in rows:
                writer.writerow(r)
    except Exception as e:
        print("Erro ao escrever CSV:", e)

########## Simulação de tráfego (modo --simulate) ##########
import random
def simulate_traffic(agg, server_ip, duration_seconds=60):
    # gera tráfego sintético entre 5 clientes e o server, com protocolos variados
    clientes = [f"192.168.0.{i}" for i in range(10,15)]
    protocols = ['HTTP','HTTPS','FTP','TCP_OTHER','UDP_OTHER']
    start = time.time()
    while time.time() - start < duration_seconds:
        ts = time.time()
        # escolhe aleatoriamente 1-6 pacotes na janela
        for _ in range(random.randint(1,6)):
            cliente = random.choice(clientes)
            proto = random.choice(protocols)
            # decide direção:
            if random.random() < 0.6:
                # cliente -> server
                src, dst = cliente, server_ip
                length = random.randint(100,2000)
            else:
                # server -> cliente
                src, dst = server_ip, cliente
                length = random.randint(100,2000)
            agg.add_packet(ts, src, dst, proto, length, server_ip)
        time.sleep(0.2)  # gera pacotes um pouco frequentemente

########## (Opcional) Função para transformar tuplas IP/porta em protocolo (quando sniff real) ##########
def infer_protocol(sport, dport, payload_present):
    # heurística simples
    if sport in (80, 8080) or dport in (80,8080):
        return 'HTTP'
    if sport in (443,) or dport in (443,):
        return 'HTTPS'
    if sport in (21,) or dport in (21,):
        return 'FTP'
    # else
    return 'TCP_OTHER' if payload_present else 'UDP_OTHER'

########## Main ##########
def main():
    parser = argparse.ArgumentParser(description="Capture/aggregate tráfego e gerar CSV para Excel")
    parser.add_argument("--server-ip", required=True, help="IP do servidor alvo")
    parser.add_argument("--output", default="output.csv", help="arquivo CSV de saída")
    parser.add_argument("--mode", choices=['simulate','live'], default='simulate', help="simulate (no root) ou live (scapy)")
    parser.add_argument("--duration", type=int, default=60, help="duração da simulação (apenas simulate)")
    parser.add_argument("--window", type=int, default=5, help="tamanho da janela em segundos")
    args = parser.parse_args()

    agg = Aggregator(window_size=args.window)
    if args.mode == 'simulate':
        print("Modo SIMULATE: gerando tráfego sintético por", args.duration, "s")
        t = threading.Thread(target=simulate_traffic, args=(agg, args.server_ip, args.duration))
        t.start()
    else:
        # Implementação base para captura com scapy - desativada por segurança aqui.
        print("Modo LIVE selecionado. (O exemplo de captura com scapy não está ativo neste script de amostra).")
        # Para produção: usar sniff(filter=f"host {args.server_ip}", prn=callback)
        # callback deve chamar agg.add_packet(...)
        # Lembre-se de rodar com sudo.
        pass

    # Loop principal: a cada 1s, tentamos 'flusar' janelas antigas
    start = time.time()
    try:
        while True:
            now = time.time()
            # flusar janelas anteriores (por exemplo, janelas que acabaram 1 janela atrás)
            cutoff = now - 1
            agg.flush_older_than(cutoff, args.output)
            if args.mode == 'simulate' and (time.time() - start) > args.duration and not t.is_alive():
                # flush final
                agg.flush_older_than(time.time()+10, args.output)
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("Interrompido pelo usuário. Flush final.")
        agg.flush_older_than(time.time()+10, args.output)

if __name__ == "__main__":
    main()
