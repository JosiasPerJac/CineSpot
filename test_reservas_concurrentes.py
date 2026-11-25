import unittest

import reservas_concurrentes as r


def correr(usar_lock):
    r.USAR_LOCK = usar_lock
    r.asientos["A1"] = None
    r.confirmados.clear()
    r.main()
    return list(r.confirmados)


class ReservasTest(unittest.TestCase):
    def test_sin_lock_vende_el_asiento_varias_veces(self):
        self.assertGreater(len(correr(False)), 1)

    def test_con_lock_vende_el_asiento_una_sola_vez(self):
        confirmados = correr(True)
        self.assertEqual(confirmados, [r.asientos["A1"]])


if __name__ == "__main__":
    unittest.main()
