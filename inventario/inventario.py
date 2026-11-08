"""Colección de productos."""

from inventario.excepciones import ProductoDuplicadoError, ProductoNoEncontradoError
from inventario.modelos import Producto


class Inventario:
    """Colección de objetos Producto indexados por código (composición).

    La estructura principal es un diccionario {codigo: Producto}.
    Soporta len(inventario), "RES001" in inventario e iteración.
    """

    def __init__(self, productos=()):
        """Crea el inventario, opcionalmente con productos iniciales.

        Args:
            productos (iterable[Producto]): productos de partida.

        Raises:
            ProductoDuplicadoError: si hay códigos repetidos.
        """
        self._productos = {}
        for producto in productos:
            self.agregar(producto)

    def agregar(self, producto):
        """Agrega un producto nuevo.

        Args:
            producto (Producto): producto a agregar.

        Raises:
            ProductoDuplicadoError: si ya existe ese código.
        """
        if producto.codigo in self._productos:
            raise ProductoDuplicadoError(
                f"Ya existe un producto con el código {producto.codigo}."
            )
        self._productos[producto.codigo] = producto

    def obtener(self, codigo):
        """Devuelve el producto con ese código.

        Args:
            codigo (str): código (se normaliza y valida).

        Returns:
            Producto: el producto encontrado.

        Raises:
            ProductoNoEncontradoError: si no existe.
        """
        clave = str(codigo).strip().upper()
        try:
            return self._productos[clave]
        except KeyError:
            raise ProductoNoEncontradoError(
                f"No existe un producto con el código '{codigo}'."
            ) from None

    def buscar(self, consulta):
        """Busca por código o parte del nombre, sin distinguir mayúsculas.

        Args:
            consulta (str): texto a buscar.

        Returns:
            list[Producto]: productos que coinciden (lista vacía si ninguno).
        """
        texto = Producto.normalizar(consulta).casefold()
        return [
            p for p in self._productos.values()
            if texto in p.codigo.casefold() or texto in p.nombre.casefold()
        ]

    def ordenados_por_nombre(self):
        """Devuelve los productos ordenados alfabéticamente por nombre.

        Returns:
            list[Producto]: lista ordenada.
        """
        return sorted(self._productos.values(), key=lambda p: p.nombre.casefold())

    def ordenados_por_precio(self):
        """Devuelve los productos ordenados de menor a mayor precio.

        Returns:
            list[Producto]: lista ordenada.
        """
        return sorted(self._productos.values(), key=lambda p: p.precio)

    def categorias(self):
        """Devuelve las categorías sin duplicados.

        Returns:
            set[str]: conjunto de categorías.
        """
        return {p.categoria for p in self._productos.values()}

    def __len__(self):
        return len(self._productos)

    def __contains__(self, codigo):
        return str(codigo).strip().upper() in self._productos

    def __iter__(self):
        return iter(self._productos.values())

    def __repr__(self):
        return f"Inventario({len(self)} productos)"
