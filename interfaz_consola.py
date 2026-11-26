"""CineSpot: interfaz por consola para ejecutar y comparar las cuatro versiones."""

import random
import threading

from reservas_concurrentes import SimuladorCineSpot

VERSIONES = {
    "1": ("basico", False),
    "2": ("basico", True),
    "3": ("complejo", False),
    "4": ("complejo", True),
}

config = {
    "hilos": 3,
    "asientos": ["A1", "A2", "A3"],
    "asiento_pedido": "A1",  # o "aleatorio"
    "demora_ms": 100,
}

_impresion = threading.Lock()  # Solo evita que las filas se mezclen al imprimir.


def solicitudes():
    usuarios = [f"U{i:02d}" for i in range(1, config["hilos"] + 1)]
    if config["asiento_pedido"] == "aleatorio":
        return [(u, random.choice(config["asientos"])) for u in usuarios]
    return [(u, config["asiento_pedido"]) for u in usuarios]


def mostrar_menu():
    print("\n========== CineSpot · Reservas concurrentes ==========")
    print(f"Configuración: {config['hilos']} hilos | Asientos: "
          f"{', '.join(config['asientos'])} | Asiento pedido: "
          f"{config['asiento_pedido']} | Demora: {config['demora_ms']} ms")
    print("  1. Tipo básico (entero)        SIN Lock")
    print("  2. Tipo básico (entero)        CON Lock")
    print("  3. Tipo complejo (diccionario) SIN Lock")
    print("  4. Tipo complejo (diccionario) CON Lock")
    print("  5. Ejecutar y comparar las 4 versiones")
    print("  6. Cambiar configuración")
    print("  0. Salir")


def ejecutar_version(tipo, usar_lock, pedidos=None):
    anchos = {}

    def imprimir_fila(t):
        with _impresion:
            print(f"{t.name:<8} {t.id_hilo:<8} {t.operacion:<16} "
                  f"{t.antes:<{anchos['estado']}} {t.resultado:<20} {t.despues}")

    simulador = SimuladorCineSpot(tipo, usar_lock, pedidos or solicitudes(), config["asientos"],
                                  config["demora_ms"] / 1000, imprimir_fila)
    anchos["estado"] = max(len(simulador.estado_inicial), len("Estado antes"))

    print(f"\n--- {simulador.version} | Función {simulador.sala.id_funcion} ---")
    print(f"Estado inicial: {simulador.estado_inicial}\n")
    print(f"{'Hilo':<8} {'ID':<8} {'Operación':<16} {'Estado antes':<{anchos['estado']}} "
          f"{'Resultado':<20} Estado después")
    print("-" * (78 + anchos["estado"]))

    estado_final = simulador.ejecutar()

    print(f"\nEstado final del recurso: {estado_final}")
    confirmadas = simulador.confirmadas()
    print(f"Confirmadas: {len(confirmadas)} "
          f"({', '.join(t.usuario for t in confirmadas) or 'ninguna'}) | "
          f"Rechazadas: {len(simulador.trabajadores) - len(confirmadas)}")
    carreras = simulador.condiciones_de_carrera()
    if carreras:
        for asiento, usuarios in carreras.items():
            print(f"CONDICIÓN DE CARRERA: {asiento} se confirmó a {len(usuarios)} "
                  f"usuarios ({', '.join(usuarios)}).")
    else:
        print("Sin condición de carrera: cada asiento se confirmó a un solo usuario.")
    return simulador, estado_final


def comparar():
    filas = []
    pedidos = solicitudes()  # Las 4 versiones reciben exactamente las mismas solicitudes.
    for tipo, usar_lock in VERSIONES.values():
        simulador, estado_final = ejecutar_version(tipo, usar_lock, pedidos)
        filas.append((simulador.version, len(simulador.confirmadas()),
                      "Sí" if simulador.condiciones_de_carrera() else "No", estado_final))

    print("\n================ Comparación de las 4 versiones ================")
    print(f"{'Versión':<32} {'Confirmadas':<12} {'¿Carrera?':<10} Estado final")
    for version, confirmadas, carrera, estado in filas:
        print(f"{version:<32} {confirmadas:<12} {carrera:<10} {estado}")


def pedir(texto, actual):
    valor = input(f"{texto} [{actual}]: ").strip()
    return valor or str(actual)


def pedir_entero(texto, actual, minimo, maximo):
    while True:
        valor = pedir(texto, actual)
        if valor.isdigit() and minimo <= int(valor) <= maximo:
            return int(valor)
        print(f"  Ingresa un número entre {minimo} y {maximo}.")


def configurar():
    print("\nPresiona Enter para conservar el valor actual.")
    config["hilos"] = pedir_entero("Número de hilos (usuarios)", config["hilos"], 1, 50)
    while True:
        asientos = pedir("Asientos de la sala, separados por coma",
                         ",".join(config["asientos"]))
        lista = [a.strip().upper() for a in asientos.split(",") if a.strip()]
        if lista:
            config["asientos"] = list(dict.fromkeys(lista))
            break
        print("  Ingresa al menos un asiento.")
    pedido = pedir("Asiento que piden los hilos (o 'aleatorio')", config["asiento_pedido"])
    config["asiento_pedido"] = "aleatorio" if pedido.lower() == "aleatorio" else pedido.upper()
    config["demora_ms"] = pedir_entero("Demora entre validar y registrar (ms)",
                                       config["demora_ms"], 0, 2000)


def main():
    while True:
        mostrar_menu()
        opcion = input("Elige una opción: ").strip()
        if opcion in VERSIONES:
            ejecutar_version(*VERSIONES[opcion])
        elif opcion == "5":
            comparar()
        elif opcion == "6":
            configurar()
            continue
        elif opcion == "0":
            print("Hasta luego.")
            return
        else:
            print("Opción no válida.")
            continue
        input("\nPresiona Enter para volver al menú...")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nHasta luego.")
