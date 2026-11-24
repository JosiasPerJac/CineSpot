"""CineSpot: varias solicitudes simultáneas compiten por los asientos de una función.

Caso de error y caso de éxito
-----------------------------
1. Ejecuta el programa con ``USAR_LOCK = False``: los hilos validan el mismo
   estado antes de que alguno escriba y la auditoría detecta reservas duplicadas.
2. Cambia la constante a ``USAR_LOCK = True`` y vuelve a ejecutarlo: el Lock
   convierte la validación y la escritura en una sola operación y la auditoría
   confirma que no hay duplicados.

Los datos de la función se leen de ``funcion.json`` (o de la ruta indicada como
primer argumento). Nada del resultado está escrito de antemano: cada línea del
registro se imprime en el momento en que el hilo la produce y la auditoría se
calcula a partir del estado real que quedó en memoria.
"""

import json
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
from pathlib import Path
from threading import Barrier, Lock, current_thread

# >>> Cambia este valor para pasar del caso de error al caso de éxito. <<<
USAR_LOCK = False

# Tiempo que tarda el "cobro" entre validar el asiento y registrarlo (segundos).
DEMORA_COBRO = (0.05, 0.15)

RUTA_DATOS = Path(__file__).with_name("funcion.json")


class Registro:
    """Imprime cada evento en el instante en que ocurre, con hilo y tiempo."""

    def __init__(self, salida=print):
        self._inicio = time.perf_counter()
        self._lock = Lock()  # Solo ordena las líneas impresas; no protege reservas.
        self._salida = salida

    def __call__(self, mensaje):
        ms = (time.perf_counter() - self._inicio) * 1000
        with self._lock:
            self._salida(f"  [{ms:7.1f} ms] {current_thread().name:<14} {mensaje}")


def _sin_registro(_mensaje):
    pass


def _cobrar():
    time.sleep(random.uniform(*DEMORA_COBRO))


class Cupos:
    """Representación básica: número de plazas disponibles."""

    def __init__(self, disponibles):
        self.iniciales = disponibles
        self._disponibles = disponibles
        self._lock = Lock()

    @property
    def estado(self):
        with self._lock:
            return self._disponibles

    def reservar(self, cliente, asiento=None, *, usar_lock=True,
                 tras_validar=None, registro=_sin_registro):
        with self._lock if usar_lock else nullcontext():
            # Sección crítica: leer el contador, validar y escribir el nuevo saldo.
            disponibles = self._disponibles
            registro(f"{cliente} lee cupos disponibles = {disponibles}")
            if disponibles <= 0:
                registro(f"{cliente} RECHAZADO: no quedan cupos")
                return False
            if tras_validar is not None:
                tras_validar()
            self._disponibles = disponibles - 1
            registro(f"{cliente} escribe cupos = {disponibles - 1} -> CONFIRMADO")
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

    def reservar(self, cliente, asiento="A1", *, usar_lock=True,
                 tras_validar=None, registro=_sin_registro):
        with self._lock if usar_lock else nullcontext():
            # Sección crítica: validar existencia, leer el titular y asignar el asiento.
            if asiento not in self._asientos:
                registro(f"{cliente} RECHAZADO: {asiento} no existe")
                return False
            titular = self._asientos[asiento]
            registro(f"{cliente} lee {asiento} -> {'libre' if titular is None else titular}")
            if titular is not None:
                registro(f"{cliente} RECHAZADO: {asiento} ya es de {titular}")
                return False
            if tras_validar is not None:
                tras_validar()
            self._asientos[asiento] = cliente
            registro(f"{cliente} escribe {asiento} = {cliente} -> CONFIRMADO")
            return True


def simular(recurso, solicitudes, *, usar_lock, tras_validar=_cobrar,
            registro=_sin_registro):
    """Lanza un hilo por solicitud; todos arrancan a la vez sobre el mismo recurso."""
    inicio = Barrier(len(solicitudes), timeout=5)

    def atender(solicitud):
        current_thread().name = f"hilo-{solicitud['cliente']}"
        inicio.wait()  # Simula que todos pulsan "reservar" al mismo tiempo.
        return recurso.reservar(
            solicitud["cliente"],
            solicitud["asiento"],
            usar_lock=usar_lock,
            tras_validar=tras_validar,
            registro=registro,
        )

    with ThreadPoolExecutor(max_workers=len(solicitudes)) as ejecutor:
        resultados = list(ejecutor.map(atender, solicitudes))
    confirmadas = [s for s, ok in zip(solicitudes, resultados) if ok]
    return confirmadas, recurso.estado


def auditar_cupos(iniciales, confirmadas, restantes):
    """Devuelve la lista de errores encontrados comparando ventas y saldo real."""
    errores = []
    vendidos = len(confirmadas)
    if vendidos > iniciales:
        errores.append(f"se confirmaron {vendidos} reservas para {iniciales} cupos "
                       f"(sobreventa de {vendidos - iniciales})")
    if restantes != iniciales - vendidos:
        errores.append(f"{vendidos} reservas descontaron cupos, pero el contador solo "
                       f"bajó de {iniciales} a {restantes} (se perdieron escrituras)")
    return errores


def auditar_asientos(confirmadas, mapa):
    """Detecta asientos confirmados a más de un cliente."""
    errores = []
    por_asiento = {}
    for s in confirmadas:
        por_asiento.setdefault(s["asiento"], []).append(s["cliente"])
    for asiento, clientes in por_asiento.items():
        if len(clientes) > 1:
            titular = mapa[asiento]
            sin_asiento = [c for c in clientes if c != titular]
            errores.append(f"{asiento} se confirmó a {len(clientes)} clientes "
                           f"({', '.join(clientes)}); solo quedó registrado {titular}. "
                           f"{' y '.join(sin_asiento)} "
                           f"{'pagó' if len(sin_asiento) == 1 else 'pagaron'} sin asiento")
    return errores


def cargar_datos(ruta):
    with open(ruta, encoding="utf-8") as archivo:
        return json.load(archivo)


def ejecutar(datos, usar_lock, salida=print):
    """Corre ambos escenarios y devuelve True si la auditoría no halló errores."""
    solicitudes = datos["solicitudes"]
    modo = "CON Lock" if usar_lock else "SIN Lock"
    salida(f"Función: {datos['funcion']} | Asientos: {', '.join(datos['asientos'])} | "
           f"Solicitudes: {len(solicitudes)} | Modo: {modo}")
    todo_ok = True

    escenarios = (
        ("Entero (Cupos)", lambda: Cupos(len(datos["asientos"])), "cupos"),
        ("Diccionario (Asientos)", lambda: Asientos(datos["asientos"]), "asientos"),
    )
    for titulo, crear, tipo in escenarios:
        salida(f"\n=== {titulo} ===")
        recurso = crear()
        confirmadas, estado = simular(recurso, solicitudes, usar_lock=usar_lock,
                                      registro=Registro(salida))
        if tipo == "cupos":
            errores = auditar_cupos(recurso.iniciales, confirmadas, estado)
        else:
            errores = auditar_asientos(confirmadas, estado)
        salida(f"  Confirmadas: {', '.join(s['cliente'] for s in confirmadas) or 'ninguna'}")
        salida(f"  Estado final: {estado}")
        if errores:
            todo_ok = False
            for error in errores:
                salida(f"  ERROR: {error}")
        else:
            salida("  OK: cada cupo/asiento se confirmó a un solo cliente")

    salida("\nResultado: " + (
        "ÉXITO - no hubo reservas duplicadas." if todo_ok else
        "FALLO - hubo reservas duplicadas. Cambia USAR_LOCK = True y vuelve a ejecutar."
    ))
    return todo_ok


def main():
    ruta = Path(sys.argv[1]) if len(sys.argv) > 1 else RUTA_DATOS
    exito = ejecutar(cargar_datos(ruta), USAR_LOCK)
    sys.exit(0 if exito else 1)


if __name__ == "__main__":
    main()
