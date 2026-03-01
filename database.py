import sqlite3
from datetime import datetime
import os

# --- LÓGICA DE RUTA DINÁMICA DE FUERZA BRUTA ---
def get_db_path():
    db_name = "pos_restaurante.db"
    
    rutas_candidatas = [
        os.environ.get("HOME"),                              
        "/data/user/0/com.lexuzz07.pos_restaurante/files",    
        "/data/data/com.lexuzz07.pos_restaurante/files",      
        os.environ.get("TMPDIR"),                             
        os.path.expanduser("~"),                              
        os.getcwd()                                           
    ]

    for ruta in rutas_candidatas:
        if ruta: 
            try:
                if not os.path.exists(ruta):
                    os.makedirs(ruta, exist_ok=True)
                archivo_prueba = os.path.join(ruta, "test_permiso.tmp")
                with open(archivo_prueba, "w") as f:
                    f.write("acceso concedido")
                os.remove(archivo_prueba) 
                return os.path.join(ruta, db_name)
            except Exception:
                continue
    return db_name

def get_db_connection():
    return sqlite3.connect(get_db_path())

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS ventas (id INTEGER PRIMARY KEY AUTOINCREMENT, mesa_id INTEGER, detalle TEXT, total REAL, fecha TEXT, metodo_pago TEXT, cerrada INTEGER DEFAULT 0)")
    cursor.execute("CREATE TABLE IF NOT EXISTS items_activos (id INTEGER PRIMARY KEY AUTOINCREMENT, mesa_id INTEGER, nombre TEXT, precio REAL, cantidad INTEGER, destino TEXT, enviado INTEGER)")
    cursor.execute("CREATE TABLE IF NOT EXISTS productos (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, precio REAL, categoria TEXT, destino TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS configuracion (clave TEXT PRIMARY KEY, valor TEXT)")
    
    cursor.execute("CREATE TABLE IF NOT EXISTS categorias (nombre TEXT PRIMARY KEY)")
    cursor.execute("CREATE TABLE IF NOT EXISTS destinos (nombre TEXT PRIMARY KEY)")
    
    cursor.execute("SELECT valor FROM configuracion WHERE clave='tablet_id'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO configuracion (clave, valor) VALUES ('tablet_id', '01')")

    # NUEVO: CONFIGURACIÓN DE NÚMERO DE MESAS
    cursor.execute("SELECT valor FROM configuracion WHERE clave='num_mesas'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO configuracion (clave, valor) VALUES ('num_mesas', '20')")

    cursor.execute("SELECT valor FROM configuracion WHERE clave='admin_usr'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO configuracion (clave, valor) VALUES ('admin_usr', 'admin')")
        cursor.execute("INSERT INTO configuracion (clave, valor) VALUES ('admin_pass', '1234')")

    cursor.execute("SELECT valor FROM configuracion WHERE clave='mesas_bloqueadas'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO configuracion (clave, valor) VALUES ('mesas_bloqueadas', '')")

    cursor.execute("SELECT count(*) FROM categorias")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO categorias (nombre) VALUES (?)", [("BEBIDAS",), ("COMIDA",), ("POSTRES",)])
        
    cursor.execute("SELECT count(*) FROM destinos")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO destinos (nombre) VALUES (?)", [("BARRA",), ("COCINA",)])

    cursor.execute("SELECT count(*) FROM productos")
    if cursor.fetchone()[0] == 0:
        menu_inicial = [
            ("Cerveza", 55, "BEBIDAS", "BARRA"), ("Refresco", 35, "BEBIDAS", "BARRA"),
            ("Hamburguesa", 150, "COMIDA", "COCINA"), ("Tacos", 90, "COMIDA", "COCINA"),
            ("Pizza", 200, "COMIDA", "COCINA"), ("Pastel", 60, "POSTRES", "COCINA")
        ]
        cursor.executemany("INSERT INTO productos (nombre, precio, categoria, destino) VALUES (?,?,?,?)", menu_inicial)
    
    conn.commit()
    conn.close()

# --- FUNCIONES DE CATEGORÍAS Y DESTINOS DINÁMICOS ---
def db_obtener_categorias():
    conn = get_db_connection()
    res = conn.cursor().execute("SELECT nombre FROM categorias ORDER BY nombre").fetchall()
    conn.close()
    return [r[0] for r in res]

def db_agregar_categoria(nombre):
    conn = get_db_connection()
    try:
        conn.cursor().execute("INSERT INTO categorias (nombre) VALUES (?)", (nombre.upper(),))
        conn.commit()
    except sqlite3.IntegrityError:
        pass 
    conn.close()

def db_eliminar_categoria(nombre):
    conn = get_db_connection()
    conn.cursor().execute("DELETE FROM categorias WHERE nombre=?", (nombre,))
    conn.cursor().execute("DELETE FROM productos WHERE categoria=?", (nombre,)) 
    conn.commit()
    conn.close()

def db_obtener_destinos():
    conn = get_db_connection()
    res = conn.cursor().execute("SELECT nombre FROM destinos ORDER BY nombre").fetchall()
    conn.close()
    return [r[0] for r in res]

def db_agregar_destino(nombre):
    conn = get_db_connection()
    try:
        conn.cursor().execute("INSERT INTO destinos (nombre) VALUES (?)", (nombre.upper(),))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()

def db_eliminar_destino(nombre):
    conn = get_db_connection()
    conn.cursor().execute("DELETE FROM destinos WHERE nombre=?", (nombre,))
    conn.cursor().execute("DELETE FROM productos WHERE destino=?", (nombre,)) 
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

def db_obtener_num_mesas():
    conn = get_db_connection()
    res = conn.cursor().execute("SELECT valor FROM configuracion WHERE clave='num_mesas'").fetchone()
    conn.close()
    return int(res[0]) if res else 20

def db_actualizar_num_mesas(num):
    conn = get_db_connection()
    conn.cursor().execute("UPDATE configuracion SET valor=? WHERE clave='num_mesas'", (str(num),))
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

def db_obtener_mesas_bloqueadas():
    conn = get_db_connection()
    res = conn.cursor().execute("SELECT valor FROM configuracion WHERE clave='mesas_bloqueadas'").fetchone()
    conn.close()
    if res and res[0]:
        return [int(x) for x in res[0].split(',')] 
    return []

def db_actualizar_mesas_bloqueadas(lista_mesas):
    conn = get_db_connection()
    valor_texto = ",".join(map(str, lista_mesas)) 
    conn.cursor().execute("UPDATE configuracion SET valor=? WHERE clave='mesas_bloqueadas'", (valor_texto,))
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
    num_mesas = db_obtener_num_mesas()
    conn = get_db_connection()
    filas = conn.cursor().execute("SELECT mesa_id, nombre, precio, cantidad, destino, enviado FROM items_activos").fetchall()
    conn.close()
    
    # Creamos diccionarios según la cantidad configurada
    datos = {i: [] for i in range(1, num_mesas + 1)}
    
    # Aseguramos que si hay mesas con órdenes viejas (superiores a la nueva cantidad), no crashee
    for f in filas: 
        if f[0] not in datos:
            datos[f[0]] = []
        datos[f[0]].append({"n": f[1], "p": f[2], "q": f[3], "d": f[4], "enviado": bool(f[5])})
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