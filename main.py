import flet as ft
import sqlite3
import openpyxl
from openpyxl.styles import Font
from datetime import datetime
import os

# --- CONFIGURACIÓN ---
TABLET_ID = "01"

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
            metodo_pago TEXT,
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

def db_registrar_venta_final(mesa_id, detalle, total, metodo):
    conn = sqlite3.connect("pos_restaurante.db")
    cursor = conn.cursor()
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M")
    cursor.execute("INSERT INTO ventas (mesa_id, detalle, total, fecha, metodo_pago, cerrada) VALUES (?, ?, ?, ?, ?, 0)", 
                   (mesa_id, detalle, total, ahora, metodo))
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
    cursor.execute("SELECT mesa_id, detalle, total, fecha, metodo_pago FROM ventas WHERE cerrada = 0")
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

# --- FUNCIÓN EXCEL ---
def generar_excel_cierre(ventas, total, efectivo, tarjeta):
    nombre_subcarpeta = "Reportes Cierre de Caja"
    if not os.path.exists(nombre_subcarpeta):
        os.makedirs(nombre_subcarpeta)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Corte de Caja"
    ws["A1"] = f"CORTE DE CAJA - TABLET {TABLET_ID}"
    ws["A1"].font = Font(bold=True, size=14)
    ws["A2"] = f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    ws["A4"], ws["B4"] = "TOTAL GENERAL:", total
    ws["A5"], ws["B5"] = "EFECTIVO:", efectivo
    ws["A6"], ws["B6"] = "TARJETA:", tarjeta
    headers = ["Mesa", "Hora", "Método", "Total", "Detalle"]
    for col, text in enumerate(headers, 1):
        cell = ws.cell(row=8, column=col, value=text)
        cell.font = Font(bold=True)
    for row_idx, v in enumerate(ventas, 9):
        ws.cell(row=row_idx, column=1, value=f"Mesa {v[0]}")
        ws.cell(row=row_idx, column=2, value=v[3])
        ws.cell(row=row_idx, column=3, value=v[4])
        ws.cell(row=row_idx, column=4, value=v[2])
        ws.cell(row=row_idx, column=5, value=v[1])
    nombre_archivo = f"Corte_T{TABLET_ID}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    ruta_completa = os.path.join(nombre_subcarpeta, nombre_archivo)
    wb.save(ruta_completa)
    return ruta_completa

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

    # --- FUNCIONES DE LÓGICA (DEFINIDAS ANTES PARA EVITAR ERRORES) ---
    def ocultar_todo():
        v_mesas.visible = v_pedido.visible = v_login.visible = False
        v_admin.visible = v_confirmacion.visible = v_ticket_final.visible = False
        v_confirm_cierre.visible = v_resumen_cierre.visible = v_pago_metodo.visible = False
        v_pago_finalizado.visible = False
        columna_botones_acciones.visible = True

    def salir_de_la_app(e):
        print("\n[!] Cerrando aplicación de forma segura...")
        import os
        os._exit(0) # Método infalible para cerrar la app

    def ir_a_mesas(e):
        ocultar_todo()
        user_input.value = ""; pass_input.value = ""
        v_mesas.visible = True
        for c in grid_mesas.controls:
            c.bgcolor = "orange" if len(cuentas[c.data]) > 0 else "blue"
        page.update()

    def ir_a_login(e):
        ocultar_todo()
        v_login.visible = True
        page.update()

    def ir_a_pedido(e):
        ocultar_todo()
        estado["mesa"] = e.control.data
        txt_titulo_mesa.value = f"MESA #{estado['mesa']}"
        v_pedido.visible = True
        mostrar_mensaje_central("¡Bienvenido!\nSelecciona productos.", "blue")
        refrescar_ticket()
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
                ft.Row([ft.Text(texto, size=22, color=color_texto, weight="bold", text_align="center")], alignment=ft.MainAxisAlignment.CENTER)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, width=700)
        )
        page.update()

    def refrescar_ticket():
        col_ticket.controls.clear()
        total = 0
        for item in cuentas[estado["mesa"]]:
            sub = item["p"] * item["q"]
            # BOTÓN X CORREGIDO PARA ACTUALIZAR MEMORIA Y DB
            icono = ft.Text(" ✔ ", color="green") if item["enviado"] else ft.TextButton(
                content=ft.Text(" X ", color="red", weight="bold"),
                on_click=lambda e, n=item["n"]: quitar_item(n))
            col_ticket.controls.append(ft.Row([icono, ft.Text(f"{item['q']}x {item['n']}", expand=True), ft.Text(f"${sub}")]))
            total += sub
        txt_total.value = f"TOTAL: ${total}"
        page.update()

    def quitar_item(nombre):
        m_id = estado["mesa"]
        for i, item in enumerate(cuentas[m_id]):
            if item["n"] == nombre and not item["enviado"]:
                db_remover_item_activo(m_id, nombre)
                if item["q"] > 1:
                    item["q"] -= 1
                else:
                    cuentas[m_id].pop(i)
                break
        refrescar_ticket()

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

    def enviar_comanda(e):
        nuevos = [i for i in cuentas[estado["mesa"]] if not i["enviado"]]
        if not nuevos:
            mostrar_mensaje_central("AVISO:\nNo hay productos nuevos.", "orange"); return
        if not any(i["enviado"] for i in cuentas[estado["mesa"]]):
            print("\n" + "*"*50 + f"\n [!] ESTADO: MESA {estado['mesa']} OCUPADA\n [!] APERTURA: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n" + "*"*50)
        db_marcar_enviados(estado["mesa"])
        for i in cuentas[estado["mesa"]]: i["enviado"] = True
        print(f"[*] ENVIANDO COMANDA MESA {estado['mesa']}")
        for z in ["BARRA", "COCINA", "OTROS"]:
            items = [f"{i['q']}x {i['n']}" for i in nuevos if i["d"] == z]
            if items: print(f"    -> {z}: {', '.join(items)}")
        refrescar_ticket(); mostrar_mensaje_central("¡ORDEN ENVIADA!", "green")

    def finalizar_pago_total(metodo_elegido):
        items = cuentas[estado["mesa"]]
        detalle = "\n".join([f"• {i['q']}x {i['n']}" for i in items])
        total = sum(i['p'] * i['q'] for i in items)
        print("\n" + "!"*45 + f"\n REPORTE CIERRE MESA {estado['mesa']} | TOTAL: ${total}\n MÉTODO: {metodo_elegido.upper()}\n FECHA: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n" + "!"*45)
        db_registrar_venta_final(estado["mesa"], detalle, total, metodo_elegido)
        db_limpiar_mesa(estado["mesa"])
        cuentas[estado["mesa"]] = []
        ocultar_todo()
        txt_mensaje_despedida.value = f"¡PAGO REGISTRADO EXITOSAMENTE!\nMétodo seleccionado: {metodo_elegido.upper()}"
        v_pago_finalizado.visible = True
        page.update()

    def ejecutar_cierre_final(e):
        ventas = db_obtener_ventas_activas()
        total_final = sum(v[2] for v in ventas)
        sub_efectivo = sum(v[2] for v in ventas if v[4] == "Efectivo")
        sub_tarjeta = sum(v[2] for v in ventas if v[4] == "Tarjeta")
        archivo = generar_excel_cierre(ventas, total_final, sub_efectivo, sub_tarjeta)
        db_ejecutar_cierre_caja()
        v_confirm_cierre.visible = False
        txt_resumen_cierre_total.value = f"INGRESO TOTAL: ${total_final}"
        txt_resumen_efectivo.value = f"EFECTIVO: ${sub_efectivo}"
        txt_resumen_tarjeta.value = f"TARJETA: ${sub_tarjeta}"
        # SE RESTAURA FECHA Y HORA EN PANTALLA
        txt_resumen_cierre_fecha.value = f"FECHA Y HORA: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        txt_archivo_creado.value = f"Archivo creado en subcarpeta: {archivo}"
        v_resumen_cierre.visible = True
        page.update()

    def filtrar_menu(categoria):
        grid_prods.controls.clear()
        btns = ft.GridView(runs_count=3, spacing=10, max_extent=150)
        for p in MENU:
            if p["c"] == categoria:
                btns.controls.append(ft.ElevatedButton(content=ft.Text(f"{p['n']}\n${p['p']}", text_align="center"),
                    on_click=lambda e, n=p['n'], pr=p['p'], d=p['d']: agregar_item(n, pr, d), height=80))
        grid_prods.controls.append(btns); page.update()

    def actualizar_reporte_admin():
        ventas = db_obtener_ventas_activas()
        col_reportes_dia.controls.clear()
        total = sum(v[2] for v in ventas)
        for m_id, detalle, tot, fecha, metodo in ventas:
            col_reportes_dia.controls.append(ft.Container(content=ft.Column([
                ft.Row([ft.Text(f"MESA {m_id}", weight="bold"), ft.Text(f"PAGO: {metodo.upper()}", color="blue", weight="bold")], alignment="spaceBetween"),
                ft.Text(detalle, size=12, color="grey"),
                ft.Row([ft.Text(f"Total: ${tot}", color="green", weight="bold"), ft.Text(fecha, size=10)], alignment="spaceBetween")
            ]), padding=10, border=ft.border.all(1, "grey"), border_radius=8))
        txt_ingreso_total_dia.value = f"TOTAL EN CAJA: ${total}"; page.update()

    # --- UI COMPONENTS ---
    user_input, pass_input = ft.TextField(label="Usuario", width=350), ft.TextField(label="Contraseña", password=True, width=350)
    v_login = ft.Container(content=ft.Row([ft.Column([ft.Text("ACCESO ADMIN", size=40, weight="bold"), user_input, pass_input, ft.ElevatedButton("ENTRAR", bgcolor="blue", color="white", width=350, height=50, on_click=lambda _: ir_a_admin(None) if user_input.value=="admin" and pass_input.value=="1234" else None), ft.TextButton("VOLVER", on_click=ir_a_mesas)], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment="center")], alignment=ft.MainAxisAlignment.CENTER), visible=False, expand=True, bgcolor="white")

    col_reportes_dia, txt_ingreso_total_dia = ft.Column(scroll="always", expand=True), ft.Text("", size=25, weight="bold", color="green")
    
    # PANEL ADMIN ACTUALIZADO SIN ICONOS
    v_admin = ft.Container(content=ft.Column([
        ft.Row([
            ft.Text("REPORTE DIARIO", size=30, weight="bold"), 
            ft.Row([
                ft.ElevatedButton("SALIR DE LA APP", bgcolor="red", color="white", on_click=salir_de_la_app), 
                ft.ElevatedButton("CIERRE", bgcolor="orange", color="white", on_click=lambda _: [setattr(v_confirm_cierre, 'visible', True), page.update()]), 
                ft.TextButton("SALIR PANEL", on_click=ir_a_mesas)
            ])
        ], alignment="spaceBetween"), 
        ft.Divider(), col_reportes_dia, ft.Divider(), ft.Row([txt_ingreso_total_dia], alignment="center")
    ]), visible=False, expand=True, padding=30, bgcolor="white")

    v_confirm_cierre = ft.Container(content=ft.Row([ft.Column([ft.Text("¡ADVERTENCIA!", size=30, weight="bold", color="red"), ft.Text("Se resetearán los ingresos."), ft.Row([ft.ElevatedButton("SÍ", bgcolor="green", color="white", on_click=ejecutar_cierre_final, width=150), ft.ElevatedButton("NO", bgcolor="red", color="white", on_click=lambda _: [setattr(v_confirm_cierre, 'visible', False), page.update()], width=150)], alignment="center")], alignment="center", horizontal_alignment="center")], alignment="center"), visible=False, expand=True, bgcolor="rgba(255,255,255,0.95)")
    v_resumen_cierre = ft.Container(content=ft.Row([ft.Column([ft.Text("RESUMEN CIERRE", size=30, weight="bold"), txt_resumen_cierre_total := ft.Text("", size=30, color="green", weight="bold"), txt_resumen_efectivo := ft.Text(""), txt_resumen_tarjeta := ft.Text(""), txt_resumen_cierre_fecha := ft.Text("", size=18, weight="bold"), txt_archivo_creado := ft.Text("", size=12, italic=True), ft.ElevatedButton("CERRAR", on_click=ir_a_admin)], alignment="center", horizontal_alignment="center")], alignment="center"), visible=False, expand=True, bgcolor="white")

    grid_mesas = ft.GridView(expand=True, runs_count=5, spacing=15)
    for i in range(1, 21): grid_mesas.controls.append(ft.Container(content=ft.Text(f"{i}", color="white", weight="bold"), bgcolor="blue", border_radius=10, padding=20, on_click=ir_a_pedido, data=i))
    v_mesas = ft.Container(content=ft.Column([ft.Row([ft.Text("SALÓN", size=30, weight="bold", expand=True), ft.TextButton("ADMIN", on_click=ir_a_login)]), grid_mesas]), expand=True, padding=20, bgcolor="white")

    columna_botones_acciones = ft.Column([
        ft.ElevatedButton("COMANDA", bgcolor="orange", color="white", height=60, on_click=enviar_comanda, width=400),
        ft.ElevatedButton("PAGAR CUENTA", bgcolor="green", color="white", height=60, on_click=lambda _: [setattr(v_confirmacion, 'visible', True), page.update()] if cuentas[estado["mesa"]] and not any(not i['enviado'] for i in cuentas[estado['mesa']]) else mostrar_mensaje_central("ERROR:\nCuenta vacía o sin enviar.", "red"), width=400)
    ])

    txt_titulo_mesa, col_ticket, txt_total, grid_prods = ft.Text("", size=25, weight="bold"), ft.Column(scroll="always", expand=True), ft.Text("TOTAL: $0", size=35, weight="bold", color="green"), ft.Column(expand=True)
    v_pedido = ft.Container(content=ft.Row([ft.Column([ft.TextButton("<- VOLVER", on_click=ir_a_mesas), ft.Row([ft.ElevatedButton("BEBIDAS", on_click=lambda _: filtrar_menu("BEBIDAS")), ft.ElevatedButton("COMIDA", on_click=lambda _: filtrar_menu("COMIDA")), ft.ElevatedButton("POSTRES", on_click=lambda _: filtrar_menu("POSTRES"))]), grid_prods], expand=3), ft.Container(content=ft.Column([txt_titulo_mesa, ft.Divider(), col_ticket, ft.Divider(), txt_total, columna_botones_acciones]), expand=2, bgcolor="#F5F5F5", padding=20, border_radius=15)]), expand=True, visible=False, bgcolor="white")

    v_confirmacion = ft.Container(content=ft.Row([ft.Column([ft.Text("¿CONFIRMAR PAGO?", size=25, weight="bold"), ft.Row([ft.ElevatedButton("SÍ, PAGAR", bgcolor="green", color="white", on_click=lambda _: [col_resumen_final.controls.clear(), [col_resumen_final.controls.append(ft.Text(f"{i['q']}x {i['n']} ... ${i['p']*i['q']}")) for i in cuentas[estado['mesa']]], setattr(v_ticket_final, 'visible', True), setattr(v_confirmacion, 'visible', False), setattr(columna_botones_acciones, 'visible', False), page.update()], width=180, height=60), ft.ElevatedButton("NO", bgcolor="red", color="white", on_click=lambda _: [setattr(v_confirmacion, 'visible', False), page.update()], width=180, height=60)], alignment="center")], alignment="center", horizontal_alignment="center")], alignment="center"), visible=False, expand=True, bgcolor="rgba(255,255,255,0.9)")
    
    col_resumen_final = ft.Column(scroll="always", expand=True)
    v_ticket_final = ft.Container(content=ft.Column([ft.Text("TICKET", size=30, weight="bold"), col_resumen_final, ft.ElevatedButton("FINALIZAR", bgcolor="blue", color="white", width=400, height=80, on_click=lambda _: [ocultar_todo(), setattr(v_pago_metodo, 'visible', True), page.update()])], horizontal_alignment="center"), bgcolor="white", visible=False, expand=True, padding=50)

    v_pago_metodo = ft.Container(content=ft.Row([ft.Column([ft.Text("MÉTODO DE PAGO", size=30, weight="bold"), ft.ElevatedButton("EFECTIVO", bgcolor="green", color="white", width=400, height=70, on_click=lambda _: finalizar_pago_total("Efectivo")), ft.ElevatedButton("TARJETA", bgcolor="blue", color="white", width=400, height=70, on_click=lambda _: finalizar_pago_total("Tarjeta"))], alignment="center", horizontal_alignment="center")], alignment="center"), visible=False, expand=True, bgcolor="white")
    v_pago_finalizado = ft.Container(content=ft.Row([ft.Column([ft.Text("GRACIAS", size=40, weight="bold"), txt_mensaje_despedida := ft.Text("", size=22, text_align="center"), ft.ElevatedButton("CERRAR", bgcolor="blue", color="white", width=350, height=70, on_click=ir_a_mesas)], alignment="center", horizontal_alignment="center")], alignment="center"), visible=False, expand=True, bgcolor="white")

    page.add(ft.Stack([v_mesas, v_pedido, v_login, v_admin, v_confirmacion, v_ticket_final, v_confirm_cierre, v_resumen_cierre, v_pago_metodo, v_pago_finalizado], expand=True))
    ir_a_mesas(None)

# --- EJECUCIÓN SEGURA PARA WINDOWS ---
if __name__ == "__main__":
    try:
        ft.app(target=main)
    except Exception as e:
        # Esto silencia cualquier error residual al cerrar la ventana bruscamente
        print("\n[!] Aplicación terminada.")