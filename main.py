import flet as ft
from datetime import datetime
import os
import urllib.request
import database as db
import reports as rp

def main(page: ft.Page):
    # ==========================================
    # 0. CONFIGURACIÓN INICIAL Y CHECKPOINTS
    # ==========================================
    page.title = "POS Restaurante Pro - SUNMI D3"
    page.theme_mode = "light"
    page.padding = ft.padding.only(top=45, bottom=45, left=15, right=15)
    
    txt_estado = ft.Text("Iniciando sistema...", size=24, weight="bold")
    txt_detalle = ft.Text("Por favor espera...", size=16, color="grey")
    
    vista_carga = ft.Container(
        content=ft.Column(
            [
                ft.ProgressRing(width=50, height=50, stroke_width=5),
                ft.Container(height=20),
                txt_estado,
                txt_detalle
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        ),
        expand=True
    )
    
    page.add(vista_carga)
    page.update()

    try:
        txt_estado.value = "Conectando Base de Datos..."
        txt_detalle.value = "Paso 1 de 2"
        page.update()
        db.init_db()

        txt_estado.value = "Cargando configuración..."
        txt_detalle.value = "Paso 2 de 2"
        page.update()
        cuentas = db.db_cargar_estado_inicial()
        estado = {"mesa": 0}
        mesas_bloqueadas = db.db_obtener_mesas_bloqueadas()

    except Exception as e:
        page.clean()
        page.add(ft.Container(
            content=ft.Column([
                ft.Text("ERROR CRÍTICO AL INICIAR", size=30, weight="bold", color="red"),
                ft.Text(f"Detalle: {str(e)}", size=16),
                ft.Text("\nVerifica que la base de datos pos_restaurante.db sea accesible.", size=14, italic=True)
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            expand=True
        ))
        page.update()
        return

    page.clean()

    # ==========================================
    # 1. DECLARACIÓN DE VARIABLES Y CONTROLES
    # ==========================================
    user_input = ft.TextField(label="Usuario", width=350)
    pass_input = ft.TextField(label="Contraseña", password=True, width=350)
    txt_config_tablet_id = ft.TextField(label="ID Tablet", width=120, input_filter=ft.NumbersOnlyInputFilter(), text_align="center")
    txt_config_num_mesas = ft.TextField(label="Núm. Mesas", width=150, input_filter=ft.NumbersOnlyInputFilter(), text_align="center")
    
    txt_mensaje_error_gestion = ft.Text("", size=18, weight="bold", expand=True, text_align="center")
    txt_nuevo_usr = ft.TextField(label="Nombre Usuario", width=350)
    txt_nuevo_pwd = ft.TextField(label="Nueva Contraseña", password=True, width=350)
    txt_mensaje_credenciales = ft.Text("", size=18, weight="bold", text_align="center")
    user_input_bloqueo = ft.TextField(label="Usuario Admin", width=350)
    pass_input_bloqueo = ft.TextField(label="Contraseña", password=True, width=350)
    col_lista_archivos = ft.Column(scroll="always", expand=1)
    contenedor_tabla_excel = ft.Column(scroll="always", expand=3)
    grid_mesas = ft.GridView(expand=True, runs_count=5, spacing=15)
    grid_bloqueo = ft.GridView(expand=True, runs_count=5, spacing=15)
    col_reportes_dia = ft.Column(scroll="always", expand=True)
    txt_ingreso_total_dia = ft.Text("", size=25, weight="bold", color="green")
    
    txt_nom = ft.TextField(label="Nombre", width=250)
    txt_pre = ft.TextField(label="Precio", width=120)
    
    lista_cat = db.db_obtener_categorias()
    lista_dest = db.db_obtener_destinos()
    
    dd_cat = ft.Dropdown(label="Categoría", width=180, options=[ft.dropdown.Option(c) for c in lista_cat], value=lista_cat[0] if lista_cat else None)
    dd_dest = ft.Dropdown(label="Destino", width=150, options=[ft.dropdown.Option(d) for d in lista_dest], value=lista_dest[0] if lista_dest else None)
    
    col_lista_prods = ft.Column(scroll="always", expand=True)
    txt_titulo_mesa = ft.Text("", size=25, weight="bold")
    col_ticket = ft.Column(scroll="always", expand=True)
    txt_total = ft.Text("TOTAL: $0", size=35, weight="bold", color="green")
    grid_prods = ft.Column(expand=True)
    
    txt_mixto_total = ft.Text("TOTAL A PAGAR: $0", size=30, weight="bold", color="blue")
    txt_mixto_efectivo = ft.TextField(label="Monto entregado en Efectivo", width=250, text_size=20)
    txt_mixto_tarjeta = ft.TextField(label="Restante a cobrar en Tarjeta", width=250, text_size=20, read_only=True, value="0.0")
    txt_mixto_error = ft.Text("", color="red", weight="bold")

    v_login = v_admin = v_gestion_menu = v_credenciales = v_visor_reportes = v_bloqueo_mesas = v_login_bloqueo = None
    v_mesas = v_pedido = v_confirmacion = v_ticket_final = v_pago_metodo = v_pago_finalizado = v_confirm_cierre = v_resumen_cierre = None
    v_pago_mixto = None 
    columna_botones_acciones = None

    # =======================================================
    # 1.5 LÓGICA DE CARGA DE LOGO (VÍA URL + BORRADO)
    # =======================================================
    txt_logo_url = ft.TextField(label="Enlace (URL) de la imagen", width=350)
    txt_estado_descarga = ft.Text("")

    def guardar_logo_url(e):
        url = txt_logo_url.value.strip()
        if url:
            txt_estado_descarga.value = "Descargando..."
            txt_estado_descarga.color = "blue"
            page.update()
            try:
                ruta_db = db.get_db_path()
                base_path = os.path.dirname(ruta_db)
                
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                nombre_archivo = f"logo_restaurante_{timestamp}.png"
                ruta_destino = os.path.join(base_path, nombre_archivo)
                
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req) as response, open(ruta_destino, 'wb') as out_file:
                    out_file.write(response.read())
                
                db.db_actualizar_logo(ruta_destino)
                inicializar_salon() 
                
                dlg_logo.open = False
                page.snack_bar = ft.SnackBar(ft.Text("¡Logo descargado y aplicado exitosamente!"), bgcolor="green")
                page.snack_bar.open = True
                txt_estado_descarga.value = ""
                page.update()
            except Exception as ex:
                txt_estado_descarga.value = f"Error: No se pudo descargar la imagen."
                txt_estado_descarga.color = "red"
                page.update()

    def borrar_logo(e):
        ruta_actual = db.db_obtener_logo()
        if ruta_actual and os.path.exists(ruta_actual):
            try:
                os.remove(ruta_actual)
            except Exception:
                pass
        
        db.db_actualizar_logo("")
        inicializar_salon()
        page.snack_bar = ft.SnackBar(ft.Text("Logo eliminado. Las mesas están limpias."), bgcolor="green")
        page.snack_bar.open = True
        page.update()

    dlg_logo = ft.AlertDialog(
        title=ft.Text("Descargar Logo"),
        content=ft.Column([
            ft.Text("Pega el enlace de internet donde esté alojado tu logo (ej. link directo de Postimages)."),
            txt_logo_url,
            txt_estado_descarga
        ], tight=True),
        actions=[
            ft.TextButton("Descargar", on_click=guardar_logo_url), 
            ft.TextButton("Cancelar", on_click=lambda _: [setattr(dlg_logo, 'open', False), page.update()])
        ]
    )

    # =======================================================
    # 1.6 LÓGICA DE CATEGORÍAS Y DESTINOS
    # =======================================================
    txt_nueva_cat = ft.TextField(label="Nombre de Categoría", width=300)
    txt_nuevo_dest = ft.TextField(label="Nombre de Destino", width=300)
    txt_confirmar_borrar_cat = ft.Text("", size=16, weight="bold")
    txt_confirmar_borrar_dest = ft.Text("", size=16, weight="bold")

    row_categorias_menu = ft.Row(scroll="auto")

    def actualizar_botones_categorias_menu():
        row_categorias_menu.controls.clear()
        for c in db.db_obtener_categorias():
            row_categorias_menu.controls.append(ft.ElevatedButton(c, on_click=lambda e, cat=c: filtrar_menu_dinamico(cat)))
        page.update()

    def guardar_categoria(e):
        if txt_nueva_cat.value:
            cat_val = txt_nueva_cat.value.strip().upper()
            db.db_agregar_categoria(cat_val)
            opciones = db.db_obtener_categorias()
            # === AQUÍ ESTÁ LA CORRECCIÓN CLAVE ===
            dd_cat.options = [ft.dropdown.Option(c) for c in opciones]
            dd_cat.value = cat_val
            actualizar_botones_categorias_menu()
            dlg_cat.open = False
            page.update()

    dlg_cat = ft.AlertDialog(
        title=ft.Text("Añadir Nueva Categoría"),
        content=txt_nueva_cat,
        actions=[ft.TextButton("Guardar", on_click=guardar_categoria), ft.TextButton("Cancelar", on_click=lambda _: [setattr(dlg_cat, 'open', False), page.update()])]
    )

    def abrir_borrar_categoria(e):
        if dd_cat.value:
            txt_confirmar_borrar_cat.value = f"¿Seguro que deseas borrar la categoría '{dd_cat.value}'?\n\n¡ATENCIÓN: Se borrarán TODOS los productos que pertenezcan a esta categoría!"
            dlg_borrar_cat.open = True
            page.update()

    def confirmar_borrar_categoria(e):
        cat_val = dd_cat.value
        if cat_val:
            db.db_eliminar_categoria(cat_val)
            opciones = db.db_obtener_categorias()
            dd_cat.options = [ft.dropdown.Option(c) for c in opciones]
            dd_cat.value = opciones[0] if opciones else None
            actualizar_botones_categorias_menu()
            refrescar_lista_gestion()
            dlg_borrar_cat.open = False
            page.update()

    dlg_borrar_cat = ft.AlertDialog(
        title=ft.Text("Borrar Categoría", color="red"),
        content=txt_confirmar_borrar_cat,
        actions=[
            ft.ElevatedButton("Sí, Borrar", bgcolor="red", color="white", on_click=confirmar_borrar_categoria),
            ft.TextButton("Cancelar", on_click=lambda _: [setattr(dlg_borrar_cat, 'open', False), page.update()])
        ]
    )

    def guardar_destino(e):
        if txt_nuevo_dest.value:
            dest_val = txt_nuevo_dest.value.strip().upper()
            db.db_agregar_destino(dest_val)
            opciones = db.db_obtener_destinos()
            dd_dest.options = [ft.dropdown.Option(d) for d in opciones]
            dd_dest.value = dest_val
            dlg_dest.open = False
            page.update()

    dlg_dest = ft.AlertDialog(
        title=ft.Text("Añadir Nuevo Destino"),
        content=txt_nuevo_dest,
        actions=[ft.TextButton("Guardar", on_click=guardar_destino), ft.TextButton("Cancelar", on_click=lambda _: [setattr(dlg_dest, 'open', False), page.update()])]
    )

    def abrir_borrar_destino(e):
        if dd_dest.value:
            txt_confirmar_borrar_dest.value = f"¿Seguro que deseas borrar el destino '{dd_dest.value}'?\n\n¡ATENCIÓN: Se borrarán TODOS los productos que pertenezcan a este destino!"
            dlg_borrar_dest.open = True
            page.update()

    def confirmar_borrar_destino(e):
        dest_val = dd_dest.value
        if dest_val:
            db.db_eliminar_destino(dest_val)
            opciones = db.db_obtener_destinos()
            dd_dest.options = [ft.dropdown.Option(d) for d in opciones]
            dd_dest.value = opciones[0] if opciones else None
            refrescar_lista_gestion()
            dlg_borrar_dest.open = False
            page.update()

    dlg_borrar_dest = ft.AlertDialog(
        title=ft.Text("Borrar Destino", color="red"),
        content=txt_confirmar_borrar_dest,
        actions=[
            ft.ElevatedButton("Sí, Borrar", bgcolor="red", color="white", on_click=confirmar_borrar_destino),
            ft.TextButton("Cancelar", on_click=lambda _: [setattr(dlg_borrar_dest, 'open', False), page.update()])
        ]
    )

    col_btns_cat = ft.Column([
        ft.ElevatedButton("+", bgcolor="green", color="white", height=30, width=45, on_click=lambda _: [setattr(txt_nueva_cat, 'value', ''), setattr(dlg_cat, 'open', True), page.update()]),
        ft.ElevatedButton("-", bgcolor="red", color="white", height=30, width=45, on_click=abrir_borrar_categoria)
    ], spacing=2)

    col_btns_dest = ft.Column([
        ft.ElevatedButton("+", bgcolor="green", color="white", height=30, width=45, on_click=lambda _: [setattr(txt_nuevo_dest, 'value', ''), setattr(dlg_dest, 'open', True), page.update()]),
        ft.ElevatedButton("-", bgcolor="red", color="white", height=30, width=45, on_click=abrir_borrar_destino)
    ], spacing=2)

    actualizar_botones_categorias_menu()

    # ==========================================
    # 2. DEFINICIÓN DE FUNCIONES
    # ==========================================
    def ocultar_todo():
        if v_mesas: v_mesas.visible = False
        if v_pedido: v_pedido.visible = False
        if v_login: v_login.visible = False
        if v_login_bloqueo: v_login_bloqueo.visible = False
        if v_admin: v_admin.visible = False
        if v_confirmacion: v_confirmacion.visible = False
        if v_ticket_final: v_ticket_final.visible = False
        if v_confirm_cierre: v_confirm_cierre.visible = False
        if v_resumen_cierre: v_resumen_cierre.visible = False
        if v_pago_metodo: v_pago_metodo.visible = False
        if v_pago_finalizado: v_pago_finalizado.visible = False
        if v_gestion_menu: v_gestion_menu.visible = False
        if v_credenciales: v_credenciales.visible = False
        if v_visor_reportes: v_visor_reportes.visible = False 
        if v_bloqueo_mesas: v_bloqueo_mesas.visible = False
        if v_pago_mixto: v_pago_mixto.visible = False
        if columna_botones_acciones: columna_botones_acciones.visible = True

    def inicializar_salon():
        grid_mesas.controls.clear()
        num_mesas = db.db_obtener_num_mesas()
        logo_path = db.db_obtener_logo()
        
        for i in range(1, num_mesas + 1):
            if i not in cuentas:
                cuentas[i] = [] 
            
            color_fondo = "blue"
            if i in mesas_bloqueadas:
                color_fondo = "grey"
            elif len(cuentas[i]) > 0:
                color_fondo = "orange"
                
            contenido_mesa = [ft.Text(f"{i}", color="white", weight="bold", size=22)]
            
            if logo_path and os.path.exists(logo_path):
                contenido_mesa.append(ft.Image(src=logo_path, width=70, height=70, fit="contain"))
                
            grid_mesas.controls.append(
                ft.Container(
                    content=ft.Column(contenido_mesa, alignment="center", horizontal_alignment="center"), 
                    bgcolor=color_fondo, border_radius=10, padding=10, on_click=ir_a_pedido, data=i
                )
            )

    def ir_a_mesas(e):
        ocultar_todo()
        user_input.value = ""; pass_input.value = ""
        user_input_bloqueo.value = ""; pass_input_bloqueo.value = ""
        v_mesas.visible = True
        inicializar_salon()
        page.update()

    def intentar_login(e):
        usr_bd, pwd_bd = db.db_obtener_credenciales()
        if user_input.value == usr_bd and pass_input.value == pwd_bd:
            ir_a_admin(None)
        else:
            page.snack_bar = ft.SnackBar(ft.Text("Usuario o contraseña incorrectos"), bgcolor="red")
            page.snack_bar.open = True
            page.update()

    def ir_a_login_bloqueo(e):
        ocultar_todo()
        user_input_bloqueo.value = ""
        pass_input_bloqueo.value = ""
        v_login_bloqueo.visible = True
        page.update()

    def intentar_login_bloqueo(e):
        usr_bd, pwd_bd = db.db_obtener_credenciales()
        if user_input_bloqueo.value == usr_bd and pass_input_bloqueo.value == pwd_bd:
            ir_a_bloqueo_mesas(None)
        else:
            page.snack_bar = ft.SnackBar(ft.Text("Usuario o contraseña incorrectos"), bgcolor="red")
            page.snack_bar.open = True
            page.update()

    def ir_a_admin(e):
        ocultar_todo()
        txt_config_tablet_id.value = db.db_obtener_tablet_id()
        v_admin.visible = True
        actualizar_reporte_admin()
        page.update()

    def ir_a_gestion_menu(e):
        ocultar_todo()
        txt_mensaje_error_gestion.value = "" 
        v_gestion_menu.visible = True
        refrescar_lista_gestion()
        page.update()

    def ir_a_credenciales(e):
        ocultar_todo()
        txt_nuevo_usr.value = ""
        txt_nuevo_pwd.value = ""
        txt_mensaje_credenciales.value = ""
        v_credenciales.visible = True
        page.update()

    def toggle_bloqueo_mesa(e):
        m_id = e.control.data
        if m_id in mesas_bloqueadas:
            mesas_bloqueadas.remove(m_id)
        else:
            mesas_bloqueadas.append(m_id)
        db.db_actualizar_mesas_bloqueadas(mesas_bloqueadas)
        refrescar_grid_bloqueo()

    def refrescar_grid_bloqueo():
        grid_bloqueo.controls.clear()
        num_mesas = db.db_obtener_num_mesas()
        for i in range(1, num_mesas + 1):
            color = "red" if i in mesas_bloqueadas else "green"
            estado_txt = "BLOQUEADA" if i in mesas_bloqueadas else "LIBRE"
            grid_bloqueo.controls.append(
                ft.Container(content=ft.Column([ft.Text(f"MESA {i}", color="white", weight="bold", size=20), ft.Text(estado_txt, color="white", size=12)], alignment="center", horizontal_alignment="center"), 
                             bgcolor=color, border_radius=10, padding=10, on_click=toggle_bloqueo_mesa, data=i)
            )
        page.update()

    def ir_a_bloqueo_mesas(e):
        ocultar_todo()
        txt_config_num_mesas.value = str(db.db_obtener_num_mesas())
        refrescar_grid_bloqueo()
        v_bloqueo_mesas.visible = True
        page.update()

    def mostrar_contenido_excel(ruta):
        datos = rp.leer_excel(ruta)
        contenedor_tabla_excel.controls.clear()
        if not datos:
            contenedor_tabla_excel.controls.append(ft.Text("⚠️ Error al leer el archivo o archivo vacío.", color="red"))
        else:
            max_cols = len(datos[0]) if datos else 5
            columnas = [ft.DataColumn(ft.Text(f"Col {i+1}", weight="bold")) for i in range(max_cols)]
            filas_dt = []
            for row in datos:
                row_limpia = row[:max_cols] + [""] * (max_cols - len(row))
                celdas = [ft.DataCell(ft.Text(str(c))) for c in row_limpia]
                filas_dt.append(ft.DataRow(cells=celdas))
            
            tabla = ft.DataTable(columns=columnas, rows=filas_dt, heading_row_color="black12", data_row_max_height=float("inf"), data_row_min_height=60)
            contenedor_tabla_excel.controls.append(ft.Row([tabla], scroll="always"))
        page.update()

    def ir_a_visor_reportes(e):
        ocultar_todo()
        col_lista_archivos.controls.clear()
        contenedor_tabla_excel.controls.clear()
        contenedor_tabla_excel.controls.append(ft.Text("Selecciona un reporte de la lista para visualizarlo.", color="grey"))
        base_path = os.path.dirname(db.get_db_path())
        ruta_reportes = os.path.join(base_path, "Reportes_Cierre")
        if os.path.exists(ruta_reportes):
            archivos = [f for f in os.listdir(ruta_reportes) if f.endswith('.xlsx')]
            archivos.sort(reverse=True)
            if archivos:
                for arch in archivos:
                    ruta_completa = os.path.join(ruta_reportes, arch)
                    btn = ft.ElevatedButton(arch, on_click=lambda e, r=ruta_completa: mostrar_contenido_excel(r), width=300)
                    col_lista_archivos.controls.append(btn)
            else:
                col_lista_archivos.controls.append(ft.Text("No hay reportes generados."))
        else:
            col_lista_archivos.controls.append(ft.Text("Carpeta no encontrada. Aún no se han hecho cortes."))
        v_visor_reportes.visible = True
        page.update()

    def mostrar_mensaje_central(texto, color_texto):
        grid_prods.controls.clear()
        grid_prods.controls.append(ft.Column([ft.Container(height=100), ft.Row([ft.Text(texto, size=22, color=color_texto, weight="bold", text_align="center")], alignment=ft.MainAxisAlignment.CENTER)], horizontal_alignment=ft.CrossAxisAlignment.CENTER, width=700))
        page.update()

    def refrescar_ticket():
        col_ticket.controls.clear(); total = 0
        for item in cuentas[estado["mesa"]]:
            sub = item["p"] * item["q"]; total += sub
            icono = ft.Text(" ✔ ", color="green") if item["enviado"] else ft.TextButton(content=ft.Text(" X ", color="red", weight="bold"), on_click=lambda e, n=item["n"]: quitar_item(n))
            col_ticket.controls.append(ft.Row([icono, ft.Text(f"{item['q']}x {item['n']}", expand=True), ft.Text(f"${sub}")]))
        txt_total.value = f"TOTAL: ${total}"; page.update()

    def ir_a_pedido(e):
        m_id = e.control.data
        if m_id in mesas_bloqueadas:
            page.snack_bar = ft.SnackBar(ft.Text(f"Acceso Denegado: La MESA {m_id} está bloqueada.", color="white"), bgcolor="red")
            page.snack_bar.open = True
            page.update()
            return
        ocultar_todo(); estado["mesa"] = m_id
        txt_titulo_mesa.value = f"MESA #{estado['mesa']}"
        v_pedido.visible = True
        mostrar_mensaje_central("¡Bienvenido!\nSelecciona productos.", "blue")
        refrescar_ticket()
        page.update()

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

    def guardar_num_mesas(e):
        n_mesas = txt_config_num_mesas.value
        if n_mesas.isdigit() and int(n_mesas) > 0:
            mesas_final = int(n_mesas)
            db.db_actualizar_num_mesas(mesas_final)
            txt_config_num_mesas.value = str(mesas_final)
            
            inicializar_salon()
            refrescar_grid_bloqueo()
            
            page.snack_bar = ft.SnackBar(ft.Text(f"Ajustes Guardados. El salón ahora tiene {mesas_final} mesas."), bgcolor="green")
            page.snack_bar.open = True
        else:
            page.snack_bar = ft.SnackBar(ft.Text("Error: Ingresa un número de mesas válido"), bgcolor="red")
            page.snack_bar.open = True
        page.update()

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

    def actualizar_tarjeta_mixto(e):
        try:
            m_id = estado["mesa"]
            total = sum(i['p']*i['q'] for i in cuentas[m_id])
            efe = 0.0 if txt_mixto_efectivo.value == "" else float(txt_mixto_efectivo.value)
            
            if efe > total or efe < 0:
                txt_mixto_error.value = "⚠️ El efectivo no puede ser mayor al total"
                txt_mixto_tarjeta.value = "0.0"
            else:
                txt_mixto_error.value = ""
                txt_mixto_tarjeta.value = str(round(total - efe, 2))
        except ValueError:
            txt_mixto_error.value = "⚠️ Ingresa un número válido"
            txt_mixto_tarjeta.value = "0.0"
        page.update()

    txt_mixto_efectivo.on_change = actualizar_tarjeta_mixto

    def ir_a_pago_mixto(e):
        ocultar_todo()
        m_id = estado["mesa"]
        total = sum(i['p']*i['q'] for i in cuentas[m_id])
        txt_mixto_total.value = f"TOTAL A PAGAR: ${total}"
        txt_mixto_efectivo.value = ""
        txt_mixto_tarjeta.value = str(total)
        txt_mixto_error.value = ""
        v_pago_mixto.visible = True
        page.update()

    def confirmar_pago_mixto(e):
        try:
            m_id = estado["mesa"]
            total = sum(i['p']*i['q'] for i in cuentas[m_id])
            if txt_mixto_error.value != "": return
            
            efe = float(txt_mixto_efectivo.value) if txt_mixto_efectivo.value else 0.0
            tar = float(txt_mixto_tarjeta.value)
            
            if round(efe + tar, 2) != round(total, 2):
                txt_mixto_error.value = "⚠️ Los montos no cuadran con el total"
                page.update(); return
                
            metodo_string = f"Mixto:{efe}:{tar}"
            db.db_registrar_venta_final(m_id, "\n".join([f"• {i['q']}x {i['n']}" for i in cuentas[m_id]]), total, metodo_string)
            db.db_limpiar_mesa(m_id)
            cuentas[m_id] = []
            
            ocultar_todo()
            txt_mensaje_despedida.value = f"¡PAGO REGISTRADO!\nMixto (Efe: ${efe} | Tar: ${tar})"
            v_pago_finalizado.visible = True
            page.update()
        except Exception as ex:
            txt_mixto_error.value = "⚠️ Error en los datos ingresados"
            page.update()

    def ejecutar_cierre_final(e):
        try:
            ventas = db.db_obtener_ventas_activas()
            total_caja = sum(v[2] for v in ventas)
            efe = 0.0
            tar = 0.0
            ventas_limpias = []
            
            for v in ventas:
                metodo = v[4]
                if metodo.lower() == "efectivo":
                    efe += v[2]
                    ventas_limpias.append(v)
                elif metodo.lower() == "tarjeta":
                    tar += v[2]
                    ventas_limpias.append(v)
                elif metodo.startswith("Mixto:"):
                    partes = metodo.split(":")
                    efe += float(partes[1])
                    tar += float(partes[2])
                    texto_metodo = "Mixto"
                    ventas_limpias.append((v[0], v[1], v[2], v[3], texto_metodo))
                else:
                    ventas_limpias.append(v)

            rp.generar_excel_cierre(ventas_limpias, total_caja, efe, tar, db.db_obtener_tablet_id())
            db.db_ejecutar_cierre_caja()
            
            v_confirm_cierre.visible = False
            txt_resumen_cierre_total.value = f"INGRESO TOTAL: ${total_caja}"
            txt_resumen_efectivo.value = f"EFECTIVO: ${efe}"
            txt_resumen_tarjeta.value = f"TARJETA: ${tar}"
            txt_resumen_cierre_fecha.value = f"FECHA Y HORA: {datetime.now()}"
            v_resumen_cierre.visible = True
            page.update()
        except Exception as ex:
            v_confirm_cierre.visible = False
            page.snack_bar = ft.SnackBar(ft.Text(f"Error al generar reporte: {str(ex)}"), bgcolor="red")
            page.snack_bar.open = True
            page.update()

    def actualizar_reporte_admin():
        ventas = db.db_obtener_ventas_activas(); col_reportes_dia.controls.clear()
        for v in ventas:
            metodo = v[4]
            if metodo.startswith("Mixto:"):
                partes = metodo.split(":")
                texto_metodo = f"MIXTO (E:${partes[1]} | T:${partes[2]})"
            else:
                texto_metodo = f"PAGO: {metodo.upper()}"
                
            col_reportes_dia.controls.append(ft.Container(content=ft.Column([ft.Row([ft.Text(f"MESA {v[0]}", weight="bold", size=18), ft.Text(texto_metodo, color="blue", weight="bold")], alignment="spaceBetween"), ft.Text("Productos:", weight="bold"), ft.Text(v[1], italic=True, color="grey"), ft.Row([ft.Text(f"Total: ${v[2]}", color="green", weight="bold"), ft.Text(f"Hora: {v[3]}", size=12)], alignment="spaceBetween")]), padding=15, border=ft.border.all(1, "grey"), border_radius=10, margin=ft.margin.only(bottom=10)))
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

    def intentar_agregar_producto(e):
        txt_mensaje_error_gestion.value = ""
        if not txt_nom.value or not txt_pre.value or not dd_cat.value or not dd_dest.value:
            txt_mensaje_error_gestion.value = "Completa todos los campos"
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
        txt_nom.value = ""; txt_pre.value = ""; refrescar_lista_gestion()
        txt_mensaje_error_gestion.value = "¡Producto añadido con éxito!"; txt_mensaje_error_gestion.color = "green"
        page.update()

    def intentar_actualizar_precio(idx, valor_texto):
        txt_mensaje_error_gestion.value = ""
        if not valor_texto:
            txt_mensaje_error_gestion.value = "El precio no puede estar vacío"
            txt_mensaje_error_gestion.color = "red"
            page.update(); return
        try:
            precio_valido = float(valor_texto)
            db.db_actualizar_precio_producto(idx, precio_valido)
            refrescar_lista_gestion()
            txt_mensaje_error_gestion.value = "¡Precio actualizado!"; txt_mensaje_error_gestion.color = "green"
            page.update()
        except ValueError:
            txt_mensaje_error_gestion.value = "El precio debe ser un número"
            txt_mensaje_error_gestion.color = "red"
            page.update()

    # ==========================================
    # 3. CONSTRUCCIÓN DE LA INTERFAZ FINAL
    # ==========================================
    inicializar_salon() 

    columna_botones_acciones = ft.Column([ft.ElevatedButton("COMANDA", bgcolor="orange", color="white", height=60, on_click=enviar_comanda, width=400), ft.ElevatedButton("PAGAR CUENTA", bgcolor="green", color="white", height=60, on_click=validar_pago_antes_de_confirmar, width=400)])
    
    page.overlay.extend([dlg_cat, dlg_dest, dlg_borrar_cat, dlg_borrar_dest, dlg_logo])

    v_login = ft.Container(content=ft.Row([ft.Column([ft.Text("ACCESO ADMIN", size=40, weight="bold"), user_input, pass_input, ft.ElevatedButton("ENTRAR", bgcolor="blue", color="white", width=350, height=50, on_click=intentar_login), ft.TextButton("VOLVER", on_click=ir_a_mesas)], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)], alignment=ft.MainAxisAlignment.CENTER), visible=False, expand=True, bgcolor="white")
    v_login_bloqueo = ft.Container(content=ft.Row([ft.Column([ft.Text("ACCESO A CONFIGURACIÓN", size=40, weight="bold"), user_input_bloqueo, pass_input_bloqueo, ft.ElevatedButton("ENTRAR", bgcolor="red", color="white", width=350, height=50, on_click=intentar_login_bloqueo), ft.TextButton("VOLVER", on_click=ir_a_mesas)], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)], alignment=ft.MainAxisAlignment.CENTER), visible=False, expand=True, bgcolor="white")
    
    v_admin = ft.Container(content=ft.Column([ft.Row([ft.Text("REPORTE DIARIO", size=30, weight="bold"), ft.Row([txt_config_tablet_id, ft.ElevatedButton("GUARDAR ID", on_click=validar_y_guardar_id), ft.ElevatedButton("VER REPORTES", bgcolor="green", color="white", on_click=ir_a_visor_reportes), ft.ElevatedButton("CAMBIAR CONTRASEÑA", on_click=ir_a_credenciales), ft.ElevatedButton("PRODUCTOS", bgcolor="blue", color="white", on_click=ir_a_gestion_menu), ft.ElevatedButton("CIERRE", bgcolor="orange", color="white", on_click=lambda _: [setattr(v_confirm_cierre, 'visible', True), page.update()]), ft.TextButton("SALIR", on_click=ir_a_mesas)], scroll="auto")], alignment="spaceBetween"), ft.Divider(), col_reportes_dia, ft.Divider(), ft.Row([txt_ingreso_total_dia], alignment="center")]), visible=False, expand=True, padding=30, bgcolor="white")
    
    v_gestion_menu = ft.Container(content=ft.Column([
        ft.Row([ft.Text("GESTIONAR PRODUCTOS", size=30, weight="bold"), ft.ElevatedButton("VOLVER", on_click=ir_a_admin), txt_mensaje_error_gestion]), 
        ft.Row([
            txt_nom, txt_pre, 
            dd_cat, col_btns_cat, 
            dd_dest, col_btns_dest, 
            ft.ElevatedButton("AÑADIR", on_click=intentar_agregar_producto, bgcolor="green", color="white", height=62)
        ], vertical_alignment=ft.CrossAxisAlignment.CENTER), 
        ft.Divider(), col_lista_prods
    ]), visible=False, expand=True, padding=30, bgcolor="white")
    
    v_credenciales = ft.Container(content=ft.Column([ft.Row([ft.Text("ACTUALIZAR CREDENCIALES", size=30, weight="bold"), ft.ElevatedButton("VOLVER", on_click=ir_a_admin)]), ft.Divider(), ft.Column([txt_nuevo_usr, txt_nuevo_pwd, ft.ElevatedButton("GUARDAR CAMBIOS", on_click=guardar_nuevas_credenciales, bgcolor="green", color="white", width=350, height=50), txt_mensaje_credenciales], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)], horizontal_alignment=ft.CrossAxisAlignment.CENTER), visible=False, expand=True, padding=30, bgcolor="white")
    v_visor_reportes = ft.Container(content=ft.Column([ft.Row([ft.Text("HISTORIAL DE CORTES (EXCEL)", size=30, weight="bold"), ft.ElevatedButton("VOLVER", on_click=ir_a_admin)]), ft.Divider(), ft.Row([col_lista_archivos, ft.VerticalDivider(), contenedor_tabla_excel], expand=True, vertical_alignment=ft.CrossAxisAlignment.START)]), visible=False, expand=True, padding=30, bgcolor="white")
    
    v_bloqueo_mesas = ft.Container(content=ft.Column([
        ft.Row([ft.Text("CONFIGURACIÓN DE MESAS", size=30, weight="bold"), ft.ElevatedButton("VOLVER AL SALÓN", on_click=ir_a_mesas)], alignment="spaceBetween"), 
        ft.Row([
            txt_config_num_mesas, 
            ft.ElevatedButton("ACTUALIZAR CANTIDAD", bgcolor="blue", color="white", on_click=guardar_num_mesas),
            ft.ElevatedButton("CAMBIAR LOGO", bgcolor="purple", color="white", on_click=lambda _: [setattr(txt_logo_url, 'value', ''), setattr(txt_estado_descarga, 'value', ''), setattr(dlg_logo, 'open', True), page.update()]),
            ft.ElevatedButton("BORRAR LOGO", bgcolor="red", color="white", on_click=borrar_logo)
        ], scroll="auto"),
        ft.Text("Toca una mesa para cambiar su estado. Verde = Libre | Rojo = Bloqueada", color="grey"), 
        ft.Divider(), 
        grid_bloqueo
    ]), visible=False, expand=True, padding=30, bgcolor="white")
    
    v_mesas = ft.Container(content=ft.Column([ft.Row([ft.Text("SALÓN", size=30, weight="bold"), ft.ElevatedButton("CONFIGURACIÓN DE MESAS", bgcolor="red", color="white", on_click=ir_a_login_bloqueo), ft.Container(expand=True), ft.TextButton("ADMIN", on_click=lambda _: [ocultar_todo(), setattr(v_login, 'visible', True), page.update()])]), grid_mesas]), expand=True, padding=20, bgcolor="white")
    
    v_pedido = ft.Container(content=ft.Row([ft.Column([ft.TextButton("<- VOLVER", on_click=ir_a_mesas), row_categorias_menu, grid_prods], expand=3), ft.Container(content=ft.Column([txt_titulo_mesa, ft.Divider(), col_ticket, ft.Divider(), txt_total, columna_botones_acciones]), expand=2, bgcolor="#F5F5F5", padding=20, border_radius=15)]), expand=True, visible=False, bgcolor="white")
    
    v_confirmacion = ft.Container(content=ft.Row([ft.Column([ft.Text("¿CONFIRMAR PAGO?", size=25, weight="bold"), ft.Row([ft.ElevatedButton("SÍ, PAGAR", bgcolor="green", color="white", on_click=lambda _: [col_resumen_final.controls.clear(), [col_resumen_final.controls.append(ft.Text(f"{i['q']}x {i['n']} ... ${i['p']*i['q']}")) for i in cuentas[estado['mesa']]], setattr(v_ticket_final, 'visible', True), setattr(v_confirmacion, 'visible', False), setattr(columna_botones_acciones, 'visible', False), page.update()], width=180, height=60), ft.ElevatedButton("NO", bgcolor="red", color="white", on_click=lambda _: [setattr(v_confirmacion, 'visible', False), page.update()], width=180, height=60)], alignment="center")], alignment="center", horizontal_alignment="center")], alignment="center"), visible=False, expand=True, bgcolor="rgba(255,255,255,0.9)")
    col_resumen_final = ft.Column(scroll="always", expand=True)
    v_ticket_final = ft.Container(content=ft.Column([ft.Text("TICKET", size=30, weight="bold"), col_resumen_final, ft.ElevatedButton("FINALIZAR", bgcolor="blue", color="white", width=400, height=80, on_click=lambda _: [ocultar_todo(), setattr(v_pago_metodo, 'visible', True), page.update()])], horizontal_alignment="center"), bgcolor="white", visible=False, expand=True, padding=50)
    v_pago_metodo = ft.Container(content=ft.Row([ft.Column([ft.Text("MÉTODO DE PAGO", size=30, weight="bold"), ft.ElevatedButton("EFECTIVO", bgcolor="green", color="white", width=400, height=70, on_click=lambda _: finalizar_pago_total("Efectivo")), ft.ElevatedButton("TARJETA", bgcolor="blue", color="white", width=400, height=70, on_click=lambda _: finalizar_pago_total("Tarjeta")), ft.ElevatedButton("AMBAS (Mixto)", bgcolor="orange", color="white", width=400, height=70, on_click=ir_a_pago_mixto)], alignment="center", horizontal_alignment="center")], alignment="center"), visible=False, expand=True, bgcolor="white")
    v_pago_mixto = ft.Container(content=ft.Row([ft.Column([ft.Text("PAGO DIVIDIDO", size=30, weight="bold"), txt_mixto_total, ft.Divider(), ft.Row([txt_mixto_efectivo, ft.Text("+", size=30, weight="bold"), txt_mixto_tarjeta], alignment="center"), txt_mixto_error, ft.Divider(), ft.ElevatedButton("CONFIRMAR PAGO", bgcolor="green", color="white", width=400, height=60, on_click=confirmar_pago_mixto), ft.ElevatedButton("CANCELAR", bgcolor="red", color="white", width=400, height=60, on_click=lambda _: [setattr(v_pago_mixto, 'visible', False), setattr(v_pago_metodo, 'visible', True), page.update()])], alignment="center", horizontal_alignment="center")], alignment="center"), visible=False, expand=True, bgcolor="white")
    v_pago_finalizado = ft.Container(content=ft.Row([ft.Column([ft.Text("GRACIAS", size=40, weight="bold"), txt_mensaje_despedida := ft.Text("", size=22, text_align="center"), ft.ElevatedButton("CERRAR", bgcolor="blue", color="white", width=350, height=70, on_click=ir_a_mesas)], alignment="center", horizontal_alignment="center")], alignment="center"), visible=False, expand=True, bgcolor="white")
    v_confirm_cierre = ft.Container(content=ft.Row([ft.Column([ft.Text("¡ADVERTENCIA!", size=30, weight="bold", color="red"), ft.Text("Se resetearán los ingresos y se generará el Excel."), ft.Row([ft.ElevatedButton("SÍ", bgcolor="green", color="white", on_click=ejecutar_cierre_final, width=150), ft.ElevatedButton("NO", bgcolor="red", color="white", on_click=lambda _: [setattr(v_confirm_cierre, 'visible', False), page.update()], width=150)], alignment="center")], alignment="center", horizontal_alignment="center")], alignment="center"), visible=False, expand=True, bgcolor="rgba(255,255,255,0.95)")
    v_resumen_cierre = ft.Container(content=ft.Row([ft.Column([ft.Text("RESUMEN CIERRE", size=30, weight="bold"), txt_resumen_cierre_total := ft.Text("", size=30, color="green", weight="bold"), txt_resumen_efectivo := ft.Text(""), txt_resumen_tarjeta := ft.Text(""), txt_resumen_cierre_fecha := ft.Text("", size=18, weight="bold"), ft.ElevatedButton("CERRAR", on_click=ir_a_admin)], alignment="center", horizontal_alignment="center")], alignment="center"), visible=False, expand=True, bgcolor="white")

    page.add(ft.Stack([
        v_mesas, v_pedido, v_login, v_login_bloqueo, v_admin, v_confirmacion, v_ticket_final, 
        v_confirm_cierre, v_resumen_cierre, v_pago_metodo, v_pago_mixto, v_pago_finalizado, 
        v_gestion_menu, v_credenciales, v_visor_reportes, v_bloqueo_mesas
    ], expand=True))
    ir_a_mesas(None)

if __name__ == "__main__":
    ft.app(target=main)