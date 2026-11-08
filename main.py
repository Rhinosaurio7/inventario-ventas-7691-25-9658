import csv

from operaciones import (
    cargar_inventario,
    guardar_inventario,
    cargar_ventas,
    registrar_bitacora,
    agregar_producto,
    buscar_productos,
    registrar_venta,
    mostrar_inventario,
    reporte_ventas_dia,
    alertar_stock_minimo
)


def mostrar_menu():
    """Muestra las opciones principales del sistema."""
    print("\n=== CARNICERÍA EL BUEN CORTE ===")
    print("1. Agregar producto")
    print("2. Buscar producto")
    print("3. Registrar venta")
    print("4. Inventario ordenado por nombre")
    print("5. Inventario ordenado por precio")
    print("6. Reporte de ventas del día")
    print("7. Alertas de stock mínimo")
    print("8. Salir")


def ejecutar_sistema():
    """Carga los datos y coordina el menú principal."""
    inventario = cargar_inventario()
    ventas = cargar_ventas()

    registrar_bitacora("Sistema iniciado")
    print(f"Productos cargados: {len(inventario)}")

    alertar_stock_minimo(inventario)

    while True:
        mostrar_menu()
        opcion = input("Seleccione una opción (1-8): ").strip()

        try:
            if opcion == "1":
                agregar_producto(inventario)
                guardar_inventario(inventario)

            elif opcion == "2":
                buscar_productos(inventario)

            elif opcion == "3":
                registrar_venta(inventario, ventas)
                guardar_inventario(inventario)

            elif opcion == "4":
                mostrar_inventario(inventario, "nombre")

            elif opcion == "5":
                mostrar_inventario(inventario, "precio")

            elif opcion == "6":
                reporte_ventas_dia(ventas)

            elif opcion == "7":
                alertar_stock_minimo(inventario)

            elif opcion == "8":
                guardar_inventario(inventario)
                registrar_bitacora("Sistema cerrado")
                print("Cambios guardados. ¡Hasta pronto!")
                break

            else:
                print("Opción inválida. Escribe un número del 1 al 8.")

        except (ValueError, OSError, csv.Error) as error:
            print("Error controlado:", error)
            registrar_bitacora("Error controlado: " + str(error))


if __name__ == "__main__":
    ejecutar_sistema()