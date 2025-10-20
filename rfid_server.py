import serial
import time
import mysql.connector
from datetime import datetime


SERIAL_PORT = "COM5"
BAUDRATE = 9600

DB_CONFIG = {
    "host": "localhost",
    "user": "rfid_user",
    "password": "jelszo",
    "database": "rfid_db"
}

READ_TIMEOUT = 1


def open_serial():
    while True:
        try:
            s = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=READ_TIMEOUT)
            print(f"Sikeresen csatlakoztam a soros portra: {SERIAL_PORT}")
            return s
        except Exception as e:
            print("Hiba a soros port megnyitásakor:", e)
            time.sleep(2)


def normalize_uid(uid_str):
    s = uid_str.replace("0X", "").replace(":", " ").replace(",", " ").strip()
    parts = s.split()
    if len(parts) == 1 and len(parts[0]) % 2 == 0:
        s2 = parts[0]
        parts = [s2[i:i+2] for i in range(0, len(s2), 2)]
    return " ".join([p.upper() for p in parts])


ser = open_serial()

try:
    db = mysql.connector.connect(**DB_CONFIG)
    cursor = db.cursor()
except Exception as e:
    print("Nem sikerült kapcsolódni az adatbázishoz:", e)
    raise

print("RFID szerver elindult, várakozás a tagekre...")

while True:
    try:
        raw = ser.readline().decode(errors='ignore').strip()
        if not raw:
            continue
        print("Beolvasott sor:", raw)
        if raw.startswith("UID:"):
            uid_raw = raw[4:].strip()
            uid = normalize_uid(uid_raw)
            print("Normalizált UID:", uid)
            try:
                cursor.execute("SELECT nev FROM felhasznalok WHERE uid = %s", (uid,))
                row = cursor.fetchone()
            except Exception as e:
                print("SQL lekérdezési hiba:", e)
                row = None
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if row and row[0]:
                nev = row[0]
                try:
                    cursor.execute(
                        "INSERT INTO belepesek (nev, uid, idopont) VALUES (%s, %s, %s)",
                        (nev, uid, now)
                    )
                    db.commit()
                    ser.write(b"OK\n")
                    print(f"Belépés engedélyezve: {nev} ({uid}) - {now}")
                except Exception as e:
                    print("Hiba az INSERT során:", e)
            else:
                try:
                    cursor.execute(
                        "INSERT INTO belepesek (nev, uid, idopont) VALUES (%s, %s, %s)",
                        ("ISMERETLEN", uid, now)
                    )
                    db.commit()
                    ser.write(b"DENY\n")
                    print(f"Belépés megtagadva: ISMERETLEN ({uid}) - {now}")
                except Exception as e:
                    print("Hiba az INSERT (ISMERETLEN) során:", e)
    except serial.SerialException as e:
        print("Soros port hiba:", e)
        try:
            ser.close()
        except Exception:
            pass
        ser = open_serial()
    except mysql.connector.Error as e:
        print("MySQL hiba:", e)
        time.sleep(2)
    except Exception as e:
        print("Egyéb hiba:", e)
        time.sleep(0.5)
