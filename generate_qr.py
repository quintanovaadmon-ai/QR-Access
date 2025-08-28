import csv, os, json, hmac, hashlib, base64
from datetime import datetime, timezone, timedelta
import qrcode

# ---------------- CONFIGURACIÓN ----------------
SECRET = "cambia-esta-clave-super-secreta"
INPUT_CSV = "residents.csv"
OUTPUT_FOLDER = "QR_" + datetime.now().strftime("%Y-%m-%d")
EXP_HOUR = 23
EXP_MINUTE = 59
TZ_OFFSET_MINUTES = -360  # México CDMX UTC-6 / verano UTC-5
# ------------------------------------------------

def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode()

def sign(payload_dict: dict) -> str:
    body = json.dumps(payload_dict, separators=(',', ':'), sort_keys=True).encode()
    mac = hmac.new(SECRET.encode(), body, hashlib.sha256).digest()
    return b64url(mac)

def generate_qr(house_id: str) -> str:
    tz = timezone(timedelta(minutes=TZ_OFFSET_MINUTES))
    now_local = datetime.now(tz)
    exp_local = now_local.replace(hour=EXP_HOUR, minute=EXP_MINUTE, second=59, microsecond=0)
    if exp_local < now_local:
        exp_local += timedelta(days=1)
    exp_utc = exp_local.astimezone(timezone.utc).isoformat().replace("+00:00","Z")

    payload = {
        "v":1,
        "rid": house_id,
        "exp": exp_utc,
        "n": b64url(os.urandom(6))
    }
    payload["sig"] = sign(payload)

    qr_text = json.dumps(payload, separators=(',',':'))
    img = qrcode.make(qr_text)
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
    filename = f"{OUTPUT_FOLDER}/{house_id}.png"
    img.save(filename)
    return filename

# ---------------- GENERACIÓN MASIVA ----------------
with open(INPUT_CSV, newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        house_id = row["house_id"].strip()
        if house_id:
            file = generate_qr(house_id)
            print(f"QR generado: {file}")
