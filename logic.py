from datetime import date, datetime
from database import get_connection


def get_all_participants_summary():
  conn = get_connection()
  cursor = conn.cursor()

  cursor.execute("SELECT id, név FROM résztvevők")
  résztvevők = cursor.fetchall()

  adatok = []
  for r_id, név in résztvevők:
    tp_id = f"TP{r_id:05d}"

    cursor.execute(
        "SELECT SUM(szerzett_nap) FROM tev_adatok WHERE résztvevő_id = ?",
        (r_id,),
    )
    res_tev = cursor.fetchone()[0]
    sum_tev = res_tev if res_tev is not None else 0.0

    cursor.execute(
        """
            SELECT c.ar_napban, c.bioszfera_haszon, m.vásárlás_dátuma, c.passziv_hozam_naponta 
            FROM megvásárolt_csomagok m 
            JOIN csomagok c ON m.csomag_id = c.id 
            WHERE m.résztvevő_id = ?
        """,
        (r_id,),
    )
    csomag_adatok = cursor.fetchall()

    sum_csomag_ar = sum(item[0] for item in csomag_adatok)
    sum_csomag_bioszfera = 0.0
    sum_passziv_hozam_osszeg = 0.0

    for ar, bh, v_datum, p_hozam in csomag_adatok:
      if v_datum:
        d_nap = (
            date.today() - datetime.strptime(v_datum, "%Y-%m-%d").date()
        ).days
        sum_csomag_bioszfera += (d_nap + 1) * bh

        for nap in range(d_nap + 1):
          sum_passziv_hozam_osszeg += p_hozam

    alap_egyenleg = sum_tev - sum_csomag_ar
    egyenleg = alap_egyenleg + sum_passziv_hozam_osszeg

    bioszfera_pont = -1000000 + sum_csomag_bioszfera + sum_tev

    tiszta_egyenleg = sum_tev + sum_passziv_hozam_osszeg
    ado_ev = round(tiszta_egyenleg / -365, 4) if tiszta_egyenleg != 0 else 0.0

    if egyenleg <= -3650.0:
      elkotheto = 30.41
      bolygo_limit = (
          "Egyensúlyi határ ( -3650 nap) elérve, csak törlesztés lehetséges"
      )
    else:
      elkotheto = max(0.0, round(3650 + egyenleg, 2))
      bolygo_limit = "Aktív keret"

    adatok.append(
        {
            "ID": tp_id,
            "Név": név,
            "Sorszám": r_id,
            "Egyenleg (nap)": round(egyenleg, 2),
            "Bioszféra Egyenleg (nap)": round(bioszfera_pont, 2),
            "Adósság törlesztése/év": f"{ado_ev:.4f}",
            "Elkölthető napok": round(elkotheto, 2),
            "Állapot": bolygo_limit,
        }
    )

  conn.close()
  return résztvevők, adatok


def get_planetary_boundaries_data():
  conn = get_connection()
  cursor = conn.cursor()

  cursor.execute(
      "SELECT id, határ_neve, százalék, kezdeti_keret, státusz FROM bolygó_határok"
  )
  határok = cursor.fetchall()

  határ_lista = []
  for h_id, h_nev, szazalek, kezdeti_keret, statusz in határok:
    kulcsszo = h_nev.split(".")[1].strip().split(" ")[0]

    cursor.execute(
        "SELECT SUM(szerzett_nap) FROM tev_adatok WHERE bolygó_határ LIKE ?",
        (f"%{kulcsszo}%",),
    )
    res = cursor.fetchone()[0]
    aktivitás_valtozas = res if res is not None else 0.0

    csomag_valtozas = 0.0
    if "Bioszféra" in h_nev:
      cursor.execute(
          "SELECT SUM((julianday('now') - julianday(m.vásárlás_dátuma) + 1) * c.bioszfera_haszon) FROM megvásárolt_csomagok m JOIN csomagok c ON m.csomag_id = c.id"
      )
      res_cs = cursor.fetchone()[0]
      csomag_valtozas = res_cs if res_cs is not None else 0.0

    ossz_nap = aktivitás_valtozas + csomag_valtozas
    ossz_ev = ossz_nap / 365.0
    aktualis_keret = kezdeti_keret + ossz_ev

    határ_lista.append(
        {
            "Bolygóhatár": h_nev,
            "Túllépés mértéke (SRC)": szazalek,
            "Kezdeti Keret / Évek (év)": round(kezdeti_keret, 2),
            "Aktivitások/Csomagok hatása (év)": round(ossz_ev, 5),
            "Aktuális Keret (év)": round(aktualis_keret, 5),
            "Státusz": statusz,
        }
    )

  conn.close()
  return határ_lista