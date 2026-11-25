"""CineSpot: varios clientes intentan reservar el mismo asiento a la vez.

1. Ejecuta con USAR_LOCK = False -> caso de error (asiento vendido varias veces).
2. Cambia a USAR_LOCK = True y ejecuta de nuevo -> caso de éxito.
"""

import random
import threading
import time

USAR_LOCK = False  # <-- Cambia a True para corregir el error

CLIENTES = ["Ana", "Luis", "Marta"]  # Todos quieren el asiento A1

asientos = {"A1": None}  # None = libre
confirmados = []
lock = threading.Lock()


def reservar(cliente):
    if USAR_LOCK:
        lock.acquire()

    if asientos["A1"] is None:
        print(f"{cliente} ve A1 libre")
        time.sleep(random.uniform(0.05, 0.15))  # Tiempo de procesar el pago
        asientos["A1"] = cliente
        confirmados.append(cliente)
        print(f"{cliente} reservó A1")
    else:
        print(f"{cliente} rechazado: A1 ya es de {asientos['A1']}")

    if USAR_LOCK:
        lock.release()


def main():
    hilos = [threading.Thread(target=reservar, args=(c,)) for c in CLIENTES]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()

    print(f"\nConfirmados: {confirmados}")
    print(f"Dueño real de A1: {asientos['A1']}")
    if len(confirmados) > 1:
        print("ERROR: A1 se vendió a más de un cliente")
    else:
        print("ÉXITO: A1 se vendió a un solo cliente")


if __name__ == "__main__":
    main()
