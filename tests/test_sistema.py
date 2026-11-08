"""Pruebas unitarias del sistema (unittest, biblioteca estándar)."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from inventario.excepciones import (
    ArchivoInventarioError, CodigoInvalidoError, DatoInvalidoError,
    InventarioError, ProductoDuplicadoError, ProductoNoEncontradoError,
    StockInsuficienteError,
)
from inventario.inventario import Inventario
from inventario.modelos import Producto, Venta
from inventario.persistencia import Bitacora, RepositorioCSV
from inventario.reglas import AlertaStock, ReglaNegocio
from inventario.reportes import ReporteVentas


def brisket(stock=10):
    return Producto("bac200", " Brisket ", "res", 40, stock, 5)


class PruebasProducto(unittest.TestCase):
    def test_normaliza_datos(self):
        p = brisket()
        self.assertEqual((p.codigo, p.nombre, p.categoria), ("BAC200", "Brisket", "Res"))

    def test_codigo_invalido(self):
        with self.assertRaises(CodigoInvalidoError):
            Producto("2", "X", "Y", 1, 1, 1)

    def test_precio_y_stock_validados(self):
        p = brisket()
        with self.assertRaises(DatoInvalidoError):
            p.precio = -1
        with self.assertRaises(DatoInvalidoError):
            p.stock = -0.1
        with self.assertRaises(DatoInvalidoError):
            p.precio = "abc"
        with self.assertRaises(DatoInvalidoError):
            p.precio = float("nan")

    def test_descontar_stock(self):
        p = brisket()
        p.descontar_stock(5)
        self.assertEqual(p.stock, 5)
        with self.assertRaises(StockInsuficienteError):
            p.descontar_stock(5.01)
        with self.assertRaises(DatoInvalidoError):
            p.descontar_stock(0)
        self.assertEqual(p.stock, 5)

    def test_excepciones_heredan_de_base(self):
        for exc in (CodigoInvalidoError, StockInsuficienteError, ProductoNoEncontradoError):
            self.assertTrue(issubclass(exc, InventarioError))

    def test_especiales(self):
        p = brisket()
        self.assertIn("BAC200", str(p))
        self.assertIn("Producto(", repr(p))
        self.assertEqual(p, Producto("BAC200", "Otro", "Res", 1, 1, 1))


class PruebasInventario(unittest.TestCase):
    def setUp(self):
        self.inv = Inventario([
            brisket(),
            Producto("POL003", "Muslo de pollo", "pollo", 24, 28, 5),
            Producto("EMB001", "Chorizo", "Embutido", 38, 12, 3),
        ])

    def test_len_contains_iter(self):
        self.assertEqual(len(self.inv), 3)
        self.assertIn("bac200", self.inv)
        self.assertEqual(len(list(self.inv)), 3)

    def test_duplicado_y_no_encontrado(self):
        with self.assertRaises(ProductoDuplicadoError):
            self.inv.agregar(brisket())
        with self.assertRaises(ProductoNoEncontradoError):
            self.inv.obtener("ZZZ999")

    def test_busqueda_parcial_sin_mayusculas(self):
        self.assertEqual([p.codigo for p in self.inv.buscar("POLLO")], ["POL003"])
        self.assertEqual([p.codigo for p in self.inv.buscar("emb")], ["EMB001"])

    def test_orden(self):
        self.assertEqual([p.codigo for p in self.inv.ordenados_por_nombre()],
                         ["BAC200", "EMB001", "POL003"])
        self.assertEqual([p.codigo for p in self.inv.ordenados_por_precio()],
                         ["POL003", "EMB001", "BAC200"])

    def test_categorias_set(self):
        self.assertEqual(self.inv.categorias(), {"Res", "Pollo", "Embutido"})


class PruebasReglas(unittest.TestCase):
    def test_niveles(self):
        alerta = AlertaStock()
        self.assertIsNone(alerta.evaluar(brisket(5.01)))
        self.assertEqual(alerta.evaluar(brisket(5)).nivel, "BAJO")
        self.assertEqual(alerta.evaluar(brisket(2.5)).nivel, "CRÍTICO")
        self.assertEqual(alerta.evaluar(brisket(0)).nivel, "AGOTADO")

    def test_abstracta(self):
        with self.assertRaises(TypeError):
            ReglaNegocio()

    def test_generar(self):
        inv = Inventario([brisket(2.5), Producto("POL003", "Pollo", "Pollo", 24, 28, 5)])
        self.assertEqual(len(AlertaStock().generar(inv)), 1)


class PruebasPersistencia(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.repo = RepositorioCSV(base / "datos" / "inv.csv", base / "datos" / "ventas.csv")
        self.bitacora = Bitacora(base / "datos" / "bitacora.log")
        self.base = base

    def tearDown(self):
        self.tmp.cleanup()

    def test_crea_archivos_si_no_existen(self):
        inv = self.repo.cargar_inventario()
        self.assertEqual(len(inv), 0)
        self.assertEqual(self.repo.cargar_ventas(), [])

    def test_guardar_y_cargar(self):
        self.repo.guardar_inventario(Inventario([brisket()]))
        self.assertEqual(self.repo.cargar_inventario().obtener("BAC200").stock, 10)

    def test_venta_ida_y_vuelta_e_inmutable(self):
        venta = Venta.crear(brisket(), 5)
        self.assertEqual(venta.total, 200.0)
        self.repo.guardar_venta(venta)
        self.assertEqual(self.repo.cargar_ventas(), [venta])
        with self.assertRaises(Exception):
            venta.total = 1

    def test_csv_corrupto(self):
        self.repo.asegurar_archivos()
        (self.base / "datos" / "inv.csv").write_text(
            "codigo,nombre,categoria,precio,stock,stock_minimo\nXX,a,b,c,d,e\n", encoding="utf-8")
        with self.assertRaises(ArchivoInventarioError):
            self.repo.cargar_inventario()

    def test_bitacora_append(self):
        self.bitacora.registrar("uno")
        self.bitacora.registrar("dos")
        lineas = (self.base / "datos" / "bitacora.log").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lineas), 2)
        self.assertTrue(lineas[1].endswith("| dos"))


class PruebasReporte(unittest.TestCase):
    def test_reporte_del_dia(self):
        v = Venta.crear(brisket(), 5)
        texto = ReporteVentas([v]).generar()
        self.assertIn("BAC200", texto)
        self.assertIn("Total vendido: 5.00 kg | Q200.00", texto)
        self.assertIn("No hay ventas", ReporteVentas([]).generar())


if __name__ == "__main__":
    unittest.main()
