import unittest

from reservas_concurrentes import (
    RUTA_DATOS,
    Asientos,
    Cupos,
    auditar_asientos,
    auditar_cupos,
    cargar_datos,
    ejecutar,
    simular,
)

SOLICITUDES = [
    {"cliente": "Ana", "asiento": "A1"},
    {"cliente": "Luis", "asiento": "A1"},
    {"cliente": "Marta", "asiento": "A1"},
]


class ReservasConcurrentesTest(unittest.TestCase):
    def test_cupos_sin_lock_la_auditoria_detecta_sobreventa(self):
        recurso = Cupos(1)
        confirmadas, restantes = simular(recurso, SOLICITUDES, usar_lock=False)
        self.assertGreater(len(confirmadas), 1)
        self.assertTrue(auditar_cupos(1, confirmadas, restantes))

    def test_cupos_con_lock_confirma_una_vez(self):
        recurso = Cupos(1)
        confirmadas, restantes = simular(recurso, SOLICITUDES, usar_lock=True)
        self.assertEqual(len(confirmadas), 1)
        self.assertEqual(restantes, 0)
        self.assertEqual(auditar_cupos(1, confirmadas, restantes), [])

    def test_asientos_sin_lock_la_auditoria_detecta_duplicado(self):
        confirmadas, mapa = simular(Asientos(["A1"]), SOLICITUDES, usar_lock=False)
        self.assertGreater(len(confirmadas), 1)
        self.assertIn(mapa["A1"], [s["cliente"] for s in confirmadas])
        self.assertTrue(auditar_asientos(confirmadas, mapa))

    def test_asientos_con_lock_registra_al_unico_cliente_confirmado(self):
        confirmadas, mapa = simular(Asientos(["A1"]), SOLICITUDES, usar_lock=True)
        self.assertEqual([s["cliente"] for s in confirmadas], [mapa["A1"]])
        self.assertEqual(auditar_asientos(confirmadas, mapa), [])

    def test_solicitud_de_asiento_inexistente_no_modifica_el_mapa(self):
        recurso = Asientos(["A1"])
        self.assertFalse(recurso.reservar("Ana", "B2"))
        self.assertEqual(recurso.estado, {"A1": None})

    def test_ejecucion_completa_falla_sin_lock_y_pasa_con_lock(self):
        datos = cargar_datos(RUTA_DATOS)
        silencio = lambda _linea: None
        self.assertFalse(ejecutar(datos, usar_lock=False, salida=silencio))
        self.assertTrue(ejecutar(datos, usar_lock=True, salida=silencio))


if __name__ == "__main__":
    unittest.main()
