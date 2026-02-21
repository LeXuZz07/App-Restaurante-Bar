import flet as ft
from datetime import datetime
import os
import database as db
import reports as rp

def main(page: ft.Page):
    db.init_db()
    page.title = "POS Restaurante Pro - SUNMI D3"
    page.theme_mode = "light"
    # Creamos un "Safe Area" manual. 
    page.padding = ft.padding.only(top=45, bottom=45, left=15, right=15)

    cuentas = db.db_cargar_estado_inicial()
    estado = {"mesa": 0}

    # --- UI COMPONENTS GLOBALES ---
    user_input = ft.TextField(label="Usuario", width=350)
    pass_input = ft.TextField(label="Contraseña", password=True, width=350)
    txt_config_tablet_id = ft.TextField(label="ID Tablet", width=120, input_filter=ft.NumbersOnlyInputFilter(), text_align="center")
    
    txt_mensaje_error_gestion = ft.Text("", size=18, weight="bold", expand=True, text_align="center")
    
    # NUEVOS COMPONENTES: Para la pantalla de credenciales
    txt_nuevo_usr = ft.TextField(label="Nombre Usuario", width=350)
    txt_nuevo_pwd = ft.TextField(label="Nueva Contraseña", password=True, width=350)
    txt_mensaje_credenciales = ft.Text("", size=18, weight="bold", text_align="center")

    # --- NAVEGACIÓN Y AUTENTICACIÓN ---
    def ocultar_todo():
        v_mesas.visible = v_pedido.visible = v_login.visible = False
        v_admin.visible = v_confirmacion.visible = v_ticket_final.visible = False
        v_confirm_cierre.visible = v_resumen_cierre.visible = v_pago_metodo.visible = False
        # AQUÍ AGREGAMOS v_credenciales PARA QUE SE OCULTE TAMBIÉN
        v_pago_finalizado.visible = v_gestion_menu.visible = v_credenciales.visible = False
        columna_botones_acciones.visible = True

    def salir_de_la_app(e): os._exit(0)

    def ir_a_mesas(e):
        ocultar_todo()
        user_input.value = ""; pass_input.value = ""
        v_mesas.visible = True
        for c in grid_mesas.controls: c.bgcolor = "orange" if len(cuentas[c.data]) > 0 else "blue"
        page.update()

    def intentar_login(e):
        usr_bd, pwd_bd = db.db_obtener_credenciales()
        if user_input.value == usr_bd and pass_input.value == pwd_bd:
            ir_a_admin(None)
        else:
            page.snack_bar = ft.SnackBar(ft.Text("Usuario o contraseña incorrectos"), bgcolor="red")
            page.snack_bar.open = True
            page.update()

    def ir_a_admin(e):
        ocultar_todo()
        txt_config_tablet_id.value = db.db_obtener_tablet_id()
        v_admin.visible = True; actualizar_reporte_admin(); page.update()

    def ir_a_gestion_menu(e):
        ocultar_todo()
        txt_mensaje_error_gestion.value = "" 
        v_gestion_menu.visible = True
        refrescar_lista_gestion()
        page.update()

    # NUEVA FUNCIÓN: Para ir a la pantalla de credenciales
    def ir_a_credenciales(e):
        ocultar_todo()
        txt_nuevo_usr.value = ""
        txt_nuevo_pwd.value = ""
        txt_mensaje_credenciales.value = ""
        v_credenciales.visible = True
        page.update()

    def ir_a_pedido(e):
        ocultar_todo(); estado["mesa"] = e.control.data
        txt_titulo_mesa.value = f"MESA #{estado['mesa']}"
        v_pedido.visible = True; mostrar_mensaje_central("¡Bienvenido!\nSelecciona productos.", "blue")
        refrescar_ticket(); page.update()

    # --- SEGURIDAD ID Y CREDENCIALES ---
    def validar_y_guardar_id(e):
        valor = txt_config_tablet_id.value
        if valor.isdigit() and int(valor) > 0:
            id_final = valor.zfill(2)
            db.db_actualizar_tablet_id(id_final)
            txt_config_tablet_id.value = id_final
            page.snack_bar = ft.SnackBar(ft.Text(f"ID actualizado a: {id_final}"), bgcolor="green")
            page.snack_bar.open = True
        else:
            page.snack_bar = ft.SnackBar(ft.Text("Error: Ingresa un número válido mayor a 0"), bgcolor="red")
            page.snack_bar.open = True
        page.update()

    # NUEVA FUNCIÓN: Lógica de guardado con mensajes en pantalla
    def guardar_nuevas_credenciales(e):
        txt_mensaje_credenciales.value = ""
        if not txt_nuevo_usr.value or not txt_nuevo_pwd.value:
            txt_mensaje_credenciales.value = "⚠️ Completa ambos campos"
            txt_mensaje_credenciales.color = "red"
            page.update()
            return
        
        db.db_actualizar_credenciales(txt_nuevo_usr.value, txt_nuevo_pwd.value)
        txt_mensaje_credenciales.value = "¡Usuario administrador actualizado correctamente!"
        txt_mensaje_credenciales.color = "green"
        txt_nuevo_usr.value = ""
        txt_nuevo_pwd.value = ""
        page.update()

    def mostrar_mensaje_central(texto, color_texto):
        grid_prods.controls.clear()
        grid_prods.controls.append(ft.Column([ft.Container(height=100), ft.Row([ft.Text(texto, size=22, color=color_texto, weight="bold", text_align="center")], alignment=ft.MainAxisAlignment.CENTER)], horizontal_alignment=ft.CrossAxisAlignment.CENTER, width=700))
        page.update()

    # --- LÓGICA DE PEDIDOS ---
    def refrescar_ticket():
        col_ticket.controls.clear(); total = 0
        for item in cuentas[estado["mesa"]]:
            sub = item["p"] * item["q"]; total += sub
            icono = ft.Text(" ✔ ", color="green") if item["enviado"] else ft.TextButton(content=ft.Text(" X ", color="red", weight="bold"), on_click=lambda e, n=item["n"]: quitar_item(n))
            col_ticket.controls.append(ft.Row([icono, ft.Text(f"{item['q']}x {item['n']}", expand=True), ft.Text(f"${sub}")]))
        txt_total.value = f"TOTAL: ${total}"; page.update()

    def agregar_item(n, p, d):
        m = estado["mesa"]; found = False
        for it in cuentas[m]:
            if it["n"] == n and not it["enviado"]:
                it["q"] += 1; found = True; db.db_guardar_item_activo(m, it); break
        if not found:
            nuevo = {"n": n, "p": p, "d": d, "q": 1, "enviado": False}
            cuentas[m].append(nuevo); db.db_guardar_item_activo(m, nuevo)
        refrescar_ticket()

    def quitar_item(nombre):
        m = estado["mesa"]
        for i, it in enumerate(cuentas[m]):
            if it["n"] == nombre and not it["enviado"]:
                db.db_remover_item_activo(m, nombre)
                if it["q"] > 1: it["q"] -= 1
                else: cuentas[m].pop(i)
                break
        refrescar_ticket()

    def enviar_comanda(e):
        m_id = estado["mesa"]; nuevos = [i for i in cuentas[m_id] if not i["enviado"]]
        if not nuevos: mostrar_mensaje_central("AVISO:\nNo hay productos nuevos.", "orange"); return
        db.db_marcar_enviados(m_id)
        for i in cuentas[m_id]: i["enviado"] = True
        refrescar_ticket(); mostrar_mensaje_central("¡ORDEN ENVIADA!", "green")

    # --- PAGO Y CIERRE ---
    def validar_pago_antes_de_confirmar(e):
        mesa_actual = cuentas[estado["mesa"]]
        if not mesa_actual: mostrar_mensaje_central("ERROR:\nLa cuenta está vacía.", "red"); return
        if any(not i['enviado'] for i in mesa_actual): mostrar_mensaje_central("ADVERTENCIA:\nItems sin enviar a comanda.", "red"); return
        setattr(v_confirmacion, 'visible', True); page.update()

    def finalizar_pago_total(metodo):
        m_id = estado["mesa"]; items = cuentas[m_id]; total = sum(i['p']*i['q'] for i in items)
        db.db_registrar_venta_final(m_id, "\n".join([f"• {i['q']}x {i['n']}" for i in items]), total, metodo)
        db.db_limpiar_mesa(m_id); cuentas[m_id] = []
        ocultar_todo(); txt_mensaje_despedida.value = f"¡PAGO REGISTRADO!\nMétodo: {metodo.upper()}"; v_pago_finalizado.visible = True; page.update()

    def ejecutar_cierre_final(e):
        ventas = db.db_obtener_ventas_activas()
        total = sum(v[2] for v in ventas); efe = sum(v[2] for v in ventas if v[4].lower() == "efectivo"); tar = sum(v[2] for v in ventas if v[4].lower() == "tarjeta")
        rp.generar_excel_cierre(ventas, total, efe, tar, db.db_obtener_tablet_id())
        db.db_ejecutar_cierre_caja()
        v_confirm_cierre.visible = False; txt_resumen_cierre_total.value = f"INGRESO TOTAL: ${total}"; txt_resumen_efectivo.value = f"EFECTIVO: ${efe}"; txt_resumen_tarjeta.value = f"TARJETA: ${tar}"
        txt_resumen_cierre_fecha.value = f"FECHA Y HORA: {datetime.now()}"; v_resumen_cierre.visible = True; page.update()

    # --- VALIDACIÓN EN LÍNEA PARA PRODUCTOS ---
    def intentar_agregar_producto(e):
        txt_mensaje_error_gestion.value = ""
        
        if not txt_nom.value or not txt_pre.value:
            txt_mensaje_error_gestion.value = "Completa todos los campos (Nombre y Precio)"
            txt_mensaje_error_gestion.color = "red"
            page.update()
            return
            
        try:
            float(txt_pre.value)
        except ValueError:
            txt_mensaje_error_gestion.value = "El precio debe ser un número válido"
            txt_mensaje_error_gestion.color = "red"
            page.update()
            return

        db.db_agregar_producto(txt_nom.value, txt_pre.value, dd_cat.value, dd_dest.value)
        txt_nom.value = ""
        txt_pre.value = ""
        refrescar_lista_gestion()
        
        txt_mensaje_error_gestion.value = "¡Producto añadido con éxito!"
        txt_mensaje_error_gestion.color = "green"
        page.update()

    def intentar_actualizar_precio(idx, valor_texto):
        txt_mensaje_error_gestion.value = ""
        if not valor_texto:
            txt_mensaje_error_gestion.value = "El precio no puede estar vacío"
            txt_mensaje_error_gestion.color = "red"
            page.update()
            return
            
        try:
            precio_valido = float(valor_texto)
            db.db_actualizar_precio_producto(idx, precio_valido)
            refrescar_lista_gestion()
            txt_mensaje_error_gestion.value = "¡Precio actualizado!"
            txt_mensaje_error_gestion.color = "green"
            page.update()
        except ValueError:
            txt_mensaje_error_gestion.value = "El precio debe ser un número"
            txt_mensaje_error_gestion.color = "red"
            page.update()

    # --- UI COMPONENTS ---
    v_login = ft.Container(content=ft.Row([ft.Column([ft.Text("ACCESO ADMIN", size=40, weight="bold"), user_input, pass_input, ft.ElevatedButton("ENTRAR", bgcolor="blue", color="white", width=350, height=50, on_click=intentar_login), ft.TextButton("VOLVER", on_click=ir_a_mesas)], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)], alignment=ft.MainAxisAlignment.CENTER), visible=False, expand=True, bgcolor="white")

    col_reportes_dia, txt_ingreso_total_dia = ft.Column(scroll="always", expand=True), ft.Text("", size=25, weight="bold", color="green")
    
    # EL BOTÓN CREDENCIALES AHORA LLAMA A ir_a_credenciales
    v_admin = ft.Container(content=ft.Column([ft.Row([ft.Text("REPORTE DIARIO", size=30, weight="bold"), ft.Row([txt_config_tablet_id, ft.ElevatedButton("GUARDAR ID", on_click=validar_y_guardar_id), ft.ElevatedButton("CAMBIAR CONTRASEÑA", on_click=ir_a_credenciales), ft.ElevatedButton("PRODUCTOS", bgcolor="blue", color="white", on_click=ir_a_gestion_menu), ft.ElevatedButton("SALIR APP", bgcolor="red", color="white", on_click=salir_de_la_app), ft.ElevatedButton("CIERRE", bgcolor="orange", color="white", on_click=lambda _: [setattr(v_confirm_cierre, 'visible', True), page.update()]), ft.TextButton("SALIR", on_click=ir_a_mesas)])], alignment="spaceBetween"), ft.Divider(), col_reportes_dia, ft.Divider(), ft.Row([txt_ingreso_total_dia], alignment="center")]), visible=False, expand=True, padding=30, bgcolor="white")

    txt_nom, txt_pre = ft.TextField(label="Nombre", width=250), ft.TextField(label="Precio", width=150)
    dd_cat = ft.Dropdown(label="Categoría", width=200, options=[ft.dropdown.Option("BEBIDAS"), ft.dropdown.Option("COMIDA"), ft.dropdown.Option("POSTRES")], value="BEBIDAS")
    dd_dest = ft.Dropdown(label="Destino", width=200, options=[ft.dropdown.Option("BARRA"), ft.dropdown.Option("COCINA")], value="BARRA")
    col_lista_prods = ft.Column(scroll="always", expand=True)
    
    v_gestion_menu = ft.Container(content=ft.Column([
        ft.Row([
            ft.Text("GESTIONAR PRODUCTOS", size=30, weight="bold"), 
            ft.ElevatedButton("VOLVER", on_click=ir_a_admin),
            txt_mensaje_error_gestion
        ]), 
        ft.Row([
            txt_nom, txt_pre, dd_cat, dd_dest, 
            ft.ElevatedButton("AÑADIR", on_click=intentar_agregar_producto, bgcolor="green", color="white")
        ]), 
        ft.Divider(), 
        col_lista_prods
    ]), visible=False, expand=True, padding=30, bgcolor="white")

    # NUEVA PANTALLA: v_credenciales
    v_credenciales = ft.Container(content=ft.Column([
        ft.Row([
            ft.Text("ACTUALIZAR CREDENCIALES", size=30, weight="bold"), 
            ft.ElevatedButton("VOLVER", on_click=ir_a_admin)
        ]), 
        ft.Divider(),
        ft.Column([
            txt_nuevo_usr, 
            txt_nuevo_pwd, 
            ft.ElevatedButton("GUARDAR CAMBIOS", on_click=guardar_nuevas_credenciales, bgcolor="green", color="white", width=350, height=50),
            txt_mensaje_credenciales
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER), visible=False, expand=True, padding=30, bgcolor="white")

    grid_mesas = ft.GridView(expand=True, runs_count=5, spacing=15)
    for i in range(1, 21): grid_mesas.controls.append(ft.Container(content=ft.Text(f"{i}", color="white", weight="bold"), bgcolor="blue", border_radius=10, padding=20, on_click=ir_a_pedido, data=i))
    v_mesas = ft.Container(content=ft.Column([ft.Row([ft.Text("SALÓN", size=30, weight="bold", expand=True), ft.TextButton("ADMIN", on_click=lambda _: [ocultar_todo(), setattr(v_login, 'visible', True), page.update()])]), grid_mesas]), expand=True, padding=20, bgcolor="white")

    columna_botones_acciones = ft.Column([ft.ElevatedButton("COMANDA", bgcolor="orange", color="white", height=60, on_click=enviar_comanda, width=400), ft.ElevatedButton("PAGAR CUENTA", bgcolor="green", color="white", height=60, on_click=validar_pago_antes_de_confirmar, width=400)])
    txt_titulo_mesa, col_ticket, txt_total, grid_prods = ft.Text("", size=25, weight="bold"), ft.Column(scroll="always", expand=True), ft.Text("TOTAL: $0", size=35, weight="bold", color="green"), ft.Column(expand=True)
    v_pedido = ft.Container(content=ft.Row([ft.Column([ft.TextButton("<- VOLVER", on_click=ir_a_mesas), ft.Row([ft.ElevatedButton("BEBIDAS", on_click=lambda _: filtrar_menu_dinamico("BEBIDAS")), ft.ElevatedButton("COMIDA", on_click=lambda _: filtrar_menu_dinamico("COMIDA")), ft.ElevatedButton("POSTRES", on_click=lambda _: filtrar_menu_dinamico("POSTRES"))]), grid_prods], expand=3), ft.Container(content=ft.Column([txt_titulo_mesa, ft.Divider(), col_ticket, ft.Divider(), txt_total, columna_botones_acciones]), expand=2, bgcolor="#F5F5F5", padding=20, border_radius=15)]), expand=True, visible=False, bgcolor="white")

    v_confirmacion = ft.Container(content=ft.Row([ft.Column([ft.Text("¿CONFIRMAR PAGO?", size=25, weight="bold"), ft.Row([ft.ElevatedButton("SÍ, PAGAR", bgcolor="green", color="white", on_click=lambda _: [col_resumen_final.controls.clear(), [col_resumen_final.controls.append(ft.Text(f"{i['q']}x {i['n']} ... ${i['p']*i['q']}")) for i in cuentas[estado['mesa']]], setattr(v_ticket_final, 'visible', True), setattr(v_confirmacion, 'visible', False), setattr(columna_botones_acciones, 'visible', False), page.update()], width=180, height=60), ft.ElevatedButton("NO", bgcolor="red", color="white", on_click=lambda _: [setattr(v_confirmacion, 'visible', False), page.update()], width=180, height=60)], alignment="center")], alignment="center", horizontal_alignment="center")], alignment="center"), visible=False, expand=True, bgcolor="rgba(255,255,255,0.9)")
    col_resumen_final = ft.Column(scroll="always", expand=True); v_ticket_final = ft.Container(content=ft.Column([ft.Text("TICKET", size=30, weight="bold"), col_resumen_final, ft.ElevatedButton("FINALIZAR", bgcolor="blue", color="white", width=400, height=80, on_click=lambda _: [ocultar_todo(), setattr(v_pago_metodo, 'visible', True), page.update()])], horizontal_alignment="center"), bgcolor="white", visible=False, expand=True, padding=50)
    v_pago_metodo = ft.Container(content=ft.Row([ft.Column([ft.Text("MÉTODO DE PAGO", size=30, weight="bold"), ft.ElevatedButton("EFECTIVO", bgcolor="green", color="white", width=400, height=70, on_click=lambda _: finalizar_pago_total("Efectivo")), ft.ElevatedButton("TARJETA", bgcolor="blue", color="white", width=400, height=70, on_click=lambda _: finalizar_pago_total("Tarjeta"))], alignment="center", horizontal_alignment="center")], alignment="center"), visible=False, expand=True, bgcolor="white")
    v_pago_finalizado = ft.Container(content=ft.Row([ft.Column([ft.Text("GRACIAS", size=40, weight="bold"), txt_mensaje_despedida := ft.Text("", size=22, text_align="center"), ft.ElevatedButton("CERRAR", bgcolor="blue", color="white", width=350, height=70, on_click=ir_a_mesas)], alignment="center", horizontal_alignment="center")], alignment="center"), visible=False, expand=True, bgcolor="white")
    v_confirm_cierre = ft.Container(content=ft.Row([ft.Column([ft.Text("¡ADVERTENCIA!", size=30, weight="bold", color="red"), ft.Text("Se resetearán los ingresos."), ft.Row([ft.ElevatedButton("SÍ", bgcolor="green", color="white", on_click=ejecutar_cierre_final, width=150), ft.ElevatedButton("NO", bgcolor="red", color="white", on_click=lambda _: [setattr(v_confirm_cierre, 'visible', False), page.update()], width=150)], alignment="center")], alignment="center", horizontal_alignment="center")], alignment="center"), visible=False, expand=True, bgcolor="rgba(255,255,255,0.95)")
    v_resumen_cierre = ft.Container(content=ft.Row([ft.Column([ft.Text("RESUMEN CIERRE", size=30, weight="bold"), txt_resumen_cierre_total := ft.Text("", size=30, color="green", weight="bold"), txt_resumen_efectivo := ft.Text(""), txt_resumen_tarjeta := ft.Text(""), txt_resumen_cierre_fecha := ft.Text("", size=18, weight="bold"), txt_archivo_creado := ft.Text("", size=12, italic=True), ft.ElevatedButton("CERRAR", on_click=ir_a_admin)], alignment="center", horizontal_alignment="center")], alignment="center"), visible=False, expand=True, bgcolor="white")

    # --- REFRESH FUNCTIONS ---
    def actualizar_reporte_admin():
        ventas = db.db_obtener_ventas_activas(); col_reportes_dia.controls.clear()
        for v in ventas:
            col_reportes_dia.controls.append(ft.Container(content=ft.Column([ft.Row([ft.Text(f"MESA {v[0]}", weight="bold", size=18), ft.Text(f"PAGO: {v[4].upper()}", color="blue", weight="bold")], alignment="spaceBetween"), ft.Text("Productos:", weight="bold"), ft.Text(v[1], italic=True, color="grey"), ft.Row([ft.Text(f"Total: ${v[2]}", color="green", weight="bold"), ft.Text(f"Hora: {v[3]}", size=12)], alignment="spaceBetween")]), padding=15, border=ft.border.all(1, "grey"), border_radius=10, margin=ft.margin.only(bottom=10)))
        txt_ingreso_total_dia.value = f"TOTAL EN CAJA: ${sum(x[2] for x in ventas)}"; page.update()

    def refrescar_lista_gestion():
        col_lista_prods.controls.clear()
        for p in db.db_obtener_productos():
            tf = ft.TextField(value=str(p[2]), width=100, height=40, text_size=14)
            col_lista_prods.controls.append(ft.Row([ft.Text(f"{p[1]} ({p[3]})", expand=True), tf, ft.TextButton("ACTUALIZAR", on_click=lambda e, idx=p[0], campo=tf: intentar_actualizar_precio(idx, campo.value)), ft.TextButton("BORRAR", on_click=lambda e, idx=p[0]: [db.db_eliminar_producto(idx), refrescar_lista_gestion()], style=ft.ButtonStyle(color="red"))]))
        page.update()

    def filtrar_menu_dinamico(cat):
        grid_prods.controls.clear(); grid = ft.GridView(runs_count=3, spacing=10, max_extent=150)
        for p in [x for x in db.db_obtener_productos() if x[3] == cat]:
            grid.controls.append(ft.ElevatedButton(content=ft.Text(f"{p[1]}\n${p[2]}", text_align="center"), on_click=lambda e, n=p[1], pr=p[2], d=p[4]: agregar_item(n, pr, d), height=80))
        grid_prods.controls.append(grid); page.update()

    # SE AGREGÓ v_credenciales A LA PILA DE VISTAS
    page.add(ft.Stack([v_mesas, v_pedido, v_login, v_admin, v_confirmacion, v_ticket_final, v_confirm_cierre, v_resumen_cierre, v_pago_metodo, v_pago_finalizado, v_gestion_menu, v_credenciales], expand=True))
    ir_a_mesas(None)

if __name__ == "__main__":
    try: ft.app(target=main)
    except Exception as e:
        pass