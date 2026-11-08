"""Persistencia: archivos CSV y bitácora."""

import csv
import os
from datetime import datetime
from pathlib import Path

from inventario.excepciones import ArchivoInventarioError, InventarioError
from inventario.inventario import Inventario
from inventario.modelos import Producto, Venta


class Bitacora:
    """Registra operaciones con fecha y hora en un archivo, en modo append."""

    FORMATO_FECHA = "%Y-%m-%d %H:%M:%S"

    def __init__(self, ruta):
        """Crea la bitácora.

        Args:
            ruta (str | Path): archivo .log (se crea si no existe).
        """
        self._ruta = Path(ruta)

    def registrar(self, mensaje):
        """Agrega una línea "fecha hora | mensaje" al final del archivo.

        Args:
            mensaje (str): texto de la operación.

        Raises:
            ArchivoInventarioError: si no se puede escribir.
        """
        try:
            self._ruta.parent.mkdir(parents=True, exist_ok=True)
            with open(self._ruta, "a", encoding="utf-8") as archivo:
                fecha_hora = datetime.now().strftime(self.FORMATO_FECHA)
                archivo.write(f"{fecha_hora} | {mensaje}\n")
        except OSError as error:
            raise ArchivoInventarioError(f"No se pudo escribir la bitácora: {error}") from error


class RepositorioCSV:
    """Lee y escribe el inventario y las ventas en archivos CSV."""

    def __init__(self, ruta_productos, ruta_ventas):
        """Crea el repositorio.

        Args:
            ruta_productos (str | Path): CSV del inventario.
            ruta_ventas (str | Path): CSV de ventas.
        """
        self._ruta_productos = Path(ruta_productos)
        self._ruta_ventas = Path(ruta_ventas)

    def asegurar_archivos(self):
        """Crea los CSV con encabezados si no existen.

        Raises:
            ArchivoInventarioError: si no se pueden crear.
        """
        try:
            for ruta, campos in (
                (self._ruta_productos, Producto.CAMPOS_CSV),
                (self._ruta_ventas, Venta.CAMPOS_CSV),
            ):
                ruta.parent.mkdir(parents=True, exist_ok=True)
                if not ruta.exists():
                    with open(ruta, "w", newline="", encoding="utf-8") as archivo:
                        csv.DictWriter(archivo, fieldnames=campos).writeheader()
        except OSError as error:
            raise ArchivoInventarioError(f"No se pudieron crear los archivos: {error}") from error

    def _leer(self, ruta, construir):
        """Lee un CSV y construye un objeto por fila con `construir`."""
        try:
            with open(ruta, "r", newline="", encoding="utf-8") as archivo:
                return [
                    construir(fila)
                    for fila in csv.DictReader(archivo)
                    if fila.get("codigo")
                ]
        except (OSError, csv.Error) as error:
            raise ArchivoInventarioError(f"No se pudo leer {ruta.name}: {error}") from error
        except InventarioError as error:
            raise ArchivoInventarioError(f"Datos inválidos en {ruta.name}: {error}") from error

    def cargar_inventario(self):
        """Carga los productos del CSV (lo crea vacío si no existe).

        Returns:
            Inventario: inventario con los productos leídos.

        Raises:
            ArchivoInventarioError: si el archivo no se puede leer o tiene
                datos inválidos.
        """
        self.asegurar_archivos()
        try:
            return Inventario(self._leer(self._ruta_productos, Producto.desde_fila_csv))
        except ArchivoInventarioError:
            raise
        except InventarioError as error:
            raise ArchivoInventarioError(f"Datos inválidos en {self._ruta_productos.name}: {error}") from error

    def guardar_inventario(self, inventario):
        """Guarda el inventario de forma segura: escribe un archivo
        temporal y luego lo reemplaza, para no perder datos si algo falla.

        Args:
            inventario (Inventario): inventario a guardar.

        Raises:
            ArchivoInventarioError: si falla la escritura.
        """
        self.asegurar_archivos()
        temporal = self._ruta_productos.with_suffix(".csv.tmp")
        try:
            with open(temporal, "w", newline="", encoding="utf-8") as archivo:
                escritor = csv.DictWriter(archivo, fieldnames=Producto.CAMPOS_CSV)
                escritor.writeheader()
                for producto in inventario:
                    escritor.writerow(producto.a_fila_csv())
            os.replace(temporal, self._ruta_productos)
        except OSError as error:
            raise ArchivoInventarioError(f"No se pudo guardar el inventario: {error}") from error

    def cargar_ventas(self):
        """Carga las ventas del CSV.

        Returns:
            list[Venta]: ventas registradas.

        Raises:
            ArchivoInventarioError: si el archivo no se puede leer.
        """
        self.asegurar_archivos()
        return self._leer(self._ruta_ventas, Venta.desde_fila_csv)

    def guardar_venta(self, venta):
        """Agrega una venta al final del archivo de ventas.

        Args:
            venta (Venta): venta a guardar.

        Raises:
            ArchivoInventarioError: si falla la escritura.
        """
        self.asegurar_archivos()
        try:
            with open(self._ruta_ventas, "a", newline="", encoding="utf-8") as archivo:
                csv.DictWriter(archivo, fieldnames=Venta.CAMPOS_CSV).writerow(venta.a_fila_csv())
        except OSError as error:
            raise ArchivoInventarioError(f"No se pudo guardar la venta: {error}") from error
