import streamlit as st
import cv2
import numpy as np
import easyocr
import imutils
import rembg
from PIL import Image
from datetime import datetime
import psycopg2
import io
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Reconocimiento de placas de vehículos",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CONEXIÓN A LA BASE DE DATOS ---
def conectar_bd():
    return psycopg2.connect(
        host="localhost",
        database="db_recplacas",
        user="postgres",
        password="admin"
    )

# --- FUNCIÓN PARA GUARDAR EN BD ---
def guardar_en_bd(placa, tiene_restriccion, dia, img_original, img_placa):
    conn = conectar_bd()
    cur = conn.cursor()
    _, buffer_original = cv2.imencode('.jpg', img_original)
    _, buffer_placa = cv2.imencode('.jpg', img_placa)
    bytes_original = buffer_original.tobytes()
    bytes_placa = buffer_placa.tobytes()
    cur.execute("""
        INSERT INTO registros_vehiculares
        (placa, tiene_restriccion, dia_semana, imagen_original, imagen_placa, fecha_hora)
        VALUES (%s, %s, %s, %s, %s, NOW())
    """, (placa, tiene_restriccion, dia, psycopg2.Binary(bytes_original), psycopg2.Binary(bytes_placa)))
    conn.commit()
    cur.close()
    conn.close()

# --- FUNCIÓN PARA OBTENER REGISTROS ---
def obtener_registros():
    conn = conectar_bd()
    query = "SELECT id, placa, tiene_restriccion, dia_semana, fecha_hora, imagen_original, imagen_placa FROM registros_vehiculares ORDER BY fecha_hora DESC;"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# --- FUNCIÓN PARA OBTENER CORREO ASOCIADO A PLACA ---
def obtener_correo_por_placa(placa):
    conn = conectar_bd()
    cur = conn.cursor()
    cur.execute("SELECT correo FROM datos_personales WHERE UPPER(placa_reg) = %s;", (placa.upper(),))
    resultado = cur.fetchone()
    cur.close()
    conn.close()
    if resultado:
        return resultado[0]
    return None

# --- FUNCIÓN PARA ENVIAR CORREO USANDO SMTP ---
def enviar_correo_smtp(destinatario, placa, dia):
    remitente = "@ucb.edu.bo"  # hagan la prueba con su correo de la u
    contraseña = ""      #  aca deben poner una contraseña, algo así kvxi kzev vllj lxev, aca esta link para creen la contraseña: https://youtube.com/shorts/Tuyai2xNwvE?si=IGKBlMi2hVBKC2GO

    asunto = f"Notificación de restricción vehicular ({placa})"
    cuerpo = f"""
    Estimado propietario,

    El vehículo con placa {placa} tiene restricción vehicular el día {dia.capitalize()}.
    Por favor, evite circular para no incurrir en una infracción de 500 BOB.

    Saludos cordiales,
    Sistema de Control Vehicular
    """

    msg = MIMEMultipart()
    msg['From'] = remitente
    msg['To'] = destinatario
    msg['Subject'] = asunto
    msg.attach(MIMEText(cuerpo, 'plain'))

    try:
        # Cambia "smtp.ucb.edu.bo" y el puerto si tu institución usa otro
        with smtplib.SMTP('smtp.gmail.com', 587) as servidor:
            servidor.starttls()
            servidor.login(remitente, contraseña)
            servidor.send_message(msg)
        st.success(f"Notificación enviada a {destinatario}")
    except Exception as e:
        st.warning(f"No se pudo enviar el correo: {e}")

# --- FUNCIÓN PARA OBTENER LA PLACA ---
def obtenerPlaca(location, img, gray):
    mask = np.zeros(gray.shape, np.uint8)
    new_image = cv2.drawContours(mask, [location], 0, 255, -1)
    new_image = cv2.bitwise_and(img, img, mask=mask)
    imagenContornos = cv2.cvtColor(new_image, cv2.COLOR_BGR2RGB)
    (x, y) = np.where(mask == 255)
    (x1, y1) = (np.min(x), np.min(y))
    (x2, y2) = (np.max(x), np.max(y))
    cropped_image = gray[x1:x2 + 1, y1:y2 + 1]
    imagenplaca = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2RGB)
    reader = easyocr.Reader(['es'])
    result = reader.readtext(cropped_image)
    placa = None
    if result:
        placa = result[0][-2]
    return placa, imagenplaca, imagenContornos

# --- FUNCIÓN: Control de restricción vehicular ---
def verificar_restriccion(placa_texto):
    dias_restriccion = {
        "lunes": [0, 1],
        "martes": [2, 3],
        "miércoles": [4, 5],
        "jueves": [6, 7],
        "viernes": [8, 9]
    }

    hoy = datetime.now().strftime("%A").lower()
    traduccion_dias = {
        "monday": "lunes",
        "tuesday": "martes",
        "wednesday": "miércoles",
        "thursday": "jueves",
        "friday": "viernes",
        "saturday": "sábado",
        "sunday": "domingo"
    }
    hoy = traduccion_dias.get(hoy, hoy)

    numeros = [c for c in placa_texto if c.isdigit()]
    if not numeros:
        return "No se detectaron números en la placa", 1, hoy

    ultimo = int(numeros[-1])
    if hoy in dias_restriccion:
        if ultimo in dias_restriccion[hoy]:
            return f"🔴 Tiene restricción hoy ({hoy.capitalize()}) - último dígito: {ultimo}", 0, hoy
        else:
            return f"🟢 No tiene restricción hoy ({hoy.capitalize()}) - último dígito: {ultimo}", 1, hoy
    else:
        return f"🟢 No hay restricción los fines de semana ({hoy.capitalize()})", 1, hoy

# --- SIDEBAR ---
pagina = st.sidebar.selectbox("Selecciona una página", ["Reconocimiento", "Registros almacenados"])

# --- PÁGINA 1: Reconocimiento ---
if pagina == "Reconocimiento":
    st.header('Reconocimiento de placas de Vehículos')
    st.warning("Carga una foto de un vehículo donde se vea la placa claramente", icon=":material/warning:")

    archivo_cargado = st.file_uploader("Elige una imagen del vehículo", type=['jpg', 'png'])

    if archivo_cargado is not None:
        c1, c2 = st.columns(2)
        bytes_data = archivo_cargado.getvalue()
        img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), 1)

        output_array = rembg.remove(img)
        output_image = Image.fromarray(output_array)

        c1.subheader("Proceso")
        c2.subheader("Resultado")

        with c1:
            c3, c4 = st.columns(2)
            c3.write("Imagen cargada")
            c3.image(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
            c4.write("Imagen con fondo eliminado")
            c4.image(cv2.cvtColor(output_array, cv2.COLOR_BGR2RGB))

            gray = cv2.cvtColor(output_array, cv2.COLOR_BGR2GRAY)
            bfilter = cv2.bilateralFilter(gray, 11, 17, 17)
            c3.write("Escala de grises")
            c3.image(cv2.cvtColor(bfilter, cv2.COLOR_BGR2RGB))

            reader = easyocr.Reader(['es'])
            result = reader.readtext(gray)
            resultadosOCR = [x[1] for x in result if len(x[1]) > 4]

            edged = cv2.Canny(bfilter, 30, 200)
            c4.write("Bordes detectados")
            c4.image(cv2.cvtColor(edged, cv2.COLOR_BGR2RGB))

        keypoints = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        contours = imutils.grab_contours(keypoints)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]

        location = None
        placa = None

        for contour in contours:
            approx = cv2.approxPolyDP(contour, 10, True)
            if len(approx) == 4:
                location = approx
                placa, imagenplaca, imagenContornos = obtenerPlaca(location, img, gray)
                if placa and len(placa) > 5:
                    break

        if placa:
            c1.write("Placa detectada")
            c1.image(imagenContornos)

            with c2:
                c3, c4 = st.columns([5, 2])
                c4.write("Placa procesada")
                c4.image(imagenplaca)
                text = placa.strip().upper()
                res = cv2.rectangle(img, tuple(location[0][0]), tuple(location[2][0]), (0, 255, 0), 3)
                c4.write("Placa detectada")
                c4.metric("Placa", text)
                c3.image(cv2.cvtColor(res, cv2.COLOR_BGR2RGB))

                # Verificar restricción
                mensaje_restriccion, flag_restriccion, dia = verificar_restriccion(text)

                if flag_restriccion == 0:
                    st.error(mensaje_restriccion)
                else:
                    st.success(mensaje_restriccion)

                # Guardar registro en BD
                try:
                    guardar_en_bd(text, flag_restriccion, dia, img, imagenplaca)
                    st.info(f"Registro almacenado ({'tiene' if flag_restriccion == 0 else 'no tiene'} restricción).")
                except Exception as e:
                    st.error(f"❌ Error al guardar en BD: {e}")

                # Si tiene restricción, buscar correo y notificar vía SMTP
                if flag_restriccion == 0:
                    correo = obtener_correo_por_placa(text)
                    if correo:
                        enviar_correo_smtp(correo, text, dia)
                    else:
                        st.warning(f"No se encontró correo asociado a la placa {text}")

            c2.write("Textos detectados con OCR")
            c2.dataframe(resultadosOCR, width='stretch')
        else:
            c2.error("No se ha encontrado una placa válida")
            c2.write("Textos detectados con OCR")
            c2.dataframe(resultadosOCR, width='stretch')

# --- PÁGINA 2: Registros almacenados ---
elif pagina == "Registros almacenados":
    st.header("Registros de vehículos almacenados")

    try:
        df = obtener_registros()
        if df.empty:
            st.info("No hay registros almacenados todavía.")
        else:
            st.dataframe(df[["id", "placa", "dia_semana", "fecha_hora", "tiene_restriccion"]], width='stretch')

            id_sel = st.selectbox("Selecciona un registro para ver detalles", df["id"])
            registro = df[df["id"] == id_sel].iloc[0]

            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Imagen original")
                st.image(Image.open(io.BytesIO(registro["imagen_original"])))

            with col2:
                st.subheader("Placa detectada")
                st.image(Image.open(io.BytesIO(registro["imagen_placa"])))

            st.markdown(f"**Fecha y hora:** {registro['fecha_hora']}")
            st.markdown(f"**Placa:** `{registro['placa']}`")
            st.markdown(f"**Día:** {registro['dia_semana'].capitalize()}")
            st.markdown(f"**Restricción:** {'Tiene restricción' if registro['tiene_restriccion'] == 0 else 'No tiene restricción'}")
    except Exception as e:
        st.error(f"Error al obtener los registros: {e}")