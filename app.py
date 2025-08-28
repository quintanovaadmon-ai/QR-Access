from flask import Flask, request, jsonify, send_file, render_template_string
import qrcode
import datetime, io, os

app = Flask(__name__)

# 🔒 Clave secreta (guárdala como variable de entorno en Render)
SECRET = os.getenv("QR_SECRET", "mi_clave_super_segura")

# 🟢 Ruta para generar QR de una casa
@app.route("/generate/<house>")
def generate_qr(house):
    today = datetime.date.today().strftime("%Y-%m-%d")
    data = f"{house}|{today}|{SECRET}"

    # Generar QR en memoria
    img = qrcode.make(data)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    return send_file(buf, mimetype="image/png")

# 🟢 Página web para verificar QR (los guardias la abren en el cel/tablet)
@app.route("/verify")
def verify_page():
    html = """
    <html>
    <head><title>Verificador QR</title></head>
    <body style="font-family:Arial; text-align:center;">
        <h2>📷 Verificador de QR</h2>
        <p>Pega aquí el contenido leído del QR:</p>
        <input type="text" id="qrdata" style="width:80%; padding:8px;" />
        <button onclick="verify()">Verificar</button>
        <p id="result"></p>

        <script>
        function verify() {
            let qrdata = document.getElementById("qrdata").value;
            fetch('/check?data=' + encodeURIComponent(qrdata))
            .then(r => r.json())
            .then(d => {
                document.getElementById("result").innerText = d.message;
            });
        }
        </script>
    </body>
    </html>
    """
    return render_template_string(html)

# 🟢 Ruta de verificación (procesa lo leído del QR)
@app.route("/check")
def check_qr():
    qrdata = request.args.get("data", "")
    try:
        house, date, secret = qrdata.split("|")
        today = datetime.date.today().strftime("%Y-%m-%d")
        if secret != SECRET:
            return jsonify({"valid": False, "message": "❌ Código inválido"})
        if date != today:
            return jsonify({"valid": False, "message": "⚠️ QR vencido"})
        return jsonify({"valid": True, "message": f"✅ Acceso permitido: {house}"})
    except:
        return jsonify({"valid": False, "message": "❌ Formato inválido"})
