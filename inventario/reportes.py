"""Reportes en texto con columnas alineadas (no imprimen: devuelven texto)."""

from datetime import datetime


class ReporteInventario:
    """Formatea una lista de productos como tabla de ancho fijo."""

    ANCHO = 74

    def tabla(self, productos):
        """Construye la tabla de productos.

        Args:
            productos (iterable[Producto]): productos a mostrar.

        Returns:
            str: tabla con encabezado y una fila por producto.
        """
        lineas = [
            f'{"CÓDIGO":<10} {"PRODUCTO":<24} '
            f'{"CATEGORÍA":<14} {"PRECIO/KG":>12} {"STOCK KG":>10}',
            "-" * self.ANCHO,
        ]
        for p in productos:
            lineas.append(
                f"{p.codigo:<10} {p.nombre:<24.24} {p.categoria:<14.14} "
                f"Q{p.precio:>10.2f} {p.stock:>10.2f}"
            )
        return "\n".join(lineas)


class ReporteVentas:
    """Genera el reporte de ventas de un día."""

    ANCHO = 75

    def __init__(self, ventas):
        """Crea el reporte.

        Args:
            ventas (iterable[Venta]): ventas a considerar.
        """
        self._ventas = list(ventas)

    def ventas_del_dia(self, fecha=None):
        """Filtra las ventas de una fecha.

        Args:
            fecha (str | None): "AAAA-MM-DD"; por defecto hoy.

        Returns:
            list[Venta]: ventas de ese día.
        """
        fecha = fecha or datetime.now().strftime("%Y-%m-%d")
        return [v for v in self._ventas if v.fecha == fecha]

    def generar(self, fecha=None):
        """Construye el texto del reporte del día.

        Args:
            fecha (str | None): "AAAA-MM-DD"; por defecto hoy.

        Returns:
            str: reporte con columnas alineadas y totales.
        """
        fecha = fecha or datetime.now().strftime("%Y-%m-%d")
        del_dia = self.ventas_del_dia(fecha)
        titulo = f"\n--- VENTAS DEL DÍA ({fecha}) ---"
        if not del_dia:
            return titulo + "\nNo hay ventas registradas hoy."

        lineas = [
            titulo,
            f'{"HORA":<10} {"CÓDIGO":<8} {"PRODUCTO":<24} '
            f'{"KG":>8} {"PRECIO/KG":>10} {"TOTAL":>11}',
            "-" * self.ANCHO,
        ]
        for v in del_dia:
            lineas.append(
                f"{v.hora:<10} {v.codigo:<8} {v.nombre:<24.24} "
                f"{v.cantidad_kg:>8.2f} Q{v.precio_kg:>9.2f} Q{v.total:>10.2f}"
            )
        total_kg = sum(v.cantidad_kg for v in del_dia)
        total_q = sum(v.total for v in del_dia)
        lineas.append("-" * self.ANCHO)
        lineas.append(
            f"Ventas: {len(del_dia)} | Total vendido: {total_kg:.2f} kg | Q{total_q:.2f}"
        )
        return "\n".join(lineas)
