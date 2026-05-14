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

        # Insertar cliente
        cursor.execute(
            "INSERT INTO clientes (nombre, correo, telefono) VALUES (%s, %s, %s)",
            (data["cliente"]["nombre"], data["cliente"]["correo"], data["cliente"]["telefono"])
        )
        cliente_id = cursor.lastrowid

        # Insertar cita con el cliente recién creado
        cursor.execute(
            "INSERT INTO citas (cliente_id, fecha, hora, estado) VALUES (%s, %s, %s, %s)",
            (cliente_id, data["fecha"], data["hora"], data["estado"])
        )
        cita_id = cursor.lastrowid

        # Insertar servicios seleccionados
        for s in data.get("servicios", []):
            if "id" in s:
                cursor.execute(
                    "INSERT INTO detalle_cita (cita_id, servicio_id) VALUES (%s, %s)",
                    (cita_id, s["id"])
                )

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"ok": True, "cita_id": cita_id, "cliente_id": cliente_id}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 400


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
