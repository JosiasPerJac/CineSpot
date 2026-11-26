"""Coordinación de las cuatro versiones de la simulación."""

from salas import CONFIRMADA, SalaCine, SalaCineBasica
from trabajador import TrabajadorReserva


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
