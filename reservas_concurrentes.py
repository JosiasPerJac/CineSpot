"""CineSpot: lógica de las cuatro versiones de la solución concurrente.

- SalaCineBasica: recurso de tipo básico (un entero: 0 libre, 1 reservado).
- SalaCine: recurso de tipo complejo (diccionario asiento -> estado y usuario).
- Cada una puede ejecutarse con o sin threading.Lock.
"""

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


class TrabajadorReserva(threading.Thread):
    """Hilo que atiende la solicitud de un usuario."""

    def __init__(self, numero, sala, id_asiento, usuario, usar_lock, demora,
                 al_terminar=None):
        super().__init__(name=f"Hilo-{numero}")
        self.sala = sala
        self.id_asiento = id_asiento
        self.usuario = usuario
        self.usar_lock = usar_lock
        self.demora = demora
        self.al_terminar = al_terminar
        self.id_hilo = None
        self.resultado = self.antes = self.despues = None

    @property
    def operacion(self):
        return f"{self.usuario} reserva {self.id_asiento}"

    def run(self):
        self.id_hilo = threading.get_native_id()
        self.resultado, self.antes, self.despues = self.sala.reservar_asiento(
            self.id_asiento, self.usuario, self.usar_lock, self.demora
        )
        if self.al_terminar:
            self.al_terminar(self)


class SimuladorCineSpot:
    """Crea la sala, lanza un hilo por solicitud y revisa el resultado."""

    def __init__(self, tipo, usar_lock, solicitudes, asientos, demora,
                 al_terminar=None):
        if tipo == "basico":
            self.sala = SalaCineBasica("F01")
            # El tipo básico solo tiene un asiento: todas las solicitudes van a él.
            solicitudes = [(usuario, "A1") for usuario, _ in solicitudes]
        else:
            self.sala = SalaCine("F01", asientos)
        self.usar_lock = usar_lock
        self.estado_inicial = self.sala.consultar()
        self.trabajadores = [
            TrabajadorReserva(i, self.sala, asiento, usuario, usar_lock, demora,
                              al_terminar)
            for i, (usuario, asiento) in enumerate(solicitudes, start=1)
        ]

    @property
    def version(self):
        return f"{self.sala.nombre} {'CON' if self.usar_lock else 'SIN'} Lock"

    def ejecutar(self):
        for t in self.trabajadores:
            t.start()
        for t in self.trabajadores:
            t.join()
        return self.sala.consultar()

    def confirmadas(self):
        return [t for t in self.trabajadores if t.resultado == CONFIRMADA]

    def condiciones_de_carrera(self):
        """Asientos que se confirmaron a más de un usuario."""
        por_asiento = {}
        for t in self.confirmadas():
            por_asiento.setdefault(t.id_asiento, []).append(t.usuario)
        return {a: usuarios for a, usuarios in por_asiento.items() if len(usuarios) > 1}
