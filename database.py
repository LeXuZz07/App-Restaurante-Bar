import sqlite3
from datetime import datetime
import os

# --- LÓGICA DE RUTA DINÁMICA ---
def get_db_path():
    db_name = "pos_restaurante.db"
    # Detectamos si estamos en Android
    if os.environ.get("FLET_PLATFORM") == "android":
        return os.path.join(os.getenv("HOME"), db_name)
    # Si estamos en PC (Windows/Linux/Mac)
    return os.path.join(os.getcwd(), db_name)

def get_db_connection():
    return sqlite3.connect(get_db_path())

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS ventas (id INTEGER PRIMARY KEY AUTOINCREMENT, mesa_id INTEGER, detalle TEXT, total REAL, fecha TEXT, metodo_pago TEXT, cerrada INTEGER DEFAULT 0)")
    cursor.execute("CREATE TABLE IF NOT EXISTS items_activos (id INTEGER PRIMARY KEY AUTOINCREMENT, mesa_id INTEGER, nombre TEXT, precio REAL, cantidad INTEGER, destino TEXT, enviado INTEGER)")
    cursor.execute("CREATE TABLE IF NOT EXISTS productos (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, precio REAL, categoria TEXT, destino TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS configuracion (clave TEXT PRIMARY KEY, valor TEXT)")
    
    cursor.execute("SELECT valor FROM configuracion WHERE clave='tablet_id'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO configuracion (clave, valor) VALUES ('tablet_id', '01')")

    # --- NUEVO: Credenciales por defecto ---
    cursor.execute("SELECT valor FROM configuracion WHERE clave='admin_usr'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO configuracion (clave, valor) VALUES ('admin_usr', 'admin')")
        cursor.execute("INSERT INTO configuracion (clave, valor) VALUES ('admin_pass', '1234')")

    cursor.execute("SELECT count(*) FROM productos")
    if cursor.fetchone()[0] == 0:
        menu_inicial = [
            ("Cerveza", 55, "BEBIDAS", "BARRA"), ("Refresco", 35, "BEBIDAS", "BARRA"),
            ("Hamburguesa", 150, "COMIDA", "COCINA"), ("Tacos", 90, "COMIDA", "COCINA"),
            ("Pizza", 200, "COMIDA", "COCINA"), ("Pastel", 60, "POSTRES", "OTROS")
        ]
        cursor.executemany("INSERT INTO productos (nombre, precio, categoria, destino) VALUES (?,?,?,?)", menu_inicial)
    
    conn.commit()
    conn.close()

# --- FUNCIONES DE CONFIGURACIÓN Y SEGURIDAD ---
def db_obtener_tablet_id():
    conn = get_db_connection()
    res = conn.cursor().execute("SELECT valor FROM configuracion WHERE clave='tablet_id'").fetchone()
    conn.close()
    return res[0] if res else "01"

def db_actualizar_tablet_id(nuevo_id):
    conn = get_db_connection()
    conn.cursor().execute("UPDATE configuracion SET valor=? WHERE clave='tablet_id'", (nuevo_id,))
    conn.commit(); conn.close()

def db_obtener_credenciales():
    conn = get_db_connection()
    usr = conn.cursor().execute("SELECT valor FROM configuracion WHERE clave='admin_usr'").fetchone()
    pwd = conn.cursor().execute("SELECT valor FROM configuracion WHERE clave='admin_pass'").fetchone()
    conn.close()
    return usr[0] if usr else "admin", pwd[0] if pwd else "1234"

def db_actualizar_credenciales(usr, pwd):
    conn = get_db_connection()
    conn.cursor().execute("UPDATE configuracion SET valor=? WHERE clave='admin_usr'", (usr,))
    conn.cursor().execute("UPDATE configuracion SET valor=? WHERE clave='admin_pass'", (pwd,))
    conn.commit()
    conn.close()

# --- FUNCIONES DE PERSISTENCIA ---
def db_guardar_item_activo(mesa, item):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, cantidad FROM items_activos WHERE mesa_id=? AND nombre=? AND enviado=0", (mesa, item['n']))
    res = cursor.fetchone()
    if res:
        cursor.execute("UPDATE items_activos SET cantidad=? WHERE id=?", (item['q'], res[0]))
    else:
        cursor.execute("INSERT INTO items_activos (mesa_id, nombre, precio, cantidad, destino, enviado) VALUES (?,?,?,?,?,?)",
                       (mesa, item['n'], item['p'], item['q'], item['d'], 0))
    conn.commit(); conn.close()

def db_remover_item_activo(mesa, nombre):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, cantidad FROM items_activos WHERE mesa_id=? AND nombre=? AND enviado=0", (mesa, nombre))
    res = cursor.fetchone()
    if res:
        if res[1] > 1: cursor.execute("UPDATE items_activos SET cantidad=? WHERE id=?", (res[1]-1, res[0]))
        else: cursor.execute("DELETE FROM items_activos WHERE id=?", (res[0],))
    conn.commit(); conn.close()

def db_marcar_enviados(mesa):
    conn = get_db_connection()
    conn.cursor().execute("UPDATE items_activos SET enviado=1 WHERE mesa_id=?", (mesa,))
    conn.commit(); conn.close()

def db_limpiar_mesa(mesa):
    conn = get_db_connection()
    conn.cursor().execute("DELETE FROM items_activos WHERE mesa_id=?", (mesa,))
    conn.commit(); conn.close()

def db_registrar_venta_final(mesa_id, detalle, total, metodo):
    conn = get_db_connection()
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.cursor().execute("INSERT INTO ventas (mesa_id, detalle, total, fecha, metodo_pago, cerrada) VALUES (?, ?, ?, ?, ?, 0)", 
                           (mesa_id, detalle, total, ahora, metodo))
    conn.commit(); conn.close()

def db_ejecutar_cierre_caja():
    conn = get_db_connection()
    conn.cursor().execute("UPDATE ventas SET cerrada = 1 WHERE cerrada = 0")
    conn.commit(); conn.close()

def db_obtener_ventas_activas():
    conn = get_db_connection()
    datos = conn.cursor().execute("SELECT mesa_id, detalle, total, fecha, metodo_pago FROM ventas WHERE cerrada = 0").fetchall()
    conn.close(); return datos

def db_cargar_estado_inicial():
    conn = get_db_connection()
    filas = conn.cursor().execute("SELECT mesa_id, nombre, precio, cantidad, destino, enviado FROM items_activos").fetchall()
    conn.close()
    datos = {i: [] for i in range(1, 21)}
    for f in filas: datos[f[0]].append({"n": f[1], "p": f[2], "q": f[3], "d": f[4], "enviado": bool(f[5])})
    return datos

def db_obtener_productos():
    conn = get_db_connection()
    prods = conn.cursor().execute("SELECT id, nombre, precio, categoria, destino FROM productos").fetchall()
    conn.close(); return prods

def db_actualizar_precio_producto(id_p, nuevo_p):
    conn = get_db_connection()
    conn.cursor().execute("UPDATE productos SET precio=? WHERE id=?", (float(nuevo_p), id_p))
    conn.commit(); conn.close()

def db_eliminar_producto(id_p):
    conn = get_db_connection()
    conn.cursor().execute("DELETE FROM productos WHERE id=?", (id_p,))
    conn.commit(); conn.close()

def db_agregar_producto(nom, pre, cat, dest):
    conn = get_db_connection()
    conn.cursor().execute("INSERT INTO productos (nombre, precio, categoria, destino) VALUES (?,?,?,?)", (nom, float(pre), cat, dest))
    conn.commit(); conn.close()