import unittest

from reservas_concurrentes import (
    CONFIRMADA,
    INVALIDA,
    OCUPADO,
    SalaCine,
    SimuladorCineSpot,
)

SOLICITUDES = [("U01", "A1"), ("U02", "A1"), ("U03", "A1")]
ASIENTOS = ["A1", "A2"]


def simular(tipo, usar_lock):
    simulador = SimuladorCineSpot(tipo, usar_lock, SOLICITUDES, ASIENTOS, demora=0.05)
    estado_final = simulador.ejecutar()
    return simulador, estado_final


class CuatroVersionesTest(unittest.TestCase):
    def test_basico_sin_lock_tiene_condicion_de_carrera(self):
        simulador, estado = simular("basico", False)
        self.assertGreater(len(simulador.confirmadas()), 1)
        self.assertTrue(simulador.condiciones_de_carrera())
        self.assertEqual(estado, "1 (reservado)")

    def test_basico_con_lock_confirma_una_sola_vez(self):
        simulador, estado = simular("basico", True)
        self.assertEqual(len(simulador.confirmadas()), 1)
        self.assertEqual(simulador.condiciones_de_carrera(), {})
        self.assertEqual(estado, "1 (reservado)")

    def test_complejo_sin_lock_tiene_condicion_de_carrera(self):
        simulador, _ = simular("complejo", False)
        self.assertIn("A1", simulador.condiciones_de_carrera())

    def test_complejo_con_lock_registra_al_unico_confirmado(self):
        simulador, estado = simular("complejo", True)
        [ganador] = simulador.confirmadas()
        self.assertEqual(estado, f"A1={ganador.usuario}, A2=libre")
        self.assertEqual(simulador.condiciones_de_carrera(), {})

    def test_cada_hilo_registra_id_estado_antes_resultado_y_despues(self):
        simulador, _ = simular("complejo", True)
        for t in simulador.trabajadores:
            self.assertIsNotNone(t.id_hilo)
            self.assertIn(t.resultado, (CONFIRMADA, OCUPADO))
            self.assertIsNotNone(t.antes)
            self.assertIsNotNone(t.despues)


class SalaCineTest(unittest.TestCase):
    def test_asiento_inexistente_es_solicitud_invalida(self):
        sala = SalaCine("F01", ["A1"])
        resultado, antes, despues = sala.reservar_asiento("Z9", "U01")
        self.assertEqual(resultado, INVALIDA)
        self.assertEqual(antes, despues)
        self.assertEqual(sala.consultar(), "A1=libre")


if __name__ == "__main__":
    unittest.main()
