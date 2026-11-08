"""Modelos de datos: Producto y Venta.

Las clases de este módulo solo guardan datos y los validan; no imprimen,
no leen el teclado ni tocan archivos.
"""

import math
import re
from dataclasses import dataclass
from datetime import datetime

from inventario.excepciones import (
    CodigoInvalidoError,
    DatoInvalidoError,
    StockInsuficienteError,
)


class Producto:
    """Producto de la carnicería (se vende por kilogramo).

    Los atributos son protegidos y se acceden mediante propiedades con
    validación: el código debe cumplir el formato, el precio debe ser
    positivo y el stock nunca puede quedar por debajo de cero.
    """

    PATRON_CODIGO = re.compile(r"[A-Z]{3}[0-9]{3}")
    CAMPOS_CSV = ("codigo", "nombre", "categoria", "precio", "stock", "stock_minimo")

    def __init__(self, codigo, nombre, categoria, precio, stock, stock_minimo):
        """Crea un producto validando todos sus datos.

        Args:
            codigo (str): tres letras y tres números (ej. "RES001").
            nombre (str): nombre del producto.
            categoria (str): categoría (se normaliza a formato título).
            precio (float): precio por kg en quetzales, mayor que cero.
            stock (float): existencias en kg, no negativas.
            stock_minimo (float): umbral de reabastecimiento en kg.

        Raises:
            CodigoInvalidoError: si el código no cumple el formato.
            DatoInvalidoError: si algún otro dato es inválido.
        """
        self._codigo = self.validar_codigo(codigo)
        self.nombre = nombre
        self.categoria = categoria
        self.precio = precio
        self.stock = stock
        self.stock_minimo = stock_minimo

    # ---------- métodos estáticos y de clase ----------

    @staticmethod
    def normalizar(texto):
        """Quita espacios sobrantes de una cadena.

        Args:
            texto (str): cadena a normalizar.

        Returns:
            str: la cadena sin espacios al inicio, al final ni repetidos.
        """
        return " ".join(str(texto).strip().split())

    @staticmethod
    def a_numero(valor, campo):
        """Convierte un valor a float finito.

        Args:
            valor: texto o número recibido.
            campo (str): nombre del dato, para el mensaje de error.

        Returns:
            float: el número convertido.

        Raises:
            DatoInvalidoError: si no es numérico o no es finito.
        """
        try:
            numero = float(valor)
        except (TypeError, ValueError):
            raise DatoInvalidoError(f"{campo} debe ser un número.") from None
        if not math.isfinite(numero):
            raise DatoInvalidoError(f"{campo} debe ser un número válido.")
        return numero

    @classmethod
    def validar_codigo(cls, codigo):
        """Valida y normaliza un código de producto.

        Args:
            codigo (str): código escrito por el usuario.

        Returns:
            str: el código en mayúsculas.

        Raises:
            CodigoInvalidoError: si no son tres letras y tres números.
        """
        limpio = str(codigo).strip().upper()
        if not cls.PATRON_CODIGO.fullmatch(limpio):
            raise CodigoInvalidoError(
                f"Código inválido '{codigo}'. Usa tres letras y tres números."
            )
        return limpio

    @classmethod
    def desde_fila_csv(cls, fila):
        """Crea un producto desde una fila (diccionario) del CSV.

        Args:
            fila (dict): fila leída con csv.DictReader.

        Returns:
            Producto: el producto construido.

        Raises:
            DatoInvalidoError / CodigoInvalidoError: si la fila es inválida.
        """
        try:
            return cls(*(fila[campo] for campo in cls.CAMPOS_CSV))
        except KeyError as error:
            raise DatoInvalidoError(f"Falta la columna {error} en el CSV.") from None

    # ---------- propiedades ----------

    @property
    def codigo(self):
        """str: código único (solo lectura)."""
        return self._codigo

    @property
    def nombre(self):
        """str: nombre del producto (no puede quedar vacío)."""
        return self._nombre

    @nombre.setter
    def nombre(self, valor):
        valor = self.normalizar(valor)
        if not valor:
            raise DatoInvalidoError("El nombre no puede estar vacío.")
        self._nombre = valor

    @property
    def categoria(self):
        """str: categoría en formato título (no puede quedar vacía)."""
        return self._categoria

    @categoria.setter
    def categoria(self, valor):
        valor = self.normalizar(valor).title()
        if not valor:
            raise DatoInvalidoError("La categoría no puede estar vacía.")
        self._categoria = valor

    @property
    def precio(self):
        """float: precio por kg; debe ser mayor que cero."""
        return self._precio

    @precio.setter
    def precio(self, valor):
        valor = self.a_numero(valor, "El precio")
        if valor <= 0:
            raise DatoInvalidoError("El precio debe ser mayor que cero.")
        self._precio = valor

    @property
    def stock(self):
        """float: existencias en kg; nunca negativas."""
        return self._stock

    @stock.setter
    def stock(self, valor):
        valor = self.a_numero(valor, "El stock")
        if valor < 0:
            raise DatoInvalidoError("El stock no puede ser negativo.")
        self._stock = round(valor, 2)

    @property
    def stock_minimo(self):
        """float: umbral de reabastecimiento en kg; no negativo."""
        return self._stock_minimo

    @stock_minimo.setter
    def stock_minimo(self, valor):
        valor = self.a_numero(valor, "El stock mínimo")
        if valor < 0:
            raise DatoInvalidoError("El stock mínimo no puede ser negativo.")
        self._stock_minimo = valor

    # ---------- comportamiento ----------

    def verificar_venta(self, cantidad):
        """Comprueba que se pueda vender `cantidad` kg, sin modificar nada.

        Args:
            cantidad (float): kg que se quieren vender.

        Returns:
            float: la cantidad convertida a número.

        Raises:
            DatoInvalidoError: si la cantidad no es un número positivo.
            StockInsuficienteError: si supera las existencias.
        """
        cantidad = self.a_numero(cantidad, "La cantidad")
        if cantidad <= 0:
            raise DatoInvalidoError("La cantidad debe ser mayor que cero.")
        if cantidad > self._stock:
            raise StockInsuficienteError(
                f"Stock insuficiente de {self._codigo}: "
                f"pides {cantidad:.2f} kg y hay {self._stock:.2f} kg."
            )
        return cantidad

    def descontar_stock(self, cantidad):
        """Resta kilogramos vendidos de las existencias.

        Args:
            cantidad (float): kg a descontar, mayor que cero.

        Raises:
            DatoInvalidoError: si la cantidad no es positiva.
            StockInsuficienteError: si supera las existencias.
        """
        cantidad = self.verificar_venta(cantidad)
        self._stock = round(self._stock - cantidad, 2)

    def necesita_reabastecer(self):
        """Indica si el stock llegó al mínimo o está por debajo.

        Returns:
            bool: True si stock <= stock_minimo.
        """
        return self._stock <= self._stock_minimo

    def a_fila_csv(self):
        """Convierte el producto a un diccionario listo para el CSV.

        Returns:
            dict: columnas del CSV con precio y stock a dos decimales.
        """
        return {
            "codigo": self._codigo,
            "nombre": self._nombre,
            "categoria": self._categoria,
            "precio": f"{self._precio:.2f}",
            "stock": f"{self._stock:.2f}",
            "stock_minimo": f"{self._stock_minimo:.2f}",
        }

    # ---------- métodos especiales ----------

    def __str__(self):
        return (
            f"{self._codigo} - {self._nombre} ({self._categoria}) "
            f"Q{self._precio:.2f}/kg, {self._stock:.2f} kg"
        )

    def __repr__(self):
        return (
            f"Producto(codigo={self._codigo!r}, nombre={self._nombre!r}, "
            f"categoria={self._categoria!r}, precio={self._precio}, "
            f"stock={self._stock}, stock_minimo={self._stock_minimo})"
        )

    def __eq__(self, otro):
        """Dos productos son iguales si comparten código."""
        if not isinstance(otro, Producto):
            return NotImplemented
        return self._codigo == otro._codigo

    def __hash__(self):
        return hash(self._codigo)


@dataclass(frozen=True)
class Venta:
    """Registro inmutable de una venta.

    Attributes:
        fecha_hora (str): "AAAA-MM-DD HH:MM:SS".
        codigo (str): código del producto vendido.
        nombre (str): nombre del producto al momento de la venta.
        cantidad_kg (float): kilogramos vendidos.
        precio_kg (float): precio por kg al momento de la venta.
        total (float): cantidad * precio, redondeado a 2 decimales.
    """

    FORMATO_FECHA = "%Y-%m-%d %H:%M:%S"
    CAMPOS_CSV = ("fecha_hora", "codigo", "nombre", "cantidad_kg", "precio_kg", "total")

    fecha_hora: str
    codigo: str
    nombre: str
    cantidad_kg: float
    precio_kg: float
    total: float

    @classmethod
    def crear(cls, producto, cantidad):
        """Construye la venta de `cantidad` kg de un producto, ahora mismo.

        No descuenta stock: eso lo hace Producto.descontar_stock.

        Args:
            producto (Producto): producto vendido.
            cantidad (float): kg vendidos.

        Returns:
            Venta: la venta con el total calculado.
        """
        return cls(
            fecha_hora=datetime.now().strftime(cls.FORMATO_FECHA),
            codigo=producto.codigo,
            nombre=producto.nombre,
            cantidad_kg=cantidad,
            precio_kg=producto.precio,
            total=round(cantidad * producto.precio, 2),
        )

    @classmethod
    def desde_fila_csv(cls, fila):
        """Crea una venta desde una fila del CSV de ventas.

        Args:
            fila (dict): fila leída con csv.DictReader.

        Returns:
            Venta: la venta construida.

        Raises:
            DatoInvalidoError: si falta una columna o un número es inválido.
        """
        try:
            return cls(
                fila["fecha_hora"],
                fila["codigo"],
                fila["nombre"],
                Producto.a_numero(fila["cantidad_kg"], "cantidad_kg"),
                Producto.a_numero(fila["precio_kg"], "precio_kg"),
                Producto.a_numero(fila["total"], "total"),
            )
        except KeyError as error:
            raise DatoInvalidoError(f"Falta la columna {error} en ventas.csv.") from None

    @property
    def fecha(self):
        """str: parte de la fecha (AAAA-MM-DD)."""
        return self.fecha_hora[:10]

    @property
    def hora(self):
        """str: parte de la hora (HH:MM:SS)."""
        return self.fecha_hora[11:]

    def a_fila_csv(self):
        """Convierte la venta a un diccionario listo para el CSV.

        Returns:
            dict: columnas del CSV con números a dos decimales.
        """
        return {
            "fecha_hora": self.fecha_hora,
            "codigo": self.codigo,
            "nombre": self.nombre,
            "cantidad_kg": f"{self.cantidad_kg:.2f}",
            "precio_kg": f"{self.precio_kg:.2f}",
            "total": f"{self.total:.2f}",
        }

    def __str__(self):
        return (
            f"{self.fecha_hora} {self.codigo} {self.nombre}: "
            f"{self.cantidad_kg:.2f} kg = Q{self.total:.2f}"
        )
