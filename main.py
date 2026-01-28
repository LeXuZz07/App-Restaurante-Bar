import flet as ft
from datetime import datetime

def main(page: ft.Page):
    # --- CONFIGURACIÓN BASE ---
    page.title = "POS Restaurante Pro - SUNMI D3"
    page.theme_mode = "light"
    page.window_width = 1200
    page.window_height = 800

    # --- VARIABLES DE ESTADO ---
    cuentas = {i: [] for i in range(1, 21)}
    ventas_totales = []  
    compras_insumos = [] 
    estado = {"mesa": 0}

    MENU = [
        {"n": "Cerveza", "p": 55, "d": "BARRA", "c": "BEBIDAS"},
        {"n": "Refresco", "p": 35, "d": "BARRA", "c": "BEBIDAS"},
        {"n": "Hamburguesa", "p": 150, "d": "COCINA", "c": "COMIDA"},
        {"n": "Tacos", "p": 90, "d": "COCINA", "c": "COMIDA"},
        {"n": "Pizza", "p": 200, "d": "COCINA", "c": "COMIDA"},
        {"n": "Pastel", "p": 60, "d": "OTROS", "c": "POSTRES"},
    ]

    # --- NAVEGACIÓN ---

    def ir_a_mesas(e):
        v_pedido.visible = v_confirmacion.visible = v_ticket_final.visible = False
        v_login.visible = v_admin.visible = False
        v_mesas.visible = True
        for c in grid_mesas.controls:
            c.bgcolor = "orange" if len(cuentas[c.data]) > 0 else "blue"
        page.update()

    def ir_a_pedido(e):
        estado["mesa"] = e.control.data
        txt_titulo_mesa.value = f"MESA #{estado['mesa']}"
        mostrar_mensaje_central("¡Bienvenido!\nSelecciona una categoría para pedir.", "blue")
        refrescar_ticket()
        v_mesas.visible = False
        v_pedido.visible = True
        page.update()

    def ir_a_login(e):
        v_mesas.visible = False
        v_login.visible = True
        page.update()

    def mostrar_mensaje_central(texto, color_texto):
        grid_prods.controls.clear()
        grid_prods.controls.append(
            ft.Column([
                ft.Container(height=100),
                ft.Row([ft.Text(texto, size=22, color=color_texto, weight="bold", text_align="center")], alignment="center")
            ], horizontal_alignment="center", width=700)
        )
        page.update()

    # --- LÓGICA DE ADMINISTRACIÓN (CON FECHAS) ---

    def validar_login(e):
        if user_input.value == "admin" and pass_input.value == "1234":
            user_input.value = ""
            pass_input.value = ""
            v_login.visible = False
            v_admin.visible = True
            actualizar_resumen()
        else:
            page.snack_bar = ft.SnackBar(ft.Text("Credenciales Incorrectas"), bgcolor="red")
            page.snack_bar.open = True
        page.update()

    def registrar_compra(e):
        if input_gasto_nom.value and input_gasto_monto.value and input_gasto_cant.value:
            try:
                gasto = {
                    "n": input_gasto_nom.value,
                    "q": int(input_gasto_cant.value),
                    "p": float(input_gasto_monto.value),
                    "f": datetime.now().strftime("%Y-%m-%d %H:%M") # Fecha y hora de compra
                }
                compras_insumos.append(gasto)
                input_gasto_nom.value = ""
                input_gasto_cant.value = "1"
                input_gasto_monto.value = ""
                actualizar_resumen()
            except ValueError:
                pass
        page.update()

    def actualizar_resumen():
        col_resumen_balance.controls.clear()
        col_lista_compras.controls.clear()
        
        hoy = datetime.now().strftime("%Y-%m-%d")
        total_v = sum(v["total"] for v in ventas_totales)
        total_c = sum(c["p"] for c in compras_insumos)
        balance = total_v - total_c

        # 1. Encabezado de Balance con Fecha
        col_resumen_balance.controls.append(ft.Text(f"FECHA DE CORTE: {hoy}", size=16, weight="bold", color="grey"))
        col_resumen_balance.controls.append(ft.Text(f"INGRESOS: ${total_v}", color="green", size=20, weight="bold"))
        col_resumen_balance.controls.append(ft.Text(f"EGRESOS: ${total_c}", color="red", size=20, weight="bold"))
        col_resumen_balance.controls.append(ft.Divider())
        col_resumen_balance.controls.append(ft.Text(f"NETO: ${balance}", size=25, weight="bold", color="blue" if balance >=0 else "red"))

        # 2. Historial de Compras con Fecha
        for c in compras_insumos:
            col_lista_compras.controls.append(
                ft.Text(f"• [{c['f']}] {c['q']}x {c['n']} - ${c['p']}", size=15)
            )
        page.update()

    # --- LÓGICA DE PRODUCTOS ---

    def agregar_item(nombre, precio, destino):
        mesa_actual = cuentas[estado["mesa"]]
        encontrado = False
        for item in mesa_actual:
            if item["n"] == nombre and not item["enviado"]:
                item["q"] += 1
                encontrado = True
                break
        if not encontrado:
            mesa_actual.append({"n": nombre, "p": precio, "d": destino, "q": 1, "enviado": False})
        refrescar_ticket()

    def quitar_item(nombre):
        mesa_actual = cuentas[estado["mesa"]]
        for i, item in enumerate(mesa_actual):
            if item["n"] == nombre and not item["enviado"]:
                if item["q"] > 1: item["q"] -= 1
                else: mesa_actual.pop(i)
                break
        refrescar_ticket()

    def refrescar_ticket():
        col_ticket.controls.clear()
        total = 0
        for item in cuentas[estado["mesa"]]:
            subtotal = item["p"] * item["q"]
            icono = ft.Text(" ✔ ", color="green", weight="bold") if item["enviado"] else ft.TextButton(
                content=ft.Text(" X ", color="red", weight="bold"),
                on_click=lambda e, n=item["n"]: quitar_item(n)
            )
            col_ticket.controls.append(
                ft.Row([
                    icono,
                    ft.Text(f"{item['q']}x {item['n']}", size=16, expand=True, color="grey" if item["enviado"] else "black"),
                    ft.Text(f"${subtotal}", size=16, weight="bold")
                ])
            )
            total += subtotal
        txt_total.value = f"TOTAL: ${total}"
        page.update()

    def filtrar_menu(categoria):
        grid_prods.controls.clear()
        botones = ft.GridView(runs_count=3, spacing=10, max_extent=150)
        for p in MENU:
            if p["c"] == categoria:
                botones.controls.append(
                    ft.ElevatedButton(
                        content=ft.Text(f"{p['n']}\n${p['p']}", text_align="center"),
                        on_click=lambda e, n=p['n'], pr=p['p'], d=p['d']: agregar_item(n, pr, d),
                        height=80
                    )
                )
        grid_prods.controls.append(botones)
        page.update()

    # --- ACCIONES ---

    def enviar_comanda(e):
        mesa_actual = cuentas[estado["mesa"]]
        productos_nuevos = [i for i in mesa_actual if not i["enviado"]]
        if not productos_nuevos:
            mostrar_mensaje_central("AVISO:\nNo hay productos nuevos para enviar.", "orange")
            return

        ya_tenia_enviados = any(i["enviado"] for i in mesa_actual)
        if not ya_tenia_enviados:
            print(f"\n**************************************************\n [!] ESTADO: MESA {estado['mesa']} OCUPADA\n [!] APERTURA: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n**************************************************")

        print(f"[*] ENVIANDO COMANDA MESA {estado['mesa']}")
        for zona in ["BARRA", "COCINA", "OTROS"]:
            items = [f"{i['q']}x {i['n']}" for i in productos_nuevos if i["d"] == zona]
            if items: print(f"    -> {zona}: {', '.join(items)}")
        
        for i in mesa_actual: i["enviado"] = True
        refrescar_ticket()
        mostrar_mensaje_central("¡ORDEN ENVIADA!\nLos productos han sido bloqueados.", "green")

    def abrir_confirmacion(e):
        mesa_actual = cuentas[estado["mesa"]]
        if not mesa_actual:
            mostrar_mensaje_central("ERROR:\nLa cuenta está vacía.", "red")
            return
        if any(not i["enviado"] for i in mesa_actual):
            mostrar_mensaje_central("ADVERTENCIA:\nHay productos sin enviar a cocina.", "red")
            return
        v_confirmacion.visible = True
        page.update()

    def mostrar_ticket_final(e):
        v_confirmacion.visible = False
        v_ticket_final.visible = True
        col_resumen_final.controls.clear()
        total = 0
        for item in cuentas[estado["mesa"]]:
            sub = item['p'] * item['q']
            col_resumen_final.controls.append(ft.Text(f"{item['q']} x {item['n']} .... ${sub}", size=18))
            total += sub
        txt_total_final.value = f"TOTAL FINAL: ${total}"
        page.update()

    def finalizar_y_limpiar(e):
        total_venta = sum(i["p"] * i["q"] for i in cuentas[estado["mesa"]])
        # Guardamos la venta con fecha y hora completa
        ventas_totales.append({
            "total": total_venta, 
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M")
        })

        print(f"\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n REPORTE DE CIERRE DE CUENTA\n MESA: {estado['mesa']} | TOTAL: ${total_venta}\n FECHA: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n ESTADO: LIBERADA\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n")
        
        cuentas[estado["mesa"]] = [] 
        ir_a_mesas(None)

    # --- INTERFACES ---

    v_login = ft.Container(
        content=ft.Column([
            ft.Text("ACCESO ADMIN", size=30, weight="bold"),
            user_input := ft.TextField(label="Usuario", width=300),
            pass_input := ft.TextField(label="Contraseña", password=True, width=300),
            ft.ElevatedButton("ENTRAR", on_click=validar_login, bgcolor="blue", color="white", width=300),
            ft.TextButton("VOLVER AL SALÓN", on_click=ir_a_mesas)
        ], alignment="center", horizontal_alignment="center"),
        visible=False, expand=True
    )

    col_resumen_balance = ft.Column()
    col_lista_compras = ft.Column(scroll="always", expand=True)
    v_admin = ft.Container(
        content=ft.Column([
            ft.Row([ft.Text("PANEL ADMINISTRATIVO", size=30, weight="bold"), ft.TextButton("CERRAR", on_click=ir_a_mesas)], alignment="spaceBetween"),
            ft.Divider(),
            ft.Row([
                ft.Column([
                    ft.Text("RESUMEN DE GANANCIAS", size=22, weight="bold"),
                    col_resumen_balance,
                    ft.Divider(),
                    ft.Text("HISTORIAL DE INVENTARIO", size=18, weight="bold"),
                    col_lista_compras
                ], expand=1),
                ft.VerticalDivider(),
                ft.Column([
                    ft.Text("REGISTRAR COMPRA", size=22, weight="bold"),
                    ft.Row([
                        input_gasto_nom := ft.TextField(label="Producto", expand=True),
                        input_gasto_cant := ft.TextField(label="Cant.", width=80, value="1"),
                        input_gasto_monto := ft.TextField(label="Costo Total $", width=140)
                    ]),
                    ft.ElevatedButton("GUARDAR EN HISTORIAL", on_click=registrar_compra, bgcolor="red", color="white", width=400)
                ], expand=1)
            ], expand=True)
        ]),
        visible=False, expand=True, padding=30
    )

    grid_mesas = ft.GridView(expand=True, runs_count=5, spacing=15)
    for i in range(1, 21):
        grid_mesas.controls.append(
            ft.Container(content=ft.Text(f"{i}", color="white", size=22, weight="bold"),
                        bgcolor="blue", border_radius=10, padding=20, on_click=ir_a_pedido, data=i))
    v_mesas = ft.Column([
        ft.Row([ft.Text("SISTEMA POS - SALÓN", size=30, weight="bold", expand=True), ft.TextButton("ADMIN", on_click=ir_a_login)]), 
        grid_mesas
    ], expand=True)

    txt_titulo_mesa = ft.Text("", size=25, weight="bold")
    col_ticket = ft.Column(scroll="always", expand=True)
    txt_total = ft.Text("TOTAL: $0", size=35, weight="bold", color="green")
    grid_prods = ft.Column(expand=True) 
    v_pedido = ft.Row([
        ft.Column([ft.TextButton("<- VOLVER", on_click=ir_a_mesas), 
                   ft.Row([
                       ft.ElevatedButton("BEBIDAS", on_click=lambda _: filtrar_menu("BEBIDAS")),
                       ft.ElevatedButton("COMIDA", on_click=lambda _: filtrar_menu("COMIDA")),
                       ft.ElevatedButton("POSTRES", on_click=lambda _: filtrar_menu("POSTRES")),
                   ]), grid_prods], expand=3),
        ft.Container(
            content=ft.Column([
                txt_titulo_mesa, ft.Divider(), col_ticket, ft.Divider(), txt_total,
                ft.ElevatedButton("ENVIAR COMANDA", bgcolor="orange", color="white", height=60, on_click=enviar_comanda, width=400),
                ft.Container(height=5),
                ft.ElevatedButton("PAGAR CUENTA", bgcolor="green", color="white", height=60, on_click=abrir_confirmacion, width=400),
            ]),
            expand=2, bgcolor="white", padding=20, border_radius=15
        )
    ], expand=True, visible=False)

    v_confirmacion = ft.Container(
        content=ft.Column([
            ft.Text("¿CONFIRMAR PAGO?", size=25, weight="bold"),
            ft.Row([
                ft.ElevatedButton("SÍ, PAGAR", bgcolor="green", color="white", on_click=mostrar_ticket_final, width=180, height=60),
                ft.ElevatedButton("NO", bgcolor="red", color="white", on_click=lambda _: [setattr(v_confirmacion, 'visible', False), page.update()], width=180, height=60),
            ], alignment="center")
        ], alignment="center"),
        bgcolor="rgba(255,255,255,0.9)", visible=False, expand=True
    )

    col_resumen_final = ft.Column(scroll="always", expand=True)
    txt_total_final = ft.Text("", size=40, weight="bold", color="green")
    v_ticket_final = ft.Container(
        content=ft.Column([
            ft.Text("RESUMEN DE VENTA", size=30, weight="bold"),
            ft.Divider(), col_resumen_final, ft.Divider(), txt_total_final,
            ft.ElevatedButton("FINALIZAR", bgcolor="blue", color="white", width=400, height=80, on_click=finalizar_y_limpiar)
        ], horizontal_alignment="center"),
        bgcolor="white", visible=False, expand=True, padding=50
    )

    page.add(ft.Stack([v_mesas, v_pedido, v_confirmacion, v_ticket_final, v_login, v_admin], expand=True))

ft.app(target=main)