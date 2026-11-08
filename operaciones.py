import csv
import math
import os
import re
from datetime import datetime

CARPETA_DATOS = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "datos"
)
ARCHIVO_PRODUCTOS = os.path.join(CARPETA_DATOS, "productos.csv")
ARCHIVO_VENTAS = os.path.join(CARPETA_DATOS, "ventas.csv")
ARCHIVO_BITACORA = os.path.join(CARPETA_DATOS, "bitacora.log")

CAMPOS_PRODUCTOS = [
    "codigo", "nombre", "categoria",
    "precio", "stock", "stock_minimo"
]

CAMPOS_VENTAS = [
    "fecha_hora", "codigo", "nombre",
    "cantidad_kg", "precio_kg", "total"
]


def asegurar_archivos():
    """Crea los archivos CSV con encabezados si no existen."""
    os.makedirs(CARPETA_DATOS, exist_ok=True)

    if not os.path.exists(ARCHIVO_PRODUCTOS):
        with open(
            ARCHIVO_PRODUCTOS, "w", newline="", encoding="utf-8"
        ) as archivo:
            csv.DictWriter(
                archivo, fieldnames=CAMPOS_PRODUCTOS
            ).writeheader()

    if not os.path.exists(ARCHIVO_VENTAS):
        with open(
            ARCHIVO_VENTAS, "w", newline="", encoding="utf-8"
        ) as archivo:
            csv.DictWriter(
                archivo, fieldnames=CAMPOS_VENTAS
            ).writeheader()


def normalizar(texto):
    """Elimina espacios sobrantes de una cadena."""
    return " ".join(texto.strip().split())


def validar_codigo(codigo):
    """Comprueba que el código tenga tres letras y tres números."""
    return bool(
        re.fullmatch(r"[A-Z]{3}[0-9]{3}", codigo.strip().upper())
    )


def registrar_bitacora(mensaje):
    """Agrega una operación con fecha y hora al archivo de bitácora."""
    os.makedirs(CARPETA_DATOS, exist_ok=True)

    with open(ARCHIVO_BITACORA, "a", encoding="utf-8") as archivo:
        fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        archivo.write(f"{fecha_hora} | {mensaje}\n")


def cargar_inventario():
    """Carga los productos del CSV y devuelve una lista de diccionarios."""
    asegurar_archivos()
    inventario = []

    try:
        with open(
            ARCHIVO_PRODUCTOS, "r", newline="", encoding="utf-8"
        ) as archivo:
            for fila in csv.DictReader(archivo):
                if fila.get("codigo"):
                    inventario.append({
                        "codigo": fila["codigo"],
                        "nombre": fila["nombre"],
                        "categoria": fila["categoria"],
                        "precio": float(fila["precio"]),
                        "stock": float(fila["stock"]),
                        "stock_minimo": float(fila["stock_minimo"]),
                    })

    except (OSError, ValueError, KeyError, csv.Error) as error:
        print("Error al cargar el inventario:", error)

    return inventario


def guardar_inventario(inventario):
    """Guarda el inventario de forma segura: escribe en un archivo
    temporal y luego lo reemplaza, para no perder datos si algo falla."""
    asegurar_archivos()
    temporal = ARCHIVO_PRODUCTOS + ".tmp"

    with open(temporal, "w", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=CAMPOS_PRODUCTOS)
        escritor.writeheader()

        for producto in inventario:
            escritor.writerow({
                "codigo": producto["codigo"],
                "nombre": producto["nombre"],
                "categoria": producto["categoria"],
                "precio": f'{producto["precio"]:.2f}',
                "stock": f'{producto["stock"]:.2f}',
                "stock_minimo": f'{producto["stock_minimo"]:.2f}'
            })

    os.replace(temporal, ARCHIVO_PRODUCTOS)
    registrar_bitacora("Inventario guardado")


def cargar_ventas():
    """Carga las ventas del CSV y devuelve una lista de tuplas."""
    asegurar_archivos()
    ventas = []

    try:
        with open(
            ARCHIVO_VENTAS, "r", newline="", encoding="utf-8"
        ) as archivo:
            for fila in csv.DictReader(archivo):
                if fila.get("codigo"):
                    ventas.append((
                        fila["fecha_hora"],
                        fila["codigo"],
                        fila["nombre"],
                        float(fila["cantidad_kg"]),
                        float(fila["precio_kg"]),
                        float(fila["total"])
                    ))

    except (OSError, ValueError, KeyError, csv.Error) as error:
        print("Error al cargar las ventas:", error)

    return ventas


def guardar_venta(venta):
    """Agrega una venta (tupla) al final del archivo de ventas."""
    asegurar_archivos()

    with open(
        ARCHIVO_VENTAS, "a", newline="", encoding="utf-8"
    ) as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=CAMPOS_VENTAS)
        escritor.writerow({
            "fecha_hora": venta[0],
            "codigo": venta[1],
            "nombre": venta[2],
            "cantidad_kg": f"{venta[3]:.2f}",
            "precio_kg": f"{venta[4]:.2f}",
            "total": f"{venta[5]:.2f}"
        })


def agregar_producto(inventario):
    """Solicita, valida y agrega un nuevo producto al inventario."""
    print("\n--- AGREGAR PRODUCTO ---")

    codigo = input("Código (ej. RES011): ").strip().upper()

    if not validar_codigo(codigo):
        print("Código inválido. Usa tres letras y tres números.")
        registrar_bitacora("Alta rechazada: código inválido")
        return

    if any(p["codigo"] == codigo for p in inventario):
        print("Ya existe un producto con ese código.")
        return

    nombre = normalizar(input("Nombre del producto: "))
    categoria = normalizar(input("Categoría: ")).title()

    try:
        precio = float(input("Precio por kilogramo (Q): "))
        stock = float(input("Stock inicial en kg: "))
        minimo = float(input("Stock mínimo en kg: "))

    except ValueError:
        print("Error: debes ingresar cantidades numéricas.")
        registrar_bitacora("Alta rechazada: datos no numéricos")
        return

    if not all(math.isfinite(x) for x in (precio, stock, minimo)):
        print("Error: las cantidades deben ser números válidos.")
        registrar_bitacora("Alta rechazada: valores no finitos")
        return

    if not nombre or not categoria or precio <= 0 or stock < 0 or minimo < 0:
        print("Datos inválidos. Revisa nombre, categoría, precio y existencias.")
        registrar_bitacora("Alta rechazada: datos inválidos")
        return

    inventario.append({
        "codigo": codigo,
        "nombre": nombre,
        "categoria": categoria,
        "precio": precio,
        "stock": stock,
        "stock_minimo": minimo
    })

    registrar_bitacora(f"Producto agregado: {codigo} - {nombre}")
    print("Producto agregado correctamente.")


def imprimir_productos(productos):
    """Muestra productos en columnas alineadas."""
    print(
        f'{"CÓDIGO":<10} {"PRODUCTO":<24} '
        f'{"CATEGORÍA":<14} {"PRECIO/KG":>12} {"STOCK KG":>10}'
    )
    print("-" * 74)

    for p in productos:
        print(
            f'{p["codigo"]:<10} '
            f'{p["nombre"]:<24.24} '
            f'{p["categoria"]:<14.14} '
            f'Q{p["precio"]:>10.2f} '
            f'{p["stock"]:>10.2f}'
        )


def buscar_productos(inventario):
    """Busca por código o coincidencia parcial del nombre."""
    consulta = normalizar(
        input("Código o parte del nombre: ")
    ).casefold()

    encontrados = [
        p for p in inventario
        if consulta in p["codigo"].casefold()
        or consulta in p["nombre"].casefold()
    ]

    if encontrados:
        imprimir_productos(encontrados)
        registrar_bitacora("Búsqueda realizada: " + consulta)
    else:
        print("No se encontraron productos.")
        registrar_bitacora("Búsqueda sin resultados: " + consulta)


def registrar_venta(inventario, ventas):
    """Registra una venta, descuenta el stock y la guarda en el CSV."""
    print("\n--- REGISTRAR VENTA ---")

    codigo = input("Código del producto: ").strip().upper()
    producto = next(
        (p for p in inventario if p["codigo"] == codigo), None
    )

    if producto is None:
        print("No existe un producto con ese código.")
        registrar_bitacora("Venta rechazada: código inexistente " + codigo)
        return

    print(
        f'{producto["nombre"]} - Q{producto["precio"]:.2f}/kg - '
        f'Disponible: {producto["stock"]:.2f} kg'
    )

    try:
        cantidad = float(input("Cantidad vendida en kg: "))
    except ValueError:
        print("Error: debes ingresar una cantidad numérica.")
        registrar_bitacora("Venta rechazada: cantidad no numérica")
        return

    if not math.isfinite(cantidad) or cantidad <= 0:
        print("La cantidad debe ser mayor que cero.")
        registrar_bitacora("Venta rechazada: cantidad inválida")
        return

    if cantidad > producto["stock"]:
        print("Stock insuficiente para esta venta.")
        registrar_bitacora(
            f"Venta rechazada: stock insuficiente de {codigo}"
        )
        return

    total = round(cantidad * producto["precio"], 2)
    fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    venta = (
        fecha_hora, producto["codigo"], producto["nombre"],
        cantidad, producto["precio"], total
    )

    # Primero se guarda la venta; el stock solo cambia si se pudo guardar.
    guardar_venta(venta)
    producto["stock"] = round(producto["stock"] - cantidad, 2)
    ventas.append(venta)

    registrar_bitacora(
        f"Venta registrada: {codigo} - {cantidad:.2f} kg - Q{total:.2f}"
    )
    print(f"Venta registrada. Total a cobrar: Q{total:.2f}")

    if producto["stock"] <= producto["stock_minimo"]:
        print(
            f'¡Atención! {producto["nombre"]} quedó en '
            f'{producto["stock"]:.2f} kg (mínimo '
            f'{producto["stock_minimo"]:.2f} kg).'
        )


def mostrar_inventario(inventario, criterio="nombre"):
    """Muestra el inventario ordenado por nombre o por precio."""
    if not inventario:
        print("El inventario está vacío.")
        return

    if criterio == "precio":
        ordenados = sorted(inventario, key=lambda p: p["precio"])
        print("\n--- INVENTARIO ORDENADO POR PRECIO ---")
    else:
        ordenados = sorted(
            inventario, key=lambda p: p["nombre"].casefold()
        )
        print("\n--- INVENTARIO ORDENADO POR NOMBRE ---")

    imprimir_productos(ordenados)

    categorias = {p["categoria"] for p in inventario}
    print("Categorías sin duplicados:", ", ".join(sorted(categorias)))


def reporte_ventas_dia(ventas):
    """Muestra las ventas de hoy con sus totales."""
    hoy = datetime.now().strftime("%Y-%m-%d")
    del_dia = [v for v in ventas if v[0].startswith(hoy)]

    print(f"\n--- VENTAS DEL DÍA ({hoy}) ---")

    if not del_dia:
        print("No hay ventas registradas hoy.")
        return

    print(
        f'{"HORA":<10} {"CÓDIGO":<8} {"PRODUCTO":<24} '
        f'{"KG":>8} {"PRECIO/KG":>10} {"TOTAL":>11}'
    )
    print("-" * 75)

    for fecha_hora, codigo, nombre, kg, precio, total in del_dia:
        print(
            f'{fecha_hora[11:]:<10} {codigo:<8} {nombre:<24.24} '
            f'{kg:>8.2f} Q{precio:>9.2f} Q{total:>10.2f}'
        )

    total_kg = sum(v[3] for v in del_dia)
    total_q = sum(v[5] for v in del_dia)
    print("-" * 75)
    print(f"Ventas: {len(del_dia)} | Total vendido: {total_kg:.2f} kg | Q{total_q:.2f}")

    registrar_bitacora("Reporte de ventas del día consultado")


def alertar_stock_minimo(inventario):
    """Muestra los productos que llegaron al stock mínimo o están por debajo."""
    bajos = [p for p in inventario if p["stock"] <= p["stock_minimo"]]

    if bajos:
        print("\n¡ALERTA DE STOCK MÍNIMO!")

        for p in bajos:
            print(
                f'- {p["nombre"]}: {p["stock"]:.2f} kg '
                f'(mínimo {p["stock_minimo"]:.2f} kg)'
            )
    else:
        print("No hay productos en stock mínimo.")