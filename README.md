# Reconocimiento de placas con notificación
Este proyecto utiliza Streamlit, OpenCV, EasyOCR y SMTP para detectar placas de vehículos desde imágenes, verificar si tienen restricción vehicular y enviar notificaciones por correo electrónico al propietario.

## Características
- Detección de placas de vehículos usando OCR.
- Eliminación de fondo para mejorar la detección.
- Verificación de restricción vehicular según último dígito de la placa
- Almacenamiento de registros en PostgreSQL.
- Notificación automática por correo electrónico a propietarios con placas restringidas.
- Visualización de registros y detalles desde la interfaz web.

## Requisitos
- Python 3.9 o superior
- PostgreSQL
- Paquetes de Python:
```bash
pip install streamlit opencv-python-headless numpy easyocr imutils rembg pillow psycopg2-binary pandas
```

## Configuración de la base de datos
### 1. Crear la base de datos en pgAdmin 4
```bash
CREATE DATABASE db_recplacas;
```
### 2. Crear las tablas necesarias:
```bash
-- Tabla de registros de placas
CREATE TABLE registros_vehiculares (
    id SERIAL PRIMARY KEY,
    placa VARCHAR(10),
    tiene_restriccion INTEGER,
    dia_semana VARCHAR(20),
    imagen_original BYTEA,
    imagen_placa BYTEA,
    fecha_hora TIMESTAMP
);

-- Tabla de datos personales
CREATE TABLE datos_personales (
    id_dp SERIAL PRIMARY KEY,
    nombres VARCHAR(50),
    apellido_paterno VARCHAR(50),
    apellido_materno VARCHAR(50),
    correo VARCHAR(50),
    placa_reg VARCHAR(10)
);
```
### 3. Configurar usuario y contraseña en la función conectar_bd() de app.py.

## Configuración del correo que será el remitente
Hacer la prueba con el correo institucional de la UCB en esta parte del código:
```bash
def enviar_correo_smtp(destinatario, placa, dia):
    remitente = "@ucb.edu.bo"
    contraseña = ""   
```
La contraseña será un token de google que será una serie de letras y deben copiarlo antes de cerrar la pestaña, acá el tutorial: https://youtube.com/shorts/Tuyai2xNwvE?si=IGKBlMi2hVBKC2GO

## Configuración de SMTP
Actualmente se encuentra configurado con Gmail y el puerto 587: 'smtp.gmail.com', 587
```bash
with smtplib.SMTP('smtp.gmail.com', 587) as servidor:
    servidor.starttls()
    servidor.login(remitente, contraseña)
```
Para cuentas institucionales de diferentes organizaciones, reemplazar smtp.gmail.com con el SMTP correspondiente: smtp.ucb.edu.bo
Se recomienda usar contraseñas de aplicación o tokens para mayor seguridad.

## Ejecución en Windows y Mac
1. Abrir terminal o PowerShell (Windows) o Terminal (Mac).
2. Navegar a la carpeta del proyecto.
3. Ejecutar Streamlit:
```bash
streamlit run app.py
```
4. Se abrirá la interfaz web en tu navegador por defecto.
5. Seleccionar la página "Reconocimiento" o "Registros almacenados" desde el sidebar.

## Uso
### 1. Reconocimiento de placas
- Subir una imagen donde se vea claramente la placa.
- El sistema detecta la placa y verifica la restricción.
- Si la placa tiene restricción, busca el correo asociado y envía notificación automática.
### 2. Registros almacenados
- Ver todos los registros almacenados en la base de datos.
- Visualizar imágenes originales y recortes de placas.