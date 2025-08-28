from flask import Flask, request, jsonify, send_file, render_template_string
import qrcode
import datetime, io, os, csv

app = Flask(__name__)

# 🔒 Clave secreta (debe configurarse en Render como variable de entorno)
SECRET = os.getenv("QR_SECRET", "mi_clave_super_segura")

# 📂 Cargar casas desde residents.csv
AUTHORIZED_HOUSES = {}
with open("residents.csv", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        AUTHORIZED_HOUSES[row["house"]] = row["status"]

# 🟢 Generar QR para una casa
@app.route("/generate/<house>")
def generate_qr(house):
    today = datetime.date.today().strftime("%Y-%m-%d")
    data = f"{house}|{today}|{SECRET}"

    img = qrcode.make(data)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    return send_file(buf, mimetype="image/png")

# 🟢 Página de verificación con cámara del celular
@app.route("/verify")
def verify_page():
    html = """
    <html>
    <head>
        <title>Verificador QR</title>
        <script src="https://unpkg.com/html5-qrcode" type="text/javascript"></script>
    </head>
    <body style="font-family:Arial; text-align:center; background:#f9f9f9;">
        <h2>📷 Verificador de QR</h2>
        <div id="reader" style="width:300px; margin:auto;"></div>
        <p id="result" style="font-size:20px; font-weight:bold; margin-top:20px;"></p>

        <script>
        function onScanSuccess(decodedText, decodedResult) {
            fetch('/check?data=' + encodeURIComponent(decodedText))
            .then(r => r.json())
            .then(d => {
                let result = document.getElementById("result");
                result.innerText = d.message;
                if(d.valid){
                    result.style.color = "green";
                } else {
                    result.style.color = "red";
                }
            });
        }

        function onScanError(errorMessage) {
            // ignorar errores para no saturar
        }

        let html5QrcodeScanner = new Html5QrcodeScanner(
            "reader", { fps: 10, qrbox: 250 });
        html5QrcodeScanner.render(onScanSuccess, onScanError);
        </script>
    </body>
    </html>
    """
    return render_template_string(html)

# 🟢 Validación del QR
@app.route("/check")
def check_qr():
    qrdata = request.args.get("data", "")
    try:
        house, date, secret = qrdata.split("|")
        today = datetime.date.today().strftime("%Y-%m-%d")

        # Validar secreto
        if secret != SECRET:
            return jsonify({"valid": False, "message": "❌ Código inválido"})

        # Validar fecha
        if date != today:
            return jsonify({"valid": False, "message": "⚠️ QR vencido"})

        # Validar casa
        status = AUTHORIZED_HOUSES.get(house, "desconocido")
        if status == "moroso":
            return jsonify({"valid": False, "message": f"⛔ Acceso denegado: {house} (moroso)"})
        elif status == "activo":
            return jsonify({"valid": True, "message": f"✅ Acceso permitido: {house}"})
        else:
            return jsonify({"valid": False, "message": f"❌ Casa no registrada: {house}"})

    except Exception:
        return jsonify({"valid": False, "message": "❌ Formato inválido"})

# 🟢 Modo local
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
