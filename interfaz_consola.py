"""CineSpot: interfaz por consola para ejecutar las cuatro versiones."""

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
    "asiento_pedido": "A1",
    "demora_ms": 100,
}

_impresion = threading.Lock()  # Solo evita que las filas se mezclen al imprimir.


def solicitudes():
    usuarios = [f"U{i:02d}" for i in range(1, config["hilos"] + 1)]
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
    print("  0. Salir")


def ejecutar_version(tipo, usar_lock):
    anchos = {}

    def imprimir_fila(t):
        with _impresion:
            print(f"{t.name:<8} {t.id_hilo:<8} {t.operacion:<16} "
                  f"{t.antes:<{anchos['estado']}} {t.resultado:<20} {t.despues}")

    simulador = SimuladorCineSpot(tipo, usar_lock, solicitudes(), config["asientos"],
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


def main():
    while True:
        mostrar_menu()
        opcion = input("Elige una opción: ").strip()
        if opcion in VERSIONES:
            ejecutar_version(*VERSIONES[opcion])
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
