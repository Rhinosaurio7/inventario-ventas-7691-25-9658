"""Interfaz de consola y coordinación de los demás objetos."""

from pathlib import Path

from inventario.excepciones import ArchivoInventarioError, InventarioError
from inventario.modelos import Producto, Venta
from inventario.persistencia import Bitacora, RepositorioCSV
from inventario.reglas import AlertaStock
from inventario.reportes import ReporteInventario, ReporteVentas


class Consola:
    """Entrada y salida por consola (la única clase que usa input/print)."""

    @staticmethod
    def leer(mensaje):
        """Lee una línea sin espacios en los extremos.

        Args:
            mensaje (str): texto de la pregunta.

        Returns:
            str: lo que escribió el usuario.
        """
        return input(mensaje).strip()

    @staticmethod
    def mostrar(texto=""):
        """Imprime un texto.

        Args:
            texto (str): contenido a mostrar.
        """
        print(texto)


class SistemaInventario:
    """Coordina el menú, el inventario, el repositorio, la bitácora y las reglas.

    Es la capa de interfaz: captura las excepciones del modelo y muestra
    mensajes amigables, de modo que el programa nunca termina con traceback.
    """

    RAIZ = Path(__file__).resolve().parent.parent
    NOMBRE_TIENDA = "CARNICERÍA EL BUEN CORTE"
    ARCHIVO_VENTAS = "ventas.csv"
    ARCHIVO_BITACORA = "bitacora.log"

    def __init__(self, ruta_inventario):
        """Prepara el sistema.

        Args:
            ruta_inventario (str | Path): CSV del inventario; si es relativa
                se toma desde la raíz del proyecto. Las ventas y la bitácora
                se guardan en la misma carpeta.
        """
        ruta = Path(ruta_inventario)
        if not ruta.is_absolute():
            ruta = self.RAIZ / ruta
        self._repositorio = RepositorioCSV(ruta, ruta.parent / self.ARCHIVO_VENTAS)
        self._bitacora = Bitacora(ruta.parent / self.ARCHIVO_BITACORA)
        self._alertas = AlertaStock()
        self._reporte_inventario = ReporteInventario()
        self._consola = Consola()
        self._inventario = None
        self._ventas = []

    # ---------- utilidades internas ----------

    def _log(self, mensaje):
        """Escribe en la bitácora sin que un fallo detenga el programa."""
        try:
            self._bitacora.registrar(mensaje)
        except ArchivoInventarioError as error:
            self._consola.mostrar(f"Aviso: {error}")

    def _guardar(self):
        """Guarda el inventario en el CSV y lo anota en la bitácora."""
        self._repositorio.guardar_inventario(self._inventario)
        self._log("Inventario guardado")

    def _leer_numero(self, mensaje):
        """Pide un número al usuario (valida con Producto.a_numero)."""
        return Producto.a_numero(self._consola.leer(mensaje), "El valor ingresado")

    def _mostrar_alertas(self):
        """Muestra las alertas de stock mínimo de todo el inventario."""
        alertas = self._alertas.generar(self._inventario)
        if alertas:
            self._consola.mostrar("\n¡ALERTA DE STOCK MÍNIMO!")
            for alerta in alertas:
                self._consola.mostrar(f"- {alerta}")
        else:
            self._consola.mostrar("No hay productos en stock mínimo.")

    def _mostrar_menu(self):
        """Imprime las opciones del menú."""
        self._consola.mostrar(f"\n=== {self.NOMBRE_TIENDA} ===")
        for linea in (
            "1. Agregar producto",
            "2. Buscar producto",
            "3. Registrar venta",
            "4. Inventario ordenado por nombre",
            "5. Inventario ordenado por precio",
            "6. Reporte de ventas del día",
            "7. Alertas de stock mínimo",
            "8. Salir",
        ):
            self._consola.mostrar(linea)

    # ---------- opciones del menú ----------

    def _agregar_producto(self):
        """Pide los datos, crea el producto y lo agrega al inventario."""
        self._consola.mostrar("\n--- AGREGAR PRODUCTO ---")
        try:
            codigo = Producto.validar_codigo(self._consola.leer("Código (ej. RES011): "))
            if codigo in self._inventario:
                self._consola.mostrar("Ya existe un producto con ese código.")
                self._log(f"Alta rechazada: código duplicado {codigo}")
                return
            nombre = self._consola.leer("Nombre del producto: ")
            categoria = self._consola.leer("Categoría: ")
            precio = self._leer_numero("Precio por kilogramo (Q): ")
            stock = self._leer_numero("Stock inicial en kg: ")
            minimo = self._leer_numero("Stock mínimo en kg: ")
            producto = Producto(codigo, nombre, categoria, precio, stock, minimo)
        except InventarioError as error:
            self._log(f"Alta rechazada: {error}")
            raise
        self._inventario.agregar(producto)
        self._guardar()
        self._log(f"Producto agregado: {producto.codigo} - {producto.nombre}")
        self._consola.mostrar("Producto agregado correctamente.")

    def _buscar_producto(self):
        """Busca por código o parte del nombre y muestra los resultados."""
        consulta = self._consola.leer("Código o parte del nombre: ")
        encontrados = self._inventario.buscar(consulta)
        if encontrados:
            self._consola.mostrar(self._reporte_inventario.tabla(encontrados))
            self._log("Búsqueda realizada: " + consulta.casefold())
        else:
            self._consola.mostrar("No se encontraron productos.")
            self._log("Búsqueda sin resultados: " + consulta.casefold())

    def _registrar_venta(self):
        """Registra una venta: valida, descuenta stock y guarda."""
        self._consola.mostrar("\n--- REGISTRAR VENTA ---")
        codigo = self._consola.leer("Código del producto: ").upper()
        try:
            producto = self._inventario.obtener(codigo)
            self._consola.mostrar(
                f"{producto.nombre} - Q{producto.precio:.2f}/kg - "
                f"Disponible: {producto.stock:.2f} kg"
            )
            cantidad = producto.verificar_venta(
                self._leer_numero("Cantidad vendida en kg: ")
            )
            venta = Venta.crear(producto, cantidad)
            # Primero se guarda la venta; el stock solo cambia si se pudo guardar.
            self._repositorio.guardar_venta(venta)
            producto.descontar_stock(cantidad)
        except InventarioError as error:
            self._log(f"Venta rechazada: {error}")
            raise
        self._guardar()
        self._ventas.append(venta)
        self._log(f"Venta registrada: {venta.codigo} - {venta.cantidad_kg:.2f} kg - Q{venta.total:.2f}")
        self._consola.mostrar(f"Venta registrada. Total a cobrar: Q{venta.total:.2f}")
        alerta = self._alertas.evaluar(producto)
        if alerta is not None:
            self._consola.mostrar(f"¡Atención! {alerta}")

    def _mostrar_inventario(self, productos, titulo):
        """Muestra una tabla de productos y las categorías sin duplicados."""
        if len(self._inventario) == 0:
            self._consola.mostrar("El inventario está vacío.")
            return
        self._consola.mostrar(f"\n--- {titulo} ---")
        self._consola.mostrar(self._reporte_inventario.tabla(productos))
        categorias = ", ".join(sorted(self._inventario.categorias()))
        self._consola.mostrar(f"Categorías sin duplicados: {categorias}")

    def _reporte_ventas(self):
        """Muestra el reporte de ventas del día."""
        self._consola.mostrar(ReporteVentas(self._ventas).generar())
        self._log("Reporte de ventas del día consultado")

    # ---------- bucle principal ----------

    def ejecutar(self):
        """Carga los datos y ejecuta el menú hasta que el usuario sale.

        Nunca lanza excepciones del sistema: las captura y las muestra.
        """
        try:
            self._inventario = self._repositorio.cargar_inventario()
            self._ventas = self._repositorio.cargar_ventas()
        except InventarioError as error:
            # No se continúa: guardar un inventario vacío borraría los datos.
            self._consola.mostrar(f"Error al cargar los datos: {error}")
            self._consola.mostrar("Corrige el archivo e inicia de nuevo.")
            self._log(f"Error al cargar: {error}")
            return

        self._log("Sistema iniciado")
        self._consola.mostrar(f"Productos cargados: {len(self._inventario)}")
        self._mostrar_alertas()

        acciones = {
            "1": self._agregar_producto,
            "2": self._buscar_producto,
            "3": self._registrar_venta,
            "4": lambda: self._mostrar_inventario(
                self._inventario.ordenados_por_nombre(), "INVENTARIO ORDENADO POR NOMBRE"
            ),
            "5": lambda: self._mostrar_inventario(
                self._inventario.ordenados_por_precio(), "INVENTARIO ORDENADO POR PRECIO"
            ),
            "6": self._reporte_ventas,
            "7": self._mostrar_alertas,
        }

        while True:
            self._mostrar_menu()
            try:
                opcion = self._consola.leer("Seleccione una opción (1-8): ")
                if opcion == "8":
                    self._guardar()
                    self._log("Sistema cerrado")
                    self._consola.mostrar("Cambios guardados. ¡Hasta pronto!")
                    break
                accion = acciones.get(opcion)
                if accion is None:
                    self._consola.mostrar("Opción inválida. Escribe un número del 1 al 8.")
                else:
                    accion()
            except InventarioError as error:
                self._consola.mostrar(f"Error: {error}")
            except (EOFError, KeyboardInterrupt):
                self._consola.mostrar("\nEntrada cancelada. Cerrando el sistema.")
                try:
                    self._repositorio.guardar_inventario(self._inventario)
                except InventarioError as error:
                    self._consola.mostrar(f"Error: {error}")
                break
