"""Excepciones personalizadas del sistema de inventario."""


class InventarioError(Exception):
    """Excepción base de todo el sistema; la capa de interfaz la captura."""


class CodigoInvalidoError(InventarioError):
    """El código no cumple el formato de tres letras y tres números."""


class DatoInvalidoError(InventarioError):
    """Un dato (nombre, precio, stock, cantidad) está vacío, no es numérico
    o está fuera de rango."""


class ProductoNoEncontradoError(InventarioError):
    """No existe un producto con el código solicitado."""


class ProductoDuplicadoError(InventarioError):
    """Ya existe un producto con el mismo código."""


class StockInsuficienteError(InventarioError):
    """La cantidad solicitada supera las existencias disponibles."""


class ArchivoInventarioError(InventarioError):
    """Un archivo de datos no se pudo leer, escribir o tiene formato roto."""
