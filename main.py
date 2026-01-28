import flet as ft
import sqlite3
from datetime import datetime

# --- CAPA DE DATOS (SQLite) ---
def init_db():
    conn = sqlite3.connect("pos_restaurante.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS ventas (id INTEGER PRIMARY KEY AUTOINCREMENT, total REAL, fecha TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS compras (id INTEGER PRIMARY KEY AUTOINCREMENT, producto TEXT, cantidad INTEGER, costo REAL, fecha TEXT)")
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

    # Estado: Carga desde DB para persistencia
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

    def ir_a_mesas(e):
        ocultar_todo()
        v_mesas.visible = True
        for c in grid_mesas.controls:
            c.bgcolor = "orange" if len(cuentas[c.data]) > 0 else "blue"
        page.update()

    def ir_a_pedido(e):
        ocultar_todo()
        estado["mesa"] = e.control.data
        txt_titulo_mesa.value = f"MESA #{estado['mesa']}"
        v_pedido.visible = True
        mostrar_mensaje_central("¡Bienvenido!\nSelecciona una categoría arriba.", "blue")
        refrescar_ticket()
        page.update()

    def ir_a_login(e):
        ocultar_todo()
        v_login.visible = True
        page.update()

    def ir_a_admin(e):
        ocultar_todo()
        v_admin.visible = True
        actualizar_resumen()
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
            user_input.value = ""; pass_input.value = ""; ir_a_admin(None)
        else:
            page.snack_bar = ft.SnackBar(ft.Text("Credenciales Incorrectas"), bgcolor="red")
            page.snack_bar.open = True; page.update()

    def registrar_compra(e):
        if input_gasto_nom.value and input_gasto_monto.value:
            try:
                conn = sqlite3.connect("pos_restaurante.db")
                conn.execute("INSERT INTO compras (producto, cantidad, costo, fecha) VALUES (?,?,?,?)",
                             (input_gasto_nom.value, int(input_gasto_cant.value), float(input_gasto_monto.value), datetime.now().strftime("%Y-%m-%d %H:%M")))
                conn.commit(); conn.close()
                input_gasto_nom.value = ""; input_gasto_monto.value = ""; actualizar_resumen()
            except: pass
        page.update()

    def actualizar_resumen():
        conn = sqlite3.connect("pos_restaurante.db")
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(total) FROM ventas"); ingresos = cursor.fetchone()[0] or 0.0
        cursor.execute("SELECT SUM(costo) FROM compras"); egresos = cursor.fetchone()[0] or 0.0
        cursor.execute("SELECT fecha, cantidad, producto, costo FROM compras ORDER BY id DESC LIMIT 10")
        hist = cursor.fetchall(); conn.close()
        col_resumen_balance.controls.clear(); col_lista_compras.controls.clear()
        col_resumen_balance.controls.append(ft.Text(f"INGRESOS: ${ingresos}", color="green", size=20, weight="bold"))
        col_resumen_balance.controls.append(ft.Text(f"EGRESOS: ${egresos}", color="red", size=20, weight="bold"))
        col_resumen_balance.controls.append(ft.Text(f"NETO: ${ingresos-egresos}", size=25, weight="bold"))
        for f, q, n, p in hist: col_lista_compras.controls.append(ft.Text(f"• [{f}] {q}x {n} - ${p}"))
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

    # --- COMANDAS Y CIERRES (CORRECCIÓN: Aviso restaurado) ---
    def enviar_comanda(e):
        nuevos = [i for i in cuentas[estado["mesa"]] if not i["enviado"]]
        if not nuevos: # <--- RESTAURADO: Mensaje de advertencia
            mostrar_mensaje_central("AVISO:\nNo hay productos nuevos para enviar.", "orange")
            return
        
        if not any(i["enviado"] for i in cuentas[estado["mesa"]]):
            print(f"\n**************************************************\n [!] ESTADO: MESA {estado['mesa']} OCUPADA\n [!] APERTURA: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n" + "*"*50)

        db_marcar_enviados(estado["mesa"])
        for i in cuentas[estado["mesa"]]: i["enviado"] = True
        
        print(f"[*] ENVIANDO COMANDA MESA {estado['mesa']}")
        for z in ["BARRA", "COCINA", "OTROS"]:
            items = [f"{i['q']}x {i['n']}" for i in nuevos if i["d"] == z]
            if items: print(f"    -> {z}: {', '.join(items)}")
        
        refrescar_ticket(); mostrar_mensaje_central("¡ORDEN ENVIADA!", "green")

    def abrir_confirmacion(e):
        if not cuentas[estado["mesa"]]:
            mostrar_mensaje_central("ERROR:\nLa cuenta está vacía.", "red"); return
        if any(not i["enviado"] for i in cuentas[estado["mesa"]]):
            mostrar_mensaje_central("ADVERTENCIA:\nEnvía la comanda primero.", "red"); return
        v_confirmacion.visible = True; page.update()

    def mostrar_ticket_final(e): # <--- Restaurado: Llena resumen
        col_resumen_final.controls.clear()
        total = 0
        for i in cuentas[estado["mesa"]]:
            sub = i['p'] * i['q']
            col_resumen_final.controls.append(ft.Text(f"{i['q']} x {i['n']} .... ${sub}", size=18))
            total += sub
        txt_total_final.value = f"TOTAL: ${total}"
        v_confirmacion.visible = False; v_ticket_final.visible = True; page.update()

    def finalizar_y_limpiar(e):
        total = sum(i["p"] * i["q"] for i in cuentas[estado["mesa"]])
        conn = sqlite3.connect("pos_restaurante.db")
        conn.execute("INSERT INTO ventas (total, fecha) VALUES (?,?)", (total, datetime.now().strftime("%Y-%m-%d %H:%M")))
        conn.commit(); conn.close()
        print(f"\n" + "!"*45 + f"\n REPORTE CIERRE MESA {estado['mesa']} | TOTAL: ${total}\n FECHA: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n" + "!"*45 + "\n")
        db_limpiar_mesa(estado["mesa"]); cuentas[estado["mesa"]] = []; ir_a_mesas(None)

    # --- INTERFACES (FONDOS SÓLIDOS) ---
    grid_mesas = ft.GridView(expand=True, runs_count=5, spacing=15)
    for i in range(1, 21):
        grid_mesas.controls.append(ft.Container(content=ft.Text(f"{i}", color="white", size=22, weight="bold"),
            bgcolor="blue", border_radius=10, padding=20, on_click=ir_a_pedido, data=i))

    v_mesas = ft.Container(content=ft.Column([ft.Row([ft.Text("SALÓN", size=30, weight="bold", expand=True), ft.TextButton("ADMIN", on_click=ir_a_login)]), grid_mesas]), expand=True, padding=20, bgcolor="white")

    v_login = ft.Container(content=ft.Column([ft.Text("ACCESO ADMIN", size=30, weight="bold"), user_input := ft.TextField(label="Usuario", width=300), pass_input := ft.TextField(label="Contraseña", password=True, width=300), ft.ElevatedButton("ENTRAR", bgcolor="blue", color="white", width=300, on_click=validar_login), ft.TextButton("VOLVER", on_click=ir_a_mesas)], alignment="center", horizontal_alignment="center"), visible=False, expand=True, bgcolor="white")

    col_resumen_balance, col_lista_compras = ft.Column(), ft.Column(scroll="always", expand=True)
    v_admin = ft.Container(content=ft.Column([ft.Row([ft.Text("ADMINISTRACIÓN", size=30, weight="bold"), ft.TextButton("CERRAR", on_click=ir_a_mesas)], alignment="spaceBetween"), ft.Row([ft.Column([ft.Text("BALANCE", size=22, weight="bold"), col_resumen_balance, ft.Divider(), ft.Text("HISTORIAL", size=18, weight="bold"), col_lista_compras], expand=1), ft.VerticalDivider(), ft.Column([ft.Text("INVENTARIO", size=22, weight="bold"), ft.Row([input_gasto_nom := ft.TextField(label="Producto", expand=True), input_gasto_cant := ft.TextField(label="Cant.", width=80, value="1"), input_gasto_monto := ft.TextField(label="Total $", width=140)]), ft.ElevatedButton("GUARDAR", bgcolor="red", color="white", width=400, on_click=registrar_compra)], expand=1)], expand=True)]), visible=False, expand=True, padding=30, bgcolor="white")

    txt_titulo_mesa, col_ticket, txt_total, grid_prods = ft.Text("", size=25, weight="bold"), ft.Column(scroll="always", expand=True), ft.Text("TOTAL: $0", size=35, weight="bold", color="green"), ft.Column(expand=True)
    v_pedido = ft.Container(content=ft.Row([ft.Column([ft.TextButton("<- VOLVER", on_click=ir_a_mesas), ft.Row([ft.ElevatedButton("BEBIDAS", on_click=lambda _: filtrar_menu("BEBIDAS")), ft.ElevatedButton("COMIDA", on_click=lambda _: filtrar_menu("COMIDA")), ft.ElevatedButton("POSTRES", on_click=lambda _: filtrar_menu("POSTRES"))]), grid_prods], expand=3), ft.Container(content=ft.Column([txt_titulo_mesa, ft.Divider(), col_ticket, ft.Divider(), txt_total, ft.ElevatedButton("ENVIAR COMANDA", bgcolor="orange", color="white", height=60, on_click=enviar_comanda, width=400), ft.ElevatedButton("PAGAR CUENTA", bgcolor="green", color="white", height=60, on_click=abrir_confirmacion, width=400)]), expand=2, bgcolor="#F5F5F5", padding=20, border_radius=15)]), expand=True, visible=False, bgcolor="white")

    v_confirmacion = ft.Container(content=ft.Column([ft.Text("¿CONFIRMAR PAGO?", size=25, weight="bold"), ft.Row([ft.ElevatedButton("SÍ, PAGAR", bgcolor="green", color="white", on_click=mostrar_ticket_final, width=180, height=60), ft.ElevatedButton("NO", bgcolor="red", color="white", on_click=lambda _: [setattr(v_confirmacion, 'visible', False), page.update()], width=180, height=60)], alignment="center")], alignment="center"), bgcolor="rgba(255,255,255,0.9)", visible=False, expand=True)
    col_resumen_final, txt_total_final = ft.Column(scroll="always", expand=True), ft.Text("", size=40, weight="bold", color="green")
    v_ticket_final = ft.Container(content=ft.Column([ft.Text("RESUMEN DE VENTA", size=30, weight="bold", text_align="center"), ft.Divider(), col_resumen_final, ft.Divider(), txt_total_final, ft.ElevatedButton("FINALIZAR", bgcolor="blue", color="white", width=400, height=80, on_click=finalizar_y_limpiar)], horizontal_alignment="center"), bgcolor="white", visible=False, expand=True, padding=50)

    page.add(ft.Stack([v_mesas, v_pedido, v_login, v_admin, v_confirmacion, v_ticket_final], expand=True))
    ir_a_mesas(None)

ft.app(target=main)