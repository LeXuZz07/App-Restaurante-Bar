import openpyxl
from openpyxl.styles import Font
from datetime import datetime
import os

TABLET_ID = "01"

def generar_excel_cierre(ventas, total, efectivo, tarjeta):
    nombre_subcarpeta = "Reportes Cierre de Caja"
    if not os.path.exists(nombre_subcarpeta): os.makedirs(nombre_subcarpeta)
    
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
    for col, text in enumerate(headers, 1): ws.cell(row=8, column=col, value=text).font = Font(bold=True)
    
    for row_idx, v in enumerate(ventas, 9):
        ws.cell(row=row_idx, column=1, value=f"Mesa {v[0]}")
        ws.cell(row=row_idx, column=2, value=v[3])
        ws.cell(row=row_idx, column=3, value=v[4])
        ws.cell(row=row_idx, column=4, value=v[2])
        ws.cell(row=row_idx, column=5, value=v[1])
    
    nombre_archivo = f"Corte_T{TABLET_ID}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    ruta_completa = os.path.join(nombre_subcarpeta, nombre_archivo)
    wb.save(ruta_completa); return ruta_completa