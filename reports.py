import openpyxl
from openpyxl.styles import Font
from datetime import datetime
import os

def generar_excel_cierre(ventas, total, efectivo, tarjeta, tablet_id):
    # Definimos ruta base según el sistema
    if os.environ.get("FLET_PLATFORM") == "android":
        base_path = os.getenv("HOME")
    else:
        base_path = os.getcwd()

    nombre_subcarpeta = os.path.join(base_path, "Reportes_Cierre")
    
    if not os.path.exists(nombre_subcarpeta): 
        os.makedirs(nombre_subcarpeta)
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Corte de Caja"
    ws["A1"] = f"CORTE DE CAJA - TABLET {tablet_id}"
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
    
    nombre_archivo = f"Corte_T{tablet_id}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    ruta_completa = os.path.join(nombre_subcarpeta, nombre_archivo)
    wb.save(ruta_completa)
    return ruta_completa

# --- NUEVA FUNCIÓN PARA LEER EL EXCEL ---
def leer_excel(ruta_completa):
    try:
        wb = openpyxl.load_workbook(ruta_completa, data_only=True)
        ws = wb.active
        filas = []
        # iter_rows nos da fila por fila, values_only saca el texto directo
        for row in ws.iter_rows(values_only=True):
            # Convertimos todo a string y cambiamos los 'None' (celdas vacías) por texto vacío
            filas.append([str(celda) if celda is not None else "" for celda in row])
        return filas
    except Exception as e:
        return None