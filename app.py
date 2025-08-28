from flask import Flask, request, jsonify, send_file, render_template_string
import qrcode
import datetime, io, os

app = Flask(__name__)

# 🔒 Clave secreta (cámbiala en Render con Environment Variable)
SECRET = os.getenv("QR_SECRET", "mi_clave_super_segura")

# 🟢 Generar QR de una casa
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

# 🟢 Página de verificación con cámara
@app.route("/verify")
def verify_page():
    html = """
    <html>
    <head>
        <title>Verificador QR</title>
        <script src="https://unpkg.com/html5-qrcode" type="text/javascript"></script>
    </head>
    <body style="font-family:Arial; text-align:center;">
        <h2>📷 Verificador de QR</h2>
        <div id="reader" style="width:300px; margin:auto;"></div>
        <p id="result" style="font-size:18px; font-weight:bold;"></p>

        <script>
        function onScanSuccess(decodedText, decodedResult) {
            fetch('/check?data=' + encodeURIComponent(decodedText))
            .then(r => r.json())
            .then(d => {
                document.getElementById("result").innerText = d.message;
            });
        }

        function onScanError(errorMessage) {
            // errores se ignoran para no spamear
        }

        let html5QrcodeScanner = new Html5QrcodeScanner(
            "reader", { fps: 10, qrbox: 250 });
        html5QrcodeScanner.render(onScanSuccess, onScanError);
        </script>
    </body>
    </html>
    """
    return render_template_string(html)

# 🟢 Ruta de verificación (procesa el QR)
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

# 🟢 Modo local (por si corres con python app.py)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
