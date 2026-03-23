
import qrcode, sys

url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000/attend"
img = qrcode.make(url)
img.save("attend_qr.png")
print(f"QR코드 생성 완료: attend_qr.png → {url}")
