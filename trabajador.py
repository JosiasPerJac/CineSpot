"""Hilo que procesa una solicitud de reserva."""

import threading


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
