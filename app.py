from flask import Flask, request, jsonify, send_file, render_template_string
import qrcode
import io, os, csv

app = Flask(__name__)

# 📂 Cargar casas desde residents.csv
AUTHORIZED_HOUSES = {}
with open("residents.csv", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        AUTHORIZED_HOUSES[row["house"]] = {
            "status": row["status"],
            "secret": row["secret"]
        }

# 🟢 Generar QR para una casa
@app.route("/generate/<house>")
def generate_qr(house):
    house_info = AUTHORIZED_HOUSES.get(house)
    if not house_info:
        return "❌ Casa no registrada", 404

    # QR: casa|clave secreta
    data = f"{house}|{house_info['secret']}"
    img = qrcode.make(data)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png")

# 🟢 Página de verificación con cámara trasera
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
            // ignorar errores
        }

        // Forzar cámara trasera
        let html5QrCode = new Html5Qrcode("reader");
        Html5Qrcode.getCameras().then(devices => {
            if (devices && devices.length) {
                let backCamera = devices.find(device => device.label.toLowerCase().includes("back"))
                                || devices.find(device => device.label.toLowerCase().includes("environment"))
                                || devices[devices.length - 1]; // fallback
                html5QrCode.start(
                    backCamera.id,
                    { fps: 10, qrbox: 250 },
                    onScanSuccess,
                    onScanError
                );
            }
        }).catch(err => {
            console.error("No se pudo acceder a la cámara", err);
        });
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
        house, secret = qrdata.split("|")

        house_info = AUTHORIZED_HOUSES.get(house)
        if not house_info:
            return jsonify({"valid": False, "message": "❌ Casa no registrada"})

        if secret != house_info["secret"]:
            return jsonify({"valid": False, "message": "❌ Código inválido"})

        if house_info["status"] == "moroso":
            return jsonify({"valid": False, "message": f"⛔ Acceso denegado: {house} (moroso)"})
        elif house_info["status"] == "activo":
            return jsonify({"valid": True, "message": f"✅ Acceso permitido: {house}"})
        else:
            return jsonify({"valid": False, "message": f"❌ Estado desconocido: {house}"})

    except Exception:
        return jsonify({"valid": False, "message": "❌ Formato inválido"})

# 🟢 Modo local
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
