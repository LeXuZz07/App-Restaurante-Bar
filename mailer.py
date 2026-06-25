import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os
import json
from datetime import datetime

def cargar_configuracion():
    """Carga las credenciales desde el archivo config.json."""
    ruta_config = os.path.join(os.path.dirname(__file__), 'config.json')
    if not os.path.exists(ruta_config):
        print("⚠️ Error: No se encontró el archivo config.json")
        return None
    
    with open(ruta_config, 'r') as f:
        return json.load(f)

def enviar_reporte_cierre(ruta_excel_adjunto):
    """
    Envía el archivo Excel generado al correo configurado en config.json.
    """
    config = cargar_configuracion()
    if not config:
        return False, "Error de configuración."

    remitente = config['EMAIL_REMITENTE']
    password = config['EMAIL_PASSWORD']
    destinatario = config['EMAIL_DESTINATARIO']
    
    # Crear el mensaje
    msg = MIMEMultipart()
    msg['From'] = remitente
    msg['To'] = destinatario
    
    fecha_hoy = datetime.now().strftime('%Y-%m-%d')
    msg['Subject'] = f"Corte de Caja - {fecha_hoy} - POS Hacienda Real"
    
    cuerpo = (
        "Hola,\n\n"
        "Se ha generado un nuevo corte de caja automáticamente desde el sistema POS.\n"
        "Se adjunta el archivo Excel con el detalle de las ventas y las estadísticas.\n\n"
        "Saludos,\n"
        "Sistema POS"
    )
    msg.attach(MIMEText(cuerpo, 'plain'))
    
    # Adjuntar archivo
    if not os.path.exists(ruta_excel_adjunto):
        return False, f"El archivo no existe: {ruta_excel_adjunto}"

    try:
        with open(ruta_excel_adjunto, "rb") as f:
            part = MIMEApplication(f.read(), _subtype="xlsx")
            part.add_header('Content-Disposition', 'attachment', filename=os.path.basename(ruta_excel_adjunto))
            msg.attach(part)
    except Exception as e:
        return False, f"Error al adjuntar: {e}"

    # Envío SMTP
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(remitente, password)
        server.send_message(msg)
        server.quit()
        return True, "Reporte enviado con éxito."
    except Exception as e:
        return False, f"Error al enviar: {e}"