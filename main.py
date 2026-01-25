import flet as ft

def main(page: ft.Page):
    # --- CONFIGURACIÓN DE PÁGINA ---
    page.title = "Sistema Restaurante - SUNMI D3 Pro"
    page.theme_mode = "light"
    page.padding = 10
    
    # Proporciones para tu pantalla grande
    page.window_width = 1200
    page.window_height = 800

    # Variables de estado
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

    def refrescar_ticket():
        col_ticket.controls.clear()
        total = 0
        for item in cuentas[estado["mesa"]]:
            col_ticket.controls.append(
                ft.Text(f"{item['n']} .... ${item['p']}", size=16)
            )
            total += item["p"]
        txt_total.value = f"TOTAL: ${total}"
        page.update()

    def procesar_impresion(e):
        # Simulación de las 3 impresoras en terminal
        print(f"\n--- GENERANDO TICKETS MESA {estado['mesa']} ---")
        for zona in ["BARRA", "COCINA", "OTROS"]:
            items = [i["n"] for i in cuentas[estado["mesa"]] if i["d"] == zona]
            if items:
                print(f"IMPRIMIENDO EN {zona}: {items}")
        
        cuentas[estado["mesa"]] = [] # Limpiar mesa
        ir_a_mesas(None)

    # --- DISEÑO VISTA 1: 20 MESAS ---
    grid_mesas = ft.GridView(expand=True, runs_count=5, spacing=15)
    for i in range(1, 21):
        grid_mesas.controls.append(
            ft.Container(
                content=ft.Text(f"{i}", color="white", size=22, weight="bold"),
                bgcolor="blue",
                border_radius=10,
                # Usamos una forma de alineación que no use ft.alignment
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

    # Lista de productos
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
        # Lado izquierdo: Selección
        ft.Column([
            ft.TextButton(content=ft.Text("<- VOLVER"), on_click=ir_a_mesas),
            grid_prods
        ], expand=3),
        # Lado derecho: Ticket
        ft.Container(
            content=ft.Column([
                txt_titulo_mesa,
                ft.Divider(),
                col_ticket,
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

    # --- CARGA ---
    page.add(ft.Stack([v_mesas, v_pedido], expand=True))

ft.app(target=main)