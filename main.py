import flet as ft

def main(page: ft.Page):
    # --- CONFIGURACIÓN BASE ---
    page.title = "POS Restaurante - SUNMI D3 Pro"
    page.theme_mode = "light"
    page.padding = 10
    
    # Proporciones para pantalla de 15.6"
    page.window_width = 1200
    page.window_height = 800

    # Variables de estado (20 mesas)
    cuentas = {i: [] for i in range(1, 21)}
    estado = {"mesa": 0}

    # --- LÓGICA DE NEGOCIO ---

    def ir_a_pedido(e):
        estado["mesa"] = e.control.data
        txt_titulo_mesa.value = f"CUENTA MESA #{estado['mesa']}"
        refrescar_ticket()
        v_mesas.visible = False
        v_pedido.visible = True
        page.update()

    def ir_a_mesas(e):
        v_pedido.visible = False
        v_mesas.visible = True
        page.update()

    def agregar_item(nombre, precio, destino):
        cuentas[estado["mesa"]].append({"n": nombre, "p": precio, "d": destino})
        refrescar_ticket()

    # Función para quitar un producto por su posición
    def quitar_item(indice):
        cuentas[estado["mesa"]].pop(indice)
        refrescar_ticket()

    def refrescar_ticket():
        col_ticket.controls.clear()
        total = 0
        # Recorremos los productos de la mesa actual
        for idx, item in enumerate(cuentas[estado["mesa"]]):
            col_ticket.controls.append(
                ft.Row([
                    # Botón de borrar usando Texto para evitar errores de íconos
                    ft.TextButton(
                        content=ft.Text(" X ", color="red", weight="bold"),
                        on_click=lambda e, i=idx: quitar_item(i)
                    ),
                    ft.Text(f"{item['n']} .... ${item['p']}", size=16, expand=True)
                ])
            )
            total += item["p"]
        txt_total.value = f"TOTAL: ${total}"
        page.update()

    def procesar_impresion(e):
        # Simulación de envío a 3 impresoras (Barra, Cocina, Otros)
        print(f"\n--- GENERANDO TICKETS MESA {estado['mesa']} ---")
        for zona in ["BARRA", "COCINA", "OTROS"]:
            items = [i["n"] for i in cuentas[estado["mesa"]] if i["d"] == zona]
            if items:
                print(f"IMPRIMIENDO EN {zona}: {items}")
        
        cuentas[estado["mesa"]] = [] # Limpiar mesa al cerrar
        ir_a_mesas(None)

    # --- DISEÑO VISTA 1: 20 MESAS ---
    grid_mesas = ft.GridView(expand=True, runs_count=5, spacing=15)
    for i in range(1, 21):
        grid_mesas.controls.append(
            ft.Container(
                content=ft.Text(f"{i}", color="white", size=22, weight="bold"),
                bgcolor="blue",
                border_radius=10,
                padding=20,
                on_click=ir_a_pedido,
                data=i
            )
        )

    v_mesas = ft.Column([
        ft.Text("SALÓN DE MESAS", size=30, weight="bold"),
        grid_mesas
    ], expand=True, visible=True)

    # --- DISEÑO VISTA 2: COMANDERO ---
    txt_titulo_mesa = ft.Text("", size=25, weight="bold")
    col_ticket = ft.Column(scroll="always", expand=True)
    txt_total = ft.Text("TOTAL: $0", size=35, weight="bold", color="green")

    MENU = [
        {"n": "Cerveza", "p": 55, "d": "BARRA"},
        {"n": "Refresco", "p": 35, "d": "BARRA"},
        {"n": "Hamburgesa", "p": 150, "d": "COCINA"},
        {"n": "Tacos", "p": 90, "d": "COCINA"},
        {"n": "Pizza", "p": 200, "d": "COCINA"},
    ]

    grid_prods = ft.GridView(expand=True, runs_count=2, max_extent=180)
    for p in MENU:
        grid_prods.controls.append(
            ft.ElevatedButton(
                content=ft.Text(f"{p['n']}\n${p['p']}", text_align="center"),
                on_click=lambda e, n=p['n'], pr=p['p'], d=p['d']: agregar_item(n, pr, d),
                height=80
            )
        )

    v_pedido = ft.Row([
        # Lado izquierdo: Selección de productos
        ft.Column([
            ft.TextButton(content=ft.Text("<- VOLVER"), on_click=ir_a_mesas),
            grid_productos_grid := grid_prods
        ], expand=3),
        # Lado derecho: Resumen de la cuenta (Ticket)
        ft.Container(
            content=ft.Column([
                txt_titulo_mesa,
                ft.Divider(),
                col_ticket, # Aquí se listan productos con su botón "X"
                ft.Divider(),
                txt_total,
                ft.ElevatedButton(
                    content=ft.Text("IMPRIMIR Y CERRAR", size=20),
                    bgcolor="green",
                    color="white",
                    height=70,
                    on_click=procesar_impresion
                )
            ]),
            expand=2, bgcolor="white", padding=20, border_radius=15
        )
    ], expand=True, visible=False)

    page.add(ft.Stack([v_mesas, v_pedido], expand=True))

ft.app(target=main)