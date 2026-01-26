import flet as ft

def main(page: ft.Page):
    # --- CONFIGURACIÓN BASE ---
    page.title = "POS Restaurante Pro - SUNMI D3"
    page.theme_mode = "light"
    page.padding = 10
    page.window_width = 1200
    page.window_height = 800

    # Variables de estado
    cuentas = {i: [] for i in range(1, 21)}
    estado = {"mesa": 0}

    # Menú extendido con categorías
    MENU = [
        {"n": "Cerveza", "p": 55, "d": "BARRA", "c": "Bebidas"},
        {"n": "Refresco", "p": 35, "d": "BARRA", "c": "Bebidas"},
        {"n": "Vino", "p": 120, "d": "BARRA", "c": "Bebidas"},
        {"n": "Hamburgesa", "p": 150, "d": "COCINA", "c": "Comida"},
        {"n": "Tacos", "p": 90, "d": "COCINA", "c": "Comida"},
        {"n": "Pizza", "p": 200, "d": "COCINA", "c": "Comida"},
        {"n": "Pastel", "p": 65, "d": "OTROS", "c": "Postres"},
        {"n": "Helado", "p": 45, "d": "OTROS", "c": "Postres"},
    ]

    # --- LÓGICA DE NEGOCIO ---

    def seleccionar_mesa(e):
        estado["mesa"] = e.control.data
        txt_titulo_mesa.value = f"CUENTA MESA #{estado['mesa']}"
        refrescar_ticket()
        v_mesas.visible = False
        v_pedido.visible = True
        page.update()

    def ir_a_mesas(e):
        v_pedido.visible = False
        v_mesas.visible = True
        # Refrescar colores del mapa
        for container in grid_mesas.controls:
            container.bgcolor = "orange" if len(cuentas[container.data]) > 0 else "blue"
        page.update()

    def agregar_item(nombre, precio, destino):
        # Lógica de Cantidades: Buscar si el producto ya está en la cuenta
        mesa_actual = cuentas[estado["mesa"]]
        encontrado = False
        for item in mesa_actual:
            if item["n"] == nombre:
                item["q"] += 1 # Aumentar cantidad
                encontrado = True
                break
        
        if not encontrado:
            # Agregar nuevo con cantidad inicial 1
            mesa_actual.append({"n": nombre, "p": precio, "d": destino, "q": 1})
        
        refrescar_ticket()

    def quitar_item(nombre):
        mesa_actual = cuentas[estado["mesa"]]
        for i, item in enumerate(mesa_actual):
            if item["n"] == nombre:
                if item["q"] > 1:
                    item["q"] -= 1 # Restar uno
                else:
                    mesa_actual.pop(i) # Eliminar si solo queda uno
                break
        refrescar_ticket()

    def refrescar_ticket():
        col_ticket.controls.clear()
        total_cuenta = 0
        for item in cuentas[estado["mesa"]]:
            subtotal = item["p"] * item["q"]
            col_ticket.controls.append(
                ft.Row([
                    ft.TextButton(
                        content=ft.Text(" X ", color="red", weight="bold"),
                        on_click=lambda e, n=item["n"]: quitar_item(n)
                    ),
                    ft.Text(f"{item['q']}x {item['n']}", size=16, expand=True),
                    ft.Text(f"${subtotal}", size=16, weight="bold")
                ])
            )
            total_cuenta += subtotal
        txt_total.value = f"TOTAL: ${total_cuenta}"
        page.update()

    def filtrar_menu(categoria):
        grid_prods.controls.clear()
        for p in MENU:
            if categoria == "TODOS" or p["c"] == categoria:
                grid_prods.controls.append(
                    ft.ElevatedButton(
                        content=ft.Text(f"{p['n']}\n${p['p']}", text_align="center"),
                        on_click=lambda e, n=p['n'], pr=p['p'], d=p['d']: agregar_item(n, pr, d),
                        height=80
                    )
                )
        page.update()

    # --- DISEÑO VISTA 1: MESAS ---
    grid_mesas = ft.GridView(expand=True, runs_count=5, spacing=15)
    for i in range(1, 21):
        grid_mesas.controls.append(
            ft.Container(
                content=ft.Text(f"{i}", color="white", size=22, weight="bold"),
                bgcolor="blue",
                border_radius=10,
                padding=20,
                on_click=seleccionar_mesa,
                data=i
            )
        )
    v_mesas = ft.Column([ft.Text("SALÓN", size=30, weight="bold"), grid_mesas], expand=True)

    # --- DISEÑO VISTA 2: COMANDERO ---
    txt_titulo_mesa = ft.Text("", size=25, weight="bold")
    col_ticket = ft.Column(scroll="always", expand=True)
    txt_total = ft.Text("TOTAL: $0", size=35, weight="bold", color="green")
    grid_prods = ft.GridView(expand=True, runs_count=3, max_extent=150, spacing=10)

    # Botones de Categorías
    btn_categorias = ft.Row([
        ft.ElevatedButton(content=ft.Text("TODOS"), on_click=lambda _: filtrar_menu("TODOS")),
        ft.ElevatedButton(content=ft.Text("BEBIDAS"), on_click=lambda _: filtrar_menu("Bebidas")),
        ft.ElevatedButton(content=ft.Text("COMIDA"), on_click=lambda _: filtrar_menu("Comida")),
        ft.ElevatedButton(content=ft.Text("POSTRES"), on_click=lambda _: filtrar_menu("Postres")),
    ], scroll="always")

    v_pedido = ft.Row([
        ft.Column([
            ft.TextButton(content=ft.Text("<- VOLVER"), on_click=ir_a_mesas),
            btn_categorias, # Fila de categorías
            grid_prods      # Cuadrícula de productos filtrados
        ], expand=3),
        ft.Container(
            content=ft.Column([
                txt_titulo_mesa,
                ft.Divider(),
                col_ticket,
                ft.Divider(),
                txt_total,
                ft.ElevatedButton(
                    content=ft.Text("IMPRIMIR", size=20),
                    bgcolor="green", color="white", height=70,
                    on_click=lambda _: [print("Enviando..."), ir_a_mesas(None)]
                )
            ]),
            expand=2, bgcolor="white", padding=20, border_radius=15
        )
    ], expand=True, visible=False)

    # Inicializar menú con todos los productos
    filtrar_menu("TODOS")

    page.add(ft.Stack([v_mesas, v_pedido], expand=True))

ft.app(target=main)