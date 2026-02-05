import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect("pos_restaurante.db")
    cursor = conn.cursor()
    # Creación de tablas
    cursor.execute("CREATE TABLE IF NOT EXISTS ventas (id INTEGER PRIMARY KEY AUTOINCREMENT, mesa_id INTEGER, detalle TEXT, total REAL, fecha TEXT, metodo_pago TEXT, cerrada INTEGER DEFAULT 0)")
    cursor.execute("CREATE TABLE IF NOT EXISTS items_activos (id INTEGER PRIMARY KEY AUTOINCREMENT, mesa_id INTEGER, nombre TEXT, precio REAL, cantidad INTEGER, destino TEXT, enviado INTEGER)")
    cursor.execute("CREATE TABLE IF NOT EXISTS productos (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, precio REAL, categoria TEXT, destino TEXT)")
    
    # Inserción inicial de productos si la tabla está vacía
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
    conn.commit(); conn.close()

def db_remover_item_activo(mesa, nombre):
    conn = sqlite3.connect("pos_restaurante.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, cantidad FROM items_activos WHERE mesa_id=? AND nombre=? AND enviado=0", (mesa, nombre))
    res = cursor.fetchone()
    if res:
        if res[1] > 1: cursor.execute("UPDATE items_activos SET cantidad=? WHERE id=?", (res[1]-1, res[0]))
        else: cursor.execute("DELETE FROM items_activos WHERE id=?", (res[0],))
    conn.commit(); conn.close()

def db_marcar_enviados(mesa):
    conn = sqlite3.connect("pos_restaurante.db")
    conn.cursor().execute("UPDATE items_activos SET enviado=1 WHERE mesa_id=?", (mesa,))
    conn.commit(); conn.close()

def db_limpiar_mesa(mesa):
    conn = sqlite3.connect("pos_restaurante.db")
    conn.cursor().execute("DELETE FROM items_activos WHERE mesa_id=?", (mesa,))
    conn.commit(); conn.close()

def db_registrar_venta_final(mesa_id, detalle, total, metodo):
    conn = sqlite3.connect("pos_restaurante.db")
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.cursor().execute("INSERT INTO ventas (mesa_id, detalle, total, fecha, metodo_pago, cerrada) VALUES (?, ?, ?, ?, ?, 0)", (mesa_id, detalle, total, ahora, metodo))
    conn.commit(); conn.close()

def db_ejecutar_cierre_caja():
    conn = sqlite3.connect("pos_restaurante.db")
    conn.cursor().execute("UPDATE ventas SET cerrada = 1 WHERE cerrada = 0")
    conn.commit(); conn.close()

def db_obtener_ventas_activas():
    conn = sqlite3.connect("pos_restaurante.db")
    datos = conn.cursor().execute("SELECT mesa_id, detalle, total, fecha, metodo_pago FROM ventas WHERE cerrada = 0").fetchall()
    conn.close(); return datos

def db_cargar_estado_inicial():
    conn = sqlite3.connect("pos_restaurante.db")
    filas = conn.cursor().execute("SELECT mesa_id, nombre, precio, cantidad, destino, enviado FROM items_activos").fetchall()
    conn.close()
    datos = {i: [] for i in range(1, 21)}
    for f in filas: datos[f[0]].append({"n": f[1], "p": f[2], "q": f[3], "d": f[4], "enviado": bool(f[5])})
    return datos

def db_obtener_productos():
    conn = sqlite3.connect("pos_restaurante.db")
    prods = conn.cursor().execute("SELECT id, nombre, precio, categoria, destino FROM productos").fetchall()
    conn.close(); return prods

def db_actualizar_precio_producto(id_p, nuevo_p):
    conn = sqlite3.connect("pos_restaurante.db")
    conn.cursor().execute("UPDATE productos SET precio=? WHERE id=?", (float(nuevo_p), id_p))
    conn.commit(); conn.close()

def db_eliminar_producto(id_p):
    conn = sqlite3.connect("pos_restaurante.db")
    conn.cursor().execute("DELETE FROM productos WHERE id=?", (id_p,))
    conn.commit(); conn.close()

def db_agregar_producto(nom, pre, cat, dest):
    conn = sqlite3.connect("pos_restaurante.db")
    conn.cursor().execute("INSERT INTO productos (nombre, precio, categoria, destino) VALUES (?,?,?,?)", (nom, float(pre), cat, dest))
    conn.commit(); conn.close()