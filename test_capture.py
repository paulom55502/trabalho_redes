import os
import csv
import time
import datetime
import pytest

from capture_to_csv import window_start_for_timestamp, Aggregator, write_csv_rows

def test_window_start_for_timestamp():
    ts = 12.3
    w = window_start_for_timestamp(ts, window_size=5)
    assert isinstance(w, datetime.datetime)
    assert w.second % 5 == 0

def test_aggregator_add_and_flush(tmp_path):
    agg = Aggregator(window_size=5)
    server_ip = "192.168.0.5"
    ts = time.time()

    agg.add_packet(ts, "192.168.0.10", server_ip, "HTTP", 100, server_ip)
    agg.add_packet(ts, server_ip, "192.168.0.10", "HTTP", 50, server_ip)

    output_csv = tmp_path / "out.csv"
    agg.flush_older_than(ts + 10, output_csv)

    with open(output_csv, newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)

    assert rows[0] == ["timestamp_window_start","cliente_ip","protocolo","bytes_entrada","bytes_saida"]
    assert len(rows) == 2
    assert rows[1][1] == "192.168.0.10"
    assert rows[1][2] == "HTTP"
    assert int(rows[1][3]) == 100
    assert int(rows[1][4]) == 50
