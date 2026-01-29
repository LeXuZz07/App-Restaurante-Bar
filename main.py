import flet as ft
import sqlite3
from datetime import datetime

# --- CAPA DE DATOS (SQLite) ---
def init_db():
    conn = sqlite3.connect("pos_restaurante.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mesa_id INTEGER,
            detalle TEXT,
            total REAL,
            fecha TEXT,
            cerrada INTEGER DEFAULT 0
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS items_activos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mesa_id INTEGER,
            nombre TEXT,
            precio REAL,
            cantidad INTEGER,
            destino TEXT,
            enviado INTEGER
        )
    """)
    conn.commit()
    conn.close()

# --- FUNCIONES DE PERSISTENCIA ---
def db_guardar_item_activo(mesa, item):
    conn = sqlite3.connect("pos_restaurante.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, cantidad FROM items_activos WHERE mesa_id=? AND nombre=? AND enviado=0", (mesa, item['n']))
    res = cursor.fetchone()
    if res:
        cursor.execute("UPDATE items_activos SET cantidad=? WHERE id=?", (item['q'], res[0]))
    else:
        cursor.execute("INSERT INTO items_activos (mesa_id, nombre, precio, cantidad, destino, enviado) VALUES (?,?,?,?,?,?)",
                       (mesa, item['n'], item['p'], item['q'], item['d'], 0))
    conn.commit()
    conn.close()

def db_remover_item_activo(mesa, nombre):
    conn = sqlite3.connect("pos_restaurante.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, cantidad FROM items_activos WHERE mesa_id=? AND nombre=? AND enviado=0", (mesa, nombre))
    res = cursor.fetchone()
    if res:
        if res[1] > 1:
            cursor.execute("UPDATE items_activos SET cantidad=? WHERE id=?", (res[1]-1, res[0]))
        else:
            cursor.execute("DELETE FROM items_activos WHERE id=?", (res[0],))
    conn.commit()
    conn.close()

def db_marcar_enviados(mesa):
    conn = sqlite3.connect("pos_restaurante.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE items_activos SET enviado=1 WHERE mesa_id=?", (mesa,))
    conn.commit()
    conn.close()

def db_limpiar_mesa(mesa):
    conn = sqlite3.connect("pos_restaurante.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM items_activos WHERE mesa_id=?", (mesa,))
    conn.commit()
    conn.close()

def db_registrar_venta_final(mesa_id, detalle, total):
    conn = sqlite3.connect("pos_restaurante.db")
    cursor = conn.cursor()
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M")
    cursor.execute("INSERT INTO ventas (mesa_id, detalle, total, fecha, cerrada) VALUES (?, ?, ?, ?, 0)", 
                   (mesa_id, detalle, total, ahora))
    conn.commit()
    conn.close()

def db_ejecutar_cierre_caja():
    conn = sqlite3.connect("pos_restaurante.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE ventas SET cerrada = 1 WHERE cerrada = 0")
    conn.commit()
    conn.close()

def db_obtener_ventas_activas():
    conn = sqlite3.connect("pos_restaurante.db")
    cursor = conn.cursor()
    cursor.execute("SELECT mesa_id, detalle, total, fecha FROM ventas WHERE cerrada = 0")
    datos = cursor.fetchall()
    conn.close()
    return datos

def db_cargar_estado_inicial():
    conn = sqlite3.connect("pos_restaurante.db")
    cursor = conn.cursor()
    cursor.execute("SELECT mesa_id, nombre, precio, cantidad, destino, enviado FROM items_activos")
    filas = cursor.fetchall()
    conn.close()
    datos = {i: [] for i in range(1, 21)}
    for f in filas:
        datos[f[0]].append({"n": f[1], "p": f[2], "q": f[3], "d": f[4], "enviado": bool(f[5])})
    return datos

# --- APLICACIÓN PRINCIPAL ---
def main(page: ft.Page):
    init_db()
    page.title = "POS Restaurante Pro - SUNMI D3"
    page.theme_mode = "light"
    page.padding = 0

    cuentas = db_cargar_estado_inicial()
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
    def ocultar_todo():
        v_mesas.visible = v_pedido.visible = v_login.visible = False
        v_admin.visible = v_confirmacion.visible = v_ticket_final.visible = False
        v_confirm_cierre.visible = v_resumen_cierre.visible = False

    def ir_a_mesas(e):
        ocultar_todo()
        user_input.value = ""
        pass_input.value = ""
        v_mesas.visible = True
        for c in grid_mesas.controls:
            c.bgcolor = "orange" if len(cuentas[c.data]) > 0 else "blue"
        page.update()

    def ir_a_pedido(e):
        ocultar_todo()
        estado["mesa"] = e.control.data
        txt_titulo_mesa.value = f"MESA #{estado['mesa']}"
        v_pedido.visible = True
        mostrar_mensaje_central("¡Bienvenido!\nSelecciona productos.", "blue")
        refrescar_ticket()
        page.update()

    def ir_a_login(e):
        ocultar_todo()
        user_input.value = ""
        pass_input.value = ""
        v_login.visible = True
        page.update()

    def ir_a_admin(e):
        ocultar_todo()
        v_admin.visible = True
        actualizar_reporte_admin()
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

    # --- LÓGICA DE ADMINISTRACIÓN ---
    def validar_login(e):
        if user_input.value == "admin" and pass_input.value == "1234":
            ir_a_admin(None)
        else:
            page.snack_bar = ft.SnackBar(ft.Text("Credenciales Incorrectas"), bgcolor="red")
            page.snack_bar.open = True
        page.update()

    def actualizar_reporte_admin():
        ventas_activas = db_obtener_ventas_activas()
        col_reportes_dia.controls.clear()
        total_acumulado = 0
        for m_id, detalle, total, fecha in ventas_activas:
            total_acumulado += total
            col_reportes_dia.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Text(f"MESA {m_id}", weight="bold", size=18),
                        ft.Text("Productos pedidos:"),
                        ft.Text(detalle, color="grey", italic=True),
                        ft.Row([
                            ft.Text(f"Total ingresado: ${total}", weight="bold", color="green"),
                            ft.Text(f"Pago: {fecha}", size=12, color="grey")
                        ], alignment="spaceBetween")
                    ]), padding=15, border=ft.border.all(1, "grey"), border_radius=10, margin=ft.margin.only(bottom=10)
                )
            )
        txt_ingreso_total_dia.value = f"TOTAL INGRESADO HOY: ${total_acumulado}"
        page.update()

    def abrir_confirmacion_cierre(e):
        v_confirm_cierre.visible = True
        page.update()

    def ejecutar_cierre_final(e):
        ventas = db_obtener_ventas_activas()
        total_final = sum(v[2] for v in ventas)
        fecha_hoy = datetime.now().strftime("%Y-%m-%d")
        db_ejecutar_cierre_caja()
        v_confirm_cierre.visible = False
        txt_resumen_cierre_total.value = f"INGRESO TOTAL: ${total_final}"
        txt_resumen_cierre_fecha.value = f"FECHA: {fecha_hoy}"
        v_resumen_cierre.visible = True
        page.update()

    # --- LÓGICA DE PEDIDOS ---
    def agregar_item(nombre, precio, destino):
        m_id = estado["mesa"]
        encontrado = False
        for item in cuentas[m_id]:
            if item["n"] == nombre and not item["enviado"]:
                item["q"] += 1; encontrado = True
                db_guardar_item_activo(m_id, item); break
        if not encontrado:
            nuevo = {"n": nombre, "p": precio, "d": destino, "q": 1, "enviado": False}
            cuentas[m_id].append(nuevo); db_guardar_item_activo(m_id, nuevo)
        refrescar_ticket()

    def quitar_item(nombre):
        m_id = estado["mesa"]
        for i, item in enumerate(cuentas[m_id]):
            if item["n"] == nombre and not item["enviado"]:
                db_remover_item_activo(m_id, nombre)
                if item["q"] > 1: item["q"] -= 1
                else: cuentas[m_id].pop(i)
                break
        refrescar_ticket()

    def refrescar_ticket():
        col_ticket.controls.clear()
        total = 0
        for item in cuentas[estado["mesa"]]:
            sub = item["p"] * item["q"]
            icono = ft.Text(" ✔ ", color="green") if item["enviado"] else ft.TextButton(
                content=ft.Text(" X ", color="red", weight="bold"), on_click=lambda e, n=item["n"]: quitar_item(n))
            col_ticket.controls.append(ft.Row([icono, ft.Text(f"{item['q']}x {item['n']}", expand=True), ft.Text(f"${sub}")]))
            total += sub
        txt_total.value = f"TOTAL: ${total}"; page.update()

    def filtrar_menu(categoria):
        grid_prods.controls.clear()
        btns = ft.GridView(runs_count=3, spacing=10, max_extent=150)
        for p in MENU:
            if p["c"] == categoria:
                btns.controls.append(ft.ElevatedButton(content=ft.Text(f"{p['n']}\n${p['p']}", text_align="center"),
                    on_click=lambda e, n=p['n'], pr=p['p'], d=p['d']: agregar_item(n, pr, d), height=80))
        grid_prods.controls.append(btns); page.update()

    # --- COMANDAS Y LOGS (RESTAURADOS) ---
    def enviar_comanda(e):
        nuevos = [i for i in cuentas[estado["mesa"]] if not i["enviado"]]
        if not nuevos:
            mostrar_mensaje_central("AVISO:\nNo hay productos nuevos para enviar.", "orange")
            return
        
        if not any(i["enviado"] for i in cuentas[estado["mesa"]]):
            print(f"\n**************************************************")
            print(f" [!] ESTADO: MESA {estado['mesa']} OCUPADA")
            print(f" [!] APERTURA: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"**************************************************")

        db_marcar_enviados(estado["mesa"])
        for i in cuentas[estado["mesa"]]: i["enviado"] = True
        
        print(f"[*] ENVIANDO COMANDA MESA {estado['mesa']}")
        for z in ["BARRA", "COCINA", "OTROS"]:
            items = [f"{i['q']}x {i['n']}" for i in nuevos if i["d"] == z]
            if items: print(f"    -> {z}: {', '.join(items)}")
        
        refrescar_ticket(); mostrar_mensaje_central("¡ORDEN ENVIADA!", "green")

    def abrir_confirmacion(e):
        m_actual = cuentas[estado["mesa"]]
        if not m_actual:
            mostrar_mensaje_central("ERROR:\nLa cuenta está vacía.", "red"); return
        if any(not i["enviado"] for i in m_actual):
            mostrar_mensaje_central("ADVERTENCIA:\nEnvía la comanda primero.", "red"); return
        v_confirmacion.visible = True; page.update()

    def mostrar_ticket_final(e):
        col_resumen_final.controls.clear()
        total = 0
        for i in cuentas[estado["mesa"]]:
            sub = i['p'] * i['q']
            col_resumen_final.controls.append(ft.Text(f"{i['q']} x {i['n']} .... ${sub}", size=18))
            total += sub
        txt_total_final.value = f"TOTAL FINAL: ${total}"
        v_confirmacion.visible = False; v_ticket_final.visible = True; page.update()

    def finalizar_pago(e):
        items = cuentas[estado["mesa"]]
        detalle = "\n".join([f"• {i['q']}x {i['n']}" for i in items])
        total = sum(i['p'] * i['q'] for i in items)
        
        print(f"\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print(f" REPORTE CIERRE MESA {estado['mesa']} | TOTAL: ${total}")
        print(f" FECHA: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n")

        db_registrar_venta_final(estado["mesa"], detalle, total)
        db_limpiar_mesa(estado["mesa"])
        cuentas[estado["mesa"]] = []; ir_a_mesas(None)

    # --- INTERFACES ---
    grid_mesas = ft.GridView(expand=True, runs_count=5, spacing=15)
    for i in range(1, 21):
        grid_mesas.controls.append(ft.Container(content=ft.Text(f"{i}", color="white", size=22, weight="bold"), bgcolor="blue", border_radius=10, padding=20, on_click=ir_a_pedido, data=i))

    v_mesas = ft.Container(content=ft.Column([ft.Row([ft.Text("SALÓN", size=30, weight="bold", expand=True), ft.TextButton("ADMIN", on_click=ir_a_login)]), grid_mesas]), expand=True, padding=20, bgcolor="white")

    # LOGIN TOTALMENTE CENTRADO (METODO SEGURO)
    user_input = ft.TextField(label="Usuario", width=350)
    pass_input = ft.TextField(label="Contraseña", password=True, width=350)
    
    # Usamos una Fila y Columna con MainAxisAlignment para centrar sin usar módulos problemáticos
    v_login = ft.Container(
        content=ft.Row(
            [
                ft.Column(
                    [
                        ft.Text("ACCESO ADMIN", size=40, weight="bold"),
                        user_input,
                        pass_input,
                        ft.ElevatedButton("ENTRAR", bgcolor="blue", color="white", width=350, height=50, on_click=validar_login),
                        ft.TextButton("VOLVER", on_click=ir_a_mesas)
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        visible=False, 
        expand=True, 
        bgcolor="white"
    )

    col_reportes_dia = ft.Column(scroll="always", expand=True)
    txt_ingreso_total_dia = ft.Text("", size=25, weight="bold", color="green")
    v_admin = ft.Container(content=ft.Column([ft.Row([ft.Text("REPORTE DIARIO", size=30, weight="bold"), ft.Row([ft.ElevatedButton("CIERRE DE CAJA", bgcolor="orange", color="white", on_click=abrir_confirmacion_cierre), ft.TextButton("SALIR", on_click=ir_a_mesas)])], alignment="spaceBetween"), ft.Divider(), col_reportes_dia, ft.Divider(), ft.Row([txt_ingreso_total_dia], alignment="center")]), visible=False, expand=True, padding=30, bgcolor="white")

    v_confirm_cierre = ft.Container(content=ft.Row([ft.Column([ft.Text("¡ADVERTENCIA!", size=30, weight="bold", color="red"), ft.Text("De seguir con la acción, se resetearán\nlos ingresos guardados.", size=20, text_align="center"), ft.Row([ft.ElevatedButton("SÍ, CONTINUAR", bgcolor="green", color="white", on_click=ejecutar_cierre_final, width=200, height=60), ft.ElevatedButton("NO", bgcolor="red", color="white", on_click=lambda _: [setattr(v_confirm_cierre, 'visible', False), page.update()], width=200, height=60)], alignment="center")], alignment="center", horizontal_alignment="center")], alignment="center"), bgcolor="rgba(255,255,255,0.95)", visible=False, expand=True)

    txt_resumen_cierre_total = ft.Text("", size=35, weight="bold", color="green")
    txt_resumen_cierre_fecha = ft.Text("", size=20)
    v_resumen_cierre = ft.Container(content=ft.Row([ft.Column([ft.Text("RESUMEN DE CIERRE", size=30, weight="bold"), ft.Divider(), txt_resumen_cierre_total, txt_resumen_cierre_fecha, ft.Container(height=20), ft.ElevatedButton("CERRAR", bgcolor="blue", color="white", width=400, height=80, on_click=ir_a_admin)], alignment="center", horizontal_alignment="center")], alignment="center"), bgcolor="white", visible=False, expand=True)

    txt_titulo_mesa, col_ticket, txt_total, grid_prods = ft.Text("", size=25, weight="bold"), ft.Column(scroll="always", expand=True), ft.Text("TOTAL: $0", size=35, weight="bold", color="green"), ft.Column(expand=True)
    v_pedido = ft.Container(content=ft.Row([ft.Column([ft.TextButton("<- VOLVER", on_click=ir_a_mesas), ft.Row([ft.ElevatedButton("BEBIDAS", on_click=lambda _: [grid_prods.controls.clear(), [grid_prods.controls.append(ft.ElevatedButton(f"{p['n']}\n${p['p']}", on_click=lambda e, n=p['n'], pr=p['p'], d=p['d']: agregar_item(n, pr, d), height=80)) for p in MENU if p['c'] == 'BEBIDAS'], page.update()]), ft.ElevatedButton("COMIDA", on_click=lambda _: [grid_prods.controls.clear(), [grid_prods.controls.append(ft.ElevatedButton(f"{p['n']}\n${p['p']}", on_click=lambda e, n=p['n'], pr=p['p'], d=p['d']: agregar_item(n, pr, d), height=80)) for p in MENU if p['c'] == 'COMIDA'], page.update()]), ft.ElevatedButton("POSTRES", on_click=lambda _: [grid_prods.controls.clear(), [grid_prods.controls.append(ft.ElevatedButton(f"{p['n']}\n${p['p']}", on_click=lambda e, n=p['n'], pr=p['p'], d=p['d']: agregar_item(n, pr, d), height=80)) for p in MENU if p['c'] == 'POSTRES'], page.update()])]), grid_prods], expand=3), ft.Container(content=ft.Column([txt_titulo_mesa, ft.Divider(), col_ticket, ft.Divider(), txt_total, ft.ElevatedButton("ENVIAR COMANDA", bgcolor="orange", color="white", height=60, on_click=enviar_comanda, width=400), ft.ElevatedButton("PAGAR CUENTA", bgcolor="green", color="white", height=60, on_click=abrir_confirmacion)]), expand=2, bgcolor="#F5F5F5", padding=20, border_radius=15)]), expand=True, visible=False, bgcolor="white")

    v_confirmacion = ft.Container(content=ft.Row([ft.Column([ft.Text("¿CONFIRMAR PAGO?", size=25, weight="bold"), ft.Row([ft.ElevatedButton("SÍ, PAGAR", bgcolor="green", color="white", on_click=mostrar_ticket_final, width=180, height=60), ft.ElevatedButton("NO", bgcolor="red", color="white", on_click=lambda _: [setattr(v_confirmacion, 'visible', False), page.update()], width=180, height=60)], alignment="center")], alignment="center", horizontal_alignment="center")], alignment="center"), bgcolor="rgba(255,255,255,0.9)", visible=False, expand=True)
    col_resumen_final, txt_total_final = ft.Column(scroll="always", expand=True), ft.Text("", size=40, weight="bold", color="green")
    v_ticket_final = ft.Container(content=ft.Column([ft.Text("RESUMEN DE VENTA", size=30, weight="bold", text_align="center"), ft.Divider(), col_resumen_final, ft.Divider(), txt_total_final, ft.ElevatedButton("FINALIZAR", bgcolor="blue", color="white", width=400, height=80, on_click=finalizar_pago)], horizontal_alignment="center"), bgcolor="white", visible=False, expand=True, padding=50)

    page.add(ft.Stack([v_mesas, v_pedido, v_login, v_admin, v_confirmacion, v_ticket_final, v_confirm_cierre, v_resumen_cierre], expand=True))
    ir_a_mesas(None)

ft.app(target=main)