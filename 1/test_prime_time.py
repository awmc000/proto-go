#!/usr/bin/env python3
"""Protocol-level tester for Protohackers 1: Prime Time.

Run your server first, then execute:

    python3 1/test_prime_time.py

Optional flags:

    python3 1/test_prime_time.py --host 127.0.0.1 --port 7007
"""

from __future__ import annotations

import argparse
import json
import math
import socket
import threading
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Test a Prime Time server.")
    parser.add_argument("--host", default="127.0.0.1", help="Server hostname")
    parser.add_argument("--port", default=7007, type=int, help="Server TCP port")
    parser.add_argument(
        "--timeout",
        default=2.0,
        type=float,
        help="Socket timeout in seconds",
    )
    return parser.parse_args()


def is_prime_reference(number: Any) -> bool:
    if isinstance(number, bool):
        return False

    if isinstance(number, int):
        n = number
    elif isinstance(number, float):
        if not math.isfinite(number) or not number.is_integer():
            return False
        n = int(number)
    else:
        return False

    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False

    limit = math.isqrt(n)
    divisor = 3
    while divisor <= limit:
        if n % divisor == 0:
            return False
        divisor += 2
    return True


def send_line(sock: socket.socket, line: str) -> None:
    sock.sendall(line.encode("utf-8") + b"\n")


def recv_line(sock: socket.socket) -> str:
    chunks = bytearray()
    while True:
        chunk = sock.recv(1)
        if not chunk:
            if chunks:
                raise AssertionError("Connection closed before newline-terminated response")
            return ""
        if chunk == b"\n":
            return chunks.decode("utf-8")
        chunks.extend(chunk)


def recv_json(sock: socket.socket) -> dict[str, Any]:
    raw = recv_line(sock)
    if raw == "":
        raise AssertionError("Expected a JSON response, but the connection closed")

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"Response was not valid JSON: {raw!r}") from exc

    if not isinstance(payload, dict):
        raise AssertionError(f"Response was not a JSON object: {payload!r}")

    return payload


def expect_valid_response(sock: socket.socket, number: Any) -> None:
    response = recv_json(sock)

    if response.get("method") != "isPrime":
        raise AssertionError(f"Unexpected method in response: {response!r}")
    if not isinstance(response.get("prime"), bool):
        raise AssertionError(f"Response prime field must be boolean: {response!r}")

    expected = is_prime_reference(number)
    actual = response["prime"]
    if actual != expected:
        raise AssertionError(
            f"Incorrect primality result for {number!r}: expected {expected}, got {actual}"
        )


def expect_malformed_then_disconnect(sock: socket.socket, line: str) -> None:
    send_line(sock, line)

    first = recv_line(sock)
    if first == "":
        raise AssertionError("Malformed request should receive a single malformed response")

    try:
        response = json.loads(first)
    except json.JSONDecodeError:
        response = None

    if isinstance(response, dict):
        if response.get("method") == "isPrime" and isinstance(response.get("prime"), bool):
            raise AssertionError(
                f"Malformed request received a conforming response instead: {response!r}"
            )

    second = recv_line(sock)
    if second != "":
        raise AssertionError(
            "Server should disconnect after replying once to a malformed request"
        )


def open_connection(host: str, port: int, timeout: float) -> socket.socket:
    sock = socket.create_connection((host, port), timeout=timeout)
    sock.settimeout(timeout)
    return sock


def test_sequential_requests(host: str, port: int, timeout: float) -> None:
    cases = [
        2,
        3,
        4,
        5,
        17,
        18,
        7919,
        7920,
        -7,
        0,
        1,
        2.0,
        17.0,
        19.25,
    ]

    with open_connection(host, port, timeout) as sock:
        for number in cases:
            send_line(sock, json.dumps({"method": "isPrime", "number": number}))
            expect_valid_response(sock, number)


def test_extraneous_fields(host: str, port: int, timeout: float) -> None:
    with open_connection(host, port, timeout) as sock:
        send_line(
            sock,
            json.dumps(
                {
                    "method": "isPrime",
                    "number": 29,
                    "ignored": "value",
                    "nested": {"also": "ignored"},
                }
            ),
        )
        expect_valid_response(sock, 29)


def test_malformed_requests(host: str, port: int, timeout: float) -> None:
    malformed_lines = [
        '{"method":"isPrime"}',
        '{"number":7}',
        '{"method":"notPrime","number":7}',
        '{"method":"isPrime","number":"7"}',
        '["isPrime", 7]',
        '{"method":"isPrime","number":7',
    ]

    for line in malformed_lines:
        with open_connection(host, port, timeout) as sock:
            expect_malformed_then_disconnect(sock, line)


def test_five_simultaneous_clients(host: str, port: int, timeout: float) -> None:
    errors: list[str] = []
    lock = threading.Lock()
    start = threading.Barrier(5)

    def worker(index: int) -> None:
        numbers = [index * 10 + 1, index * 10 + 2, index * 10 + 3, index * 10 + 11]
        try:
            with open_connection(host, port, timeout) as sock:
                start.wait(timeout=timeout)
                for number in numbers:
                    send_line(sock, json.dumps({"method": "isPrime", "number": number}))
                    expect_valid_response(sock, number)
        except Exception as exc:
            with lock:
                errors.append(f"client {index}: {exc}")

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    if errors:
        raise AssertionError("Concurrent client test failed:\n" + "\n".join(errors))


def main() -> int:
    args = parse_args()

    tests = [
        ("sequential requests", test_sequential_requests),
        ("extraneous fields", test_extraneous_fields),
        ("malformed requests", test_malformed_requests),
        ("five simultaneous clients", test_five_simultaneous_clients),
    ]

    for name, test in tests:
        test(args.host, args.port, args.timeout)
        print(f"[PASS] {name}")

    print("All Prime Time protocol checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
