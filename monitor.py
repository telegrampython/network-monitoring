import requests
from netmiko import ConnectHandler
from datetime import datetime

TOKEN = "YOUR_TOKEN"           
CHAT_ID = "1125224994"

ROUTERS = [
    {"name": "R1", "host": "192.168.20.1"},
    {"name": "R2", "host": "192.168.40.1"},
    {"name": "R3", "host": "10.0.0.4"},    
]

USERNAME = "admin"
PASSWORD = "admin"

def send_telegram(msg: str):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

def check_router(r):
    device = {
        "device_type": "cisco_ios",
        "host": r["host"],
        "username": admin,
        "password": cisco123,
        "secret": PASSWORD,   # اگر enable secret جدا داری، این را عوض کن
        "timeout": 8,
    }

    try:
        conn = ConnectHandler(**device)
        # اگر enable لازم داری:
        try:
            conn.enable()
        except Exception:
            pass

        ip_int = conn.send_command("show ip interface brief")
        ospf_n = conn.send_command("show ip ospf neighbor")
        conn.disconnect()

        # 1) Interface Down؟
        down_lines = []
        for line in ip_int.splitlines():
            # line format: Interface IP-Address OK? Method Status Protocol
            if ("administratively down" in line) or ("down" in line and "up" not in line):
                if line.strip().startswith(("Gig", "Eth", "e", "Gi", "Fa")):
                    down_lines.append(line)

        # 2) OSPF Neighbor خالی؟
        ospf_problem = False
        if ("Neighbor ID" not in ospf_n) or ("FULL" not in ospf_n and "FULL/" not in ospf_n):
            # اگر هیچ FULL نبود، احتمال مشکل
            ospf_problem = True

        return {
            "ok": True,
            "ip_int": ip_int,
            "ospf": ospf_n,
            "down_lines": down_lines,
            "ospf_problem": ospf_problem,
        }

    except Exception as e:
        return {"ok": False, "error": str(e)}

def main():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    alerts = []

    for r in ROUTERS:
        res = check_router(r)

        if not res["ok"]:
            alerts.append(f"❌ {r['name']} unreachable ({r['host']})\n{res['error']}")
            continue

        if res["down_lines"]:
            alerts.append(f"⚠️ {r['name']} interface issue:\n" + "\n".join(res["down_lines"]))

        if res["ospf_problem"]:
            alerts.append(f"⚠️ {r['name']} OSPF neighbor problem:\n{res['ospf']}")

    if alerts:
        send_telegram(f"📡 Network Alert ({now})\n\n" + "\n\n".join(alerts))
    else:
        
        # send_telegram(f"✅ Network OK ({now})")
        pass

if __name__ == "__main__":
    main()
