"""Salas de cine y operaciones sobre los asientos compartidos."""

import random
import threading
import time
from contextlib import nullcontext

CONFIRMADA = "reserva_confirmada"
OCUPADO = "asiento_ocupado"
INVALIDA = "solicitud_invalida"


def _procesar_pago(demora):
    """Simula el tiempo entre validar el asiento y registrarlo."""
    if demora > 0:
        time.sleep(random.uniform(demora * 0.5, demora * 1.5))


class SalaCineBasica:
    """Tipo básico: un entero representa un único asiento."""

    nombre = "Básico (entero)"

    def __init__(self, id_funcion="F01"):
        self.id_funcion = id_funcion
        self._estado = 0  # 0 = disponible, 1 = reservado
        self._lock = threading.Lock()

    def consultar(self):
        return f"{self._estado} ({'reservado' if self._estado else 'disponible'})"

    def reservar_asiento(self, id_asiento, usuario, usar_lock=True, demora=0.0):
        with self._lock if usar_lock else nullcontext():
            antes = self.consultar()
            if self._estado == 1:
                return OCUPADO, antes, antes
            _procesar_pago(demora)
            self._estado = 1
            return CONFIRMADA, antes, self.consultar()


class SalaCine:
    """Tipo complejo: un diccionario por función con estado y usuario de cada asiento."""

    nombre = "Complejo (diccionario)"

    def __init__(self, id_funcion, ids_asientos):
        self.id_funcion = id_funcion
        self._asientos = {a: {"estado": 0, "usuario": None} for a in ids_asientos}
        self._lock = threading.Lock()

    def consultar(self):
        return ", ".join(
            f"{a}={r['usuario'] if r['estado'] else 'libre'}"
            for a, r in self._asientos.items()
        )

    def reservar_asiento(self, id_asiento, usuario, usar_lock=True, demora=0.0):
        with self._lock if usar_lock else nullcontext():
            antes = self.consultar()
            registro = self._asientos.get(id_asiento)
            if registro is None:
                return INVALIDA, antes, antes
            if registro["estado"] == 1:
                return OCUPADO, antes, antes
            _procesar_pago(demora)
            self._asientos[id_asiento] = {"estado": 1, "usuario": usuario}
            return CONFIRMADA, antes, self.consultar()
