"""Simulación de dos solicitudes para la última plaza de una función."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
from threading import Barrier, Lock


class Cupos:
    """Representación básica: número de plazas disponibles."""

    def __init__(self, disponibles):
        self._disponibles = disponibles
        self._lock = Lock()

    @property
    def estado(self):
        with self._lock:
            return self._disponibles

    def reservar(self, cliente, *, usar_lock=True, tras_validar=None):
        with self._lock if usar_lock else nullcontext():
            # Sección crítica: leer el contador, validar y escribir el nuevo saldo.
            disponibles = self._disponibles
            if disponibles <= 0:
                return False
            if tras_validar is not None:
                tras_validar()
            self._disponibles = disponibles - 1
            return True


class Asientos:
    """Representación compleja: asiento y titular dentro de una función."""

    def __init__(self, asientos):
        self._asientos = dict.fromkeys(asientos)
        self._lock = Lock()

    @property
    def estado(self):
        with self._lock:
            return self._asientos.copy()

    def reservar(self, cliente, asiento="A1", *, usar_lock=True, tras_validar=None):
        with self._lock if usar_lock else nullcontext():
            # Sección crítica: validar existencia, leer el titular y asignar el asiento.
            if asiento not in self._asientos or self._asientos[asiento] is not None:
                return False
            if tras_validar is not None:
                tras_validar()
            self._asientos[asiento] = cliente
            return True


def simular(recurso, *, usar_lock):
    """Ejecuta dos solicitudes sobre la misma instancia con una plaza libre."""
    inicio = Barrier(2, timeout=5)
    # En la demostración sin Lock, ambos hilos validan antes de escribir.
    carrera = None if usar_lock else Barrier(2, timeout=5)

    def solicitar(cliente):
        inicio.wait()
        return recurso.reservar(
            cliente,
            usar_lock=usar_lock,
            tras_validar=carrera.wait if carrera is not None else None,
        )

    clientes = ("Ana", "Luis")
    with ThreadPoolExecutor(max_workers=2) as ejecutor:
        respuestas = dict(zip(clientes, ejecutor.map(solicitar, clientes)))
    return respuestas, recurso.estado


def main():
    for nombre, crear_recurso in (
        ("Entero", lambda: Cupos(1)),
        ("Diccionario", lambda: Asientos(["A1"])),
    ):
        for usar_lock in (False, True):
            respuestas, estado = simular(crear_recurso(), usar_lock=usar_lock)
            modo = "con Lock" if usar_lock else "sin Lock"
            detalle = ", ".join(
                f"{cliente}={'confirmada' if aceptada else 'rechazada'}"
                for cliente, aceptada in respuestas.items()
            )
            print(f"{nombre} {modo} | {detalle} | Estado final: {estado}")


if __name__ == "__main__":
    main()
