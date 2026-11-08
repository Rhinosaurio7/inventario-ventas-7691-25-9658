"""Regla de negocio asignada: alerta de stock mínimo.

Jerarquía:
    ReglaNegocio (abstracta)
        ├── ReglaAgotado       -> stock == 0
        ├── ReglaStockCritico  -> stock <= 50 % del mínimo
        └── ReglaStockBajo     -> stock <= mínimo

Ejemplo numérico: Brisket con mínimo 5 kg.
    stock 5.00 kg -> BAJO | stock 2.50 kg -> CRÍTICO | stock 0 kg -> AGOTADO
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class Alerta:
    """Aviso de reabastecimiento (inmutable).

    Attributes:
        nivel (str): "AGOTADO", "CRÍTICO" o "BAJO".
        mensaje (str): texto para mostrar al usuario.
    """

    nivel: str
    mensaje: str

    def __str__(self):
        return f"[{self.nivel}] {self.mensaje}"


class ReglaNegocio(ABC):
    """Regla que evalúa un producto y decide si genera una alerta."""

    @property
    @abstractmethod
    def nivel(self):
        """str: nombre del nivel de alerta que produce la regla."""

    @abstractmethod
    def aplica(self, producto):
        """Indica si la regla se cumple para el producto.

        Args:
            producto (Producto): producto a evaluar.

        Returns:
            bool: True si el producto cae en este nivel.
        """

    def evaluar(self, producto):
        """Genera la alerta si la regla aplica (método plantilla).

        Args:
            producto (Producto): producto a evaluar.

        Returns:
            Alerta | None: la alerta, o None si la regla no aplica.
        """
        if not self.aplica(producto):
            return None
        mensaje = (
            f"{producto.nombre}: {producto.stock:.2f} kg "
            f"(mínimo {producto.stock_minimo:.2f} kg)"
        )
        return Alerta(self.nivel, mensaje)


class ReglaAgotado(ReglaNegocio):
    """El producto no tiene existencias."""

    def __init__(self):
        """Crea la regla (no necesita parámetros)."""
        super().__init__()

    @property
    def nivel(self):
        """str: nivel de alerta (AGOTADO)."""
        return "AGOTADO"

    def aplica(self, producto):
        """True si el stock es cero."""
        return producto.stock == 0


class ReglaStockCritico(ReglaNegocio):
    """El stock está en la mitad del mínimo o menos."""

    def __init__(self, proporcion=0.5):
        """Crea la regla.

        Args:
            proporcion (float): fracción del mínimo que marca lo crítico.
        """
        super().__init__()
        self._proporcion = proporcion

    @property
    def nivel(self):
        """str: nivel de alerta (CRÍTICO)."""
        return "CRÍTICO"

    def aplica(self, producto):
        """True si stock <= stock_minimo * proporción."""
        return producto.stock <= producto.stock_minimo * self._proporcion


class ReglaStockBajo(ReglaNegocio):
    """El stock llegó al mínimo o está por debajo."""

    def __init__(self):
        """Crea la regla (usa Producto.necesita_reabastecer)."""
        super().__init__()

    @property
    def nivel(self):
        """str: nivel de alerta (BAJO)."""
        return "BAJO"

    def aplica(self, producto):
        """True si el producto necesita reabastecerse."""
        return producto.necesita_reabastecer()


class AlertaStock:
    """Recorre el inventario aplicando las reglas, de la más grave a la menos.

    Polimorfismo: llama a regla.evaluar(producto) sin preguntar el tipo.
    """

    def __init__(self, reglas=None):
        """Crea el evaluador.

        Args:
            reglas (list[ReglaNegocio] | None): reglas ordenadas por
                gravedad; por defecto Agotado, Crítico y Bajo.
        """
        self._reglas = list(reglas) if reglas is not None else [
            ReglaAgotado(), ReglaStockCritico(), ReglaStockBajo()
        ]

    def evaluar(self, producto):
        """Devuelve la alerta más grave de un producto.

        Args:
            producto (Producto): producto a evaluar.

        Returns:
            Alerta | None: primera alerta que aplica, o None.
        """
        for regla in self._reglas:
            alerta = regla.evaluar(producto)
            if alerta is not None:
                return alerta
        return None

    def generar(self, inventario):
        """Genera las alertas de todo el inventario.

        Args:
            inventario (Inventario): inventario a revisar.

        Returns:
            list[Alerta]: alertas encontradas (vacía si todo está bien).
        """
        alertas = (self.evaluar(producto) for producto in inventario)
        return [a for a in alertas if a is not None]
