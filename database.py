import sqlite3
from datetime import date

DB_NAME = "takaró_elved.db"


def get_connection():
  return sqlite3.connect(DB_NAME)


def init_db():
  conn = get_connection()
  cursor = conn.cursor()

  # 1. Résztvevők tábla
  cursor.execute(
      """
        CREATE TABLE IF NOT EXISTS résztvevők (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            név TEXT UNIQUE NOT NULL
        )
    """
  )

  # 2. Aktivitás Típusok katalógus
  cursor.execute(
      """
        CREATE TABLE IF NOT EXISTS aktivitás_típusok (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            aktivitás_neve TEXT UNIQUE NOT NULL,
            alap_nap REAL NOT NULL,
            kategória TEXT NOT NULL
        )
    """
  )

  # 3. Csomagok tábla
  cursor.execute(
      """
        CREATE TABLE IF NOT EXISTS csomagok (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            csomag_neve TEXT UNIQUE NOT NULL,
            terület REAL NOT NULL,
            ar_napban INTEGER NOT NULL,
            passziv_hozam_naponta REAL NOT NULL,
            bioszfera_haszon REAL NOT NULL
        )
    """
  )

  # 4. Tev_Adatok (Aktivitások naplója)
  cursor.execute(
      """
        CREATE TABLE IF NOT EXISTS tev_adatok (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            résztvevő_id INTEGER,
            aktivitás_neve TEXT,
            szerzett_nap REAL,
            dátum TEXT,
            bolygó_határ TEXT,
            FOREIGN KEY(résztvevő_id) REFERENCES résztvevők(id)
        )
    """
  )

  # 5. Megvásárolt Csomagok tábla
  cursor.execute(
      """
        CREATE TABLE IF NOT EXISTS megvásárolt_csomagok (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            résztvevő_id INTEGER,
            csomag_id INTEGER,
            vásárlás_dátuma TEXT,
            FOREIGN KEY(résztvevő_id) REFERENCES résztvevők(id),
            FOREIGN KEY(csomag_id) REFERENCES csomagok(id)
        )
    """
  )

  # 6. Bolygóhatárok tábla
  cursor.execute("DROP TABLE IF EXISTS bolygó_határok")
  cursor.execute(
      """
        CREATE TABLE bolygó_határok (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            határ_neve TEXT UNIQUE NOT NULL,
            százalék TEXT NOT NULL,
            kezdeti_keret REAL NOT NULL,
            státusz TEXT NOT NULL
        )
    """
  )

  # 7. Admin tábla
  cursor.execute(
      """
        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            felhasználónév TEXT UNIQUE NOT NULL,
            jelszó_hash TEXT NOT NULL,
            utolsó_bejelentkezés TEXT,
            szerepkör TEXT NOT NULL
        )
    """
  )

  # Kezdeti admin feltöltése, ha üres
  cursor.execute("SELECT COUNT(*) FROM admin")
  if cursor.fetchone()[0] == 0:
    cursor.execute(
        """
            INSERT INTO admin (felhasználónév, jelszó_hash, utolsó_bejelentkezés, szerepkör)
            VALUES (?, ?, ?, ?)
        """,
        (
            "főadmin",
            "default_hash_elerheto",
            date.today().strftime("%Y-%m-%d"),
            "főadmin",
        ),
    )

  # Kezdeti aktivitások feltöltése
  cursor.execute("SELECT COUNT(*) FROM aktivitás_típusok")
  if cursor.fetchone()[0] == 0:
    alap_aktivitások = [
        (
            "Mélymulcsos kertészkedés / Komposztálás (1 óra)",
            1.0,
            "Bioszféra integritása",
        ),
        ("Helyi ökológiai termék vásárlása (1 óra)", 1.0, "Klímaváltozás"),
        ("Zero waste / Vegyszermentes háztartás (1 óra)", 1.0, "Új entitások"),
        ("Természetjárás / Séta (1 óra)", 1.0, "Egyéni jóllét"),
        ("Meditáció / Csend (1 óra)", 1.0, "Egyéni jóllét"),
        ("Ökológiai olvasás / Tanulás (1 óra)", 1.0, "Egyéni jóllét"),
        ("Görkorcsolyázás / Mozgás (1 óra)", 1.0, "Egyéni jóllét"),
        ("Fosszilis alapú / Interkontinentális utazás", -30.0, "Klímaváltozás"),
    ]
    cursor.executemany(
        """
            INSERT OR IGNORE INTO aktivitás_típusok (aktivitás_neve, alap_nap, kategória)
            VALUES (?, ?, ?)
        """,
        alap_aktivitások,
    )

  # Csomagok feltöltése
  cursor.execute("SELECT COUNT(*) FROM csomagok")
  if cursor.fetchone()[0] == 0:
    alap_csomagok = [
        ("Biodiverzitás Oázis Csomag", 300.0, 1000, 6.0, 120.0),
        ("Illatos / Hasznos Kerti Csomag", 150.0, 1000, 6.0, 120.0),
        ("Mikrobiális Regeneráló Csomag", 100.0, 1000, 5.0, 100.0),
    ]
    cursor.executemany(
        """
            INSERT OR IGNORE INTO csomagok (csomag_neve, terület, ar_napban, passziv_hozam_naponta, bioszfera_haszon)
            VALUES (?, ?, ?, ?, ?)
        """,
        alap_csomagok,
    )

  # Bolygóhatárok feltöltése
  alap_határok = [
      ("1. Klímaváltozás", "-21%", -300.0, "🔴 Átlépve"),
      ("2. Bioszféra integritása", "> -900% / -200%", -350.0, "🔴 Átlépve"),
      ("3. Új entitások", "Határ átlépve", -1570.0, "🔴 Átlépve"),
      ("4. Biogeokémiai áramlások", "-166% / -194%", -20.0, "🔴 Átlépve"),
      ("5. Földhasználat megváltoztatása", "-173%", -150.0, "🔴 Átlépve"),
      ("6. Édesvíz-felhasználás", "-77% / -75%", -50.0, "🔴 Átlépve"),
      ("7. Óceánok savasodása", "- 0,7%", -300.0, "🔴 Átlépve"),
      ("8. Atmoszférikus aeroszolok", "37% (Nem túllépett)", 0.2, "🟢 Biztonságos"),
      ("9. Stratoszférikus ózon", "95% (Nem túllépett)", 10.0, "🟢 Biztonságos"),
  ]
  cursor.executemany(
      """
        INSERT INTO bolygó_határok (határ_neve, százalék, kezdeti_keret, státusz)
        VALUES (?, ?, ?, ?)
    """,
      alap_határok,
  )

  conn.commit()
  conn.close()