import unittest

from reservas_concurrentes import Asientos, Cupos, simular


class ReservasConcurrentesTest(unittest.TestCase):
    def test_cupos_sin_lock_confirma_dos_veces(self):
        respuestas, restantes = simular(Cupos(1), usar_lock=False)
        self.assertEqual(respuestas, {"Ana": True, "Luis": True})
        self.assertEqual(restantes, 0)

    def test_cupos_con_lock_confirma_una_vez(self):
        respuestas, restantes = simular(Cupos(1), usar_lock=True)
        self.assertEqual(sum(respuestas.values()), 1)
        self.assertEqual(restantes, 0)

    def test_asientos_sin_lock_confirma_dos_veces_y_conserva_un_titular(self):
        respuestas, asientos = simular(Asientos(["A1"]), usar_lock=False)
        self.assertEqual(respuestas, {"Ana": True, "Luis": True})
        self.assertIn(asientos["A1"], respuestas)

    def test_asientos_con_lock_registra_al_unico_cliente_confirmado(self):
        respuestas, asientos = simular(Asientos(["A1"]), usar_lock=True)
        confirmados = [cliente for cliente, aceptada in respuestas.items() if aceptada]
        self.assertEqual(confirmados, [asientos["A1"]])

    def test_solicitud_de_asiento_inexistente_no_modifica_el_mapa(self):
        recurso = Asientos(["A1"])
        self.assertFalse(recurso.reservar("Ana", "B2"))
        self.assertEqual(recurso.estado, {"A1": None})


if __name__ == "__main__":
    unittest.main()
