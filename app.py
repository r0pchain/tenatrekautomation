from flask import Flask, request, jsonify, render_template
import bluetooth
import time

app = Flask(__name__)

DEVICE_MAC = "98:98:98:98:98:98"

commands = {
    "saucer": "*SAUCER#",
    "secondary": "*SEC#",
    "neck": "*NECK#",
    "chiller": "*CHILLER#",
    "nav": "*NAV#",
    "strobe": "*STROBE#",
    "impulse": "*IMP#",
    "deflector": "*DFLCT#",
    "photon": "*PHOTON#",
    "phaser": "*PHASER#",
    "warp": "*WARP#",
    "play1": "*PLAY1$",
    "play2": "*PLAY2$",
    "play3": "*PLAY3$",
    "play4": "*PLAY4$",
    "play5": "*PLAY5$",
    "play6": "*PLAY6$",
    "play7": "*PLAY7$",
    "play8": "*PLAY8$",
    "play9": "*PLAY9$",
    "play10": "*PLAY10$",
}

def send_command(command):
    try:
        sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        sock.connect((DEVICE_MAC, 3))
        sock.send(command)
        sock.close()
        return f"Sent: {command}"
    except bluetooth.btcommon.BluetoothError as e:
        return f"Bluetooth error: {e}"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/send", methods=["POST"])
def send():
    data = request.json
    command_key = data.get("command")

    if command_key not in commands and command_key not in ["demo", "lightup"]:
        return jsonify({"error": "Invalid command"}), 400

    if command_key == "demo":
        sequence = ["play1", "secondary", "saucer", "neck", "chiller", "nav", "strobe", "impulse", "deflector"]
    elif command_key == "lightup":
        sequence = ["saucer", "secondary", "neck", "chiller", "nav", "strobe", "impulse", "deflector"]
    else:
        sequence = [command_key]

    results = []
    for cmd in sequence:
        result = send_command(commands[cmd])
        results.append(result)
        time.sleep(0.5)  # 500ms delay between commands

    return jsonify({"message": f"{command_key} sequence executed", "results": results})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=1701)

