from email.mime.text import MIMEText
import smtplib

from flask import Flask, request, jsonify
from db import get_connection

app = Flask(__name__)

@app.route("/servicios", methods=["GET"])
def get_servicios():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, nombre, precio, categoria FROM servicios")
    servicios = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(servicios)

@app.route("/citas", methods=["POST"])
def crear_cita():
    data = request.json
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO clientes (nombre, correo, telefono) VALUES (%s, %s, %s)",
            (data["cliente"]["nombre"], data["cliente"]["correo"], data["cliente"]["telefono"])
        )
        cliente_id = cursor.lastrowid


        estado = data.get("estado", "pendiente")

        cursor.execute(
            "INSERT INTO citas (cliente_id, fecha, hora, estado) VALUES (%s, %s, %s, %s)",
            (cliente_id, data["fecha"], data["hora"], estado)
        )
        cita_id = cursor.lastrowid

        
        for s in data.get("servicios", []):
            if "id" in s:
                cursor.execute(
                    "INSERT INTO detalle_cita (cita_id, servicio_id) VALUES (%s, %s)",
                    (cita_id, s["id"])
                )

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"ok": True, "cita_id": cita_id, "cliente_id": cliente_id, "estado": estado}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/citas", methods=["GET"])
def listar_citas():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Traer citas con cliente
    cursor.execute("""
        SELECT c.id, c.fecha, c.hora, c.estado,
               cl.id AS cliente_id, cl.nombre, cl.correo, cl.telefono
        FROM citas c
        LEFT JOIN clientes cl ON c.cliente_id = cl.id
    """)
    citas_raw = cursor.fetchall()

    citas = []
    for c in citas_raw:
        cursor.execute("""
            SELECT s.id, s.nombre, s.precio, s.categoria
            FROM detalle_cita d
            JOIN servicios s ON d.servicio_id = s.id
            WHERE d.cita_id = %s
        """, (c["id"],))
        servicios = cursor.fetchall()

        cita = {
            "id": c["id"],
            "cliente": {
                "id": c["cliente_id"],
                "nombre": c["nombre"],
                "correo": c["correo"],
                "telefono": c["telefono"]
            },
            "servicios": servicios,
            "fecha": c["fecha"].isoformat(),
            "hora": str(c["hora"]),
            "estado": c["estado"]
        }
        citas.append(cita)

    cursor.close()
    conn.close()
    return jsonify(citas)

@app.route('/enviarcorreo', methods=['POST'])
def enviar_correo():
    data = request.json
    destinatario = data.get("correo")
    asunto = "Confirmación de cita"
    mensaje = f"Hola {data.get('cliente')}, tu cita está agendada para {data.get('fecha')} a las {data.get('hora')}."

    if not destinatario:
        return jsonify({"error": "Correo no proporcionado"}), 400

    try:
        msg = MIMEText(mensaje)
        msg['Subject'] = asunto
        msg['From'] = "tuservidor@dominio.com"
        msg['To'] = destinatario

        # Configuración SMTP (ejemplo con Gmail)
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login("esteticastudio02@gmail.com", "wivf trjm zwya wfik")
        server.sendmail("esteticastudio02@gmail.com", [destinatario], msg.as_string())
        server.quit()

        return jsonify({"message": "Correo enviado correctamente"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
