from datetime import date, datetime, timedelta
import pandas as pd
import streamlit as st

from database import get_connection, init_db
from logic import get_all_participants_summary, get_planetary_boundaries_data

from database import get_connection, init_db
from logic import get_all_participants_summary, get_planetary_boundaries_data

# Alkalmazás és adatbázis inicializálása
init_db()

st.set_page_config(
    page_title="Takaró-elved Rendszer", page_icon="🌍", layout="wide"
)

st.markdown(
    """
    <style>
    .metric-card {
        background-color: #f4f6f5;
        border: 1px solid #d8e2dc;
        padding: 18px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
        margin-bottom: 12px;
    }
    .custom-container {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 14px;
        border: 1px solid #eef2f0;
        box-shadow: 0 2px 12px rgba(0,0,0,0.04);
        margin-bottom: 20px;
    }
    h1, h2, h3 {
        color: #2d3748;
    }
    </style>
""",
    unsafe_allow_html=True,
)

st.sidebar.title("🌍 Navigáció")
oldal = st.sidebar.selectbox(
    "Válassz oldalt:",
    [
        "Résztvevők (Áttekintés)",
        "Új résztvevő felvétele",
        "Aktivitás rögzítése",
        "Csomag vásárlása",
        "Bolygóhatárok monitor",
        "⚙ Admin / Katalógus szerkesztése",
    ],
)

conn = get_connection()
cursor = conn.cursor()

if oldal == "Résztvevők (Áttekintés)":
  st.title("👥 Résztvevők és Saját Ökológiai Mutatók")
  st.markdown(
      "Üdv a rendszerben! Itt nyomon követheted az egyes résztvevők ökológiai"
      " egyenlegét, az időalapú bázisokat, valamint a tételes aktivitási és"
      " csomagelőzményeket."
  )
  st.write("")

  résztvevők, adatok = get_all_participants_summary()

  if not résztvevők:
    st.info("Még nincsenek résztvevők. Vedd fel az elsőt a bal oldali menüben!")
  else:
    st.subheader("📊 Összesített rangsor és egyenlegek")
    df = pd.DataFrame(adatok)
    st.dataframe(df, use_container_width=True)

    st.divider()
    st.subheader("🔍 Résztvevő Részletes Profilja és Előzményei")

    valasztott_resztvevo = st.selectbox(
        "Válassz ki egy résztvevőt a fókuszált nézethez:",
        résztvevők,
        format_func=lambda x: x[1],
    )

    if valasztott_resztvevo:
      vr_id = valasztott_resztvevo[0]
      vr_nev = valasztott_resztvevo[1]
      kiv_adat = next(item for item in adatok if item["Sorszám"] == vr_id)

      st.markdown(f"### 👤 {vr_nev} *(Azonosító: {kiv_adat['ID']})*")
      m1, m2, m3, m4 = st.columns(4)
      with m1:
        st.metric(
            label="⚖️ Egyenleg (nap)", value=f"{kiv_adat['Egyenleg (nap)']}"
        )
      with m2:
        st.metric(
            label="🌿 Bioszféra Egyenleg",
            value=f"{kiv_adat['Bioszféra Egyenleg (nap)']}",
        )
      with m3:
        st.metric(
            label="⏳ Adósság törlesztés/év",
            value=f"{kiv_adat['Adósság törlesztése/év']} év",
        )
      with m4:
        st.metric(
            label="✨ Elkölthető napok", value=f"{kiv_adat['Elkölthető napok']}"
        )

      st.write("")
      col1, col2 = st.columns(2)

      with col1:
        st.markdown("<div class='custom-container'>", unsafe_allow_html=True)
        st.markdown(f"**🌱 {vr_nev} rögzített aktivitásai:**")
        cursor.execute(
            """
                SELECT dátum, aktivitás_neve, szerzett_nap, bolygó_határ 
                FROM tev_adatok 
                WHERE résztvevő_id = ? 
                ORDER BY dátum DESC
            """,
            (vr_id,),
        )
        tevek = cursor.fetchall()
        if tevek:
          df_tev = pd.DataFrame(
              tevek, columns=["Dátum", "Aktivitás", "Napok", "Kapcsolódó Határ"]
          )
          st.dataframe(df_tev, use_container_width=True, height=250)
        else:
          st.info("Még nincsenek rögzített aktivitások ehhez a személyhez.")
        st.markdown("</div>", unsafe_allow_html=True)

      with col2:
        st.markdown("<div class='custom-container'>", unsafe_allow_html=True)
        st.markdown(f"**📦 {vr_nev} megvásárolt csomagjai és fázisai:**")
        cursor.execute(
            """
                SELECT c.csomag_neve, c.terület, c.ar_napban, m.vásárlás_dátuma, c.passziv_hozam_naponta, c.bioszfera_haszon 
                FROM megvásárolt_csomagok m 
                JOIN csomagok c ON m.csomag_id = c.id 
                WHERE m.résztvevő_id = ?
            """,
            (vr_id,),
        )
        csom = cursor.fetchall()
        if csom:
          csom_feldolgozott = []
          for c_nev, c_ter, c_ar, v_datum, p_hozam, b_haszon in csom:
            if v_datum:
              eltelt_nap = (
                  date.today() - datetime.strptime(v_datum, "%Y-%m-%d").date()
              ).days
              if eltelt_nap < 1095:
                státusz = "1. Fázis: Türelmi idő (0-3 év)"
              elif eltelt_nap < 2555:
                státusz = "2. Fázis: Tőketörlesztés (3-7 év)"
              else:
                státusz = "3. Fázis: Passzív haszon & Robbanás (7 év+)"
            else:
              státusz = "Ismeretlen"

            csom_feldolgozott.append(
                {
                    "Csomag Neve": c_nev,
                    "Dátum": v_datum,
                    "Státusz": státusz,
                    "Ár (nap)": c_ar,
                    "Passzív Hozam": p_hozam,
                }
            )

          df_csom = pd.DataFrame(csom_feldolgozott)
          st.dataframe(df_csom, use_container_width=True, height=250)
        else:
          st.info("Még nincsenek vásárolt csomagok ehhez a személyhez.")
        st.markdown("</div>", unsafe_allow_html=True)

elif oldal == "Új résztvevő felvétele":
  st.title("➕ Új résztvevő regisztrálása")
  with st.form("uj_resztvevo_form"):
    uj_nev = st.text_input("Résztvevő neve:")
    submit = st.form_submit_button("Mentés")

    if submit:
      if uj_nev.strip() != "":
        try:
          cursor.execute(
              "INSERT INTO résztvevők (név) VALUES (?)", (uj_nev.strip(),)
          )
          conn.commit()
          st.success(f"Sikeresen hozzáadva: {uj_nev}!")
        except sqlite3.IntegrityError:
          st.warning("Ilyen nevű résztvevő már létezik!")
      else:
        st.error("Kérlek, adj meg egy nevet!")

elif oldal == "Aktivitás rögzítése":
  st.title("🌱 Aktivitás rögzítése")
  cursor.execute("SELECT id, név FROM résztvevők")
  resztvevok = cursor.fetchall()

  if not resztvevok:
    st.warning("Előbb hozz létre legalább egy résztvevőt!")
  else:
    cursor.execute(
        "SELECT aktivitás_neve, alap_nap, kategória FROM aktivitás_típusok"
    )
    aktivitasok = cursor.fetchall()

    if not aktivitasok:
      st.warning("Nincsenek elérhető aktivitások az admin katalógusban!")
    else:
      with st.form("tev_form"):
        resztvevo_valasztott = st.selectbox(
            "Válassz résztvevőt:", resztvevok, format_func=lambda x: x[1]
        )
        aktivitas_valasztott = st.selectbox(
            "Aktivitás típusa:", aktivitasok, format_func=lambda x: x[0]
        )

        min_datum = date.today() - timedelta(days=7)
        max_datum = date.today()
        valasztott_datum = st.date_input(
            "Aktivitás dátuma (legfeljebb 1 hétre visszamenőleg):",
            value=max_datum,
            min_value=min_datum,
            max_value=max_datum,
        )

        submit_tev = st.form_submit_button("Aktivitás rögzítése")

        if submit_tev:
          r_id = resztvevo_valasztott[0]
          akt_nev = aktivitas_valasztott[0]
          nap = aktivitas_valasztott[1]
          kategoria = aktivitas_valasztott[2]
          datum_str = valasztott_datum.strftime("%Y-%m-%d")

          cursor.execute(
              """
                    INSERT INTO tev_adatok (résztvevő_id, aktivitás_neve, szerzett_nap, dátum, bolygó_határ)
                    VALUES (?, ?, ?, ?, ?)
                """,
              (r_id, akt_nev, nap, datum_str, kategoria),
          )
          conn.commit()
          st.success(
              f"Sikeresen rögzítve ({datum_str})! {akt_nev}"
              f" ({'+' if nap>0 else ''}{nap:.2f} nap) hozzárendelve"
              f" {resztvevo_valasztott[1]} részére."
          )

elif oldal == "Csomag vásárlása":
  st.title("📦 Regeneráló csomag vásárlása")
  cursor.execute("SELECT id, név FROM résztvevők")
  resztvevok = cursor.fetchall()
  cursor.execute("SELECT id, csomag_neve, ar_napban FROM csomagok")
  csomagok = cursor.fetchall()

  if not resztvevok or not csomagok:
    st.warning("Szükséges hozzá résztvevő és elérhető csomag is!")
  else:
    with st.form("csomag_form"):
      r_valasztott = st.selectbox(
          "Vásárló:", resztvevok, format_func=lambda x: x[1]
      )
      cs_valasztott = st.selectbox(
          "Csomag:",
          csomagok,
          format_func=lambda x: f"{x[1]} ({x[2]:.2f} nap)",
      )
      submit_csomag = st.form_submit_button("Csomag megvásárlása")

      if submit_csomag:
        r_id = r_valasztott[0]
        cs_id = cs_valasztott[0]
        mai_datum = date.today().strftime("%Y-%m-%d")

        cursor.execute(
            """
                INSERT INTO megvásárolt_csomagok (résztvevő_id, csomag_id, vásárlás_dátuma)
                VALUES (?, ?, ?)
            """,
            (r_id, cs_id, mai_datum),
        )
        conn.commit()
        st.success(
            f"Sikeres csomagvásárlás! {cs_valasztott[1]} rögzítve"
            f" {r_valasztott[1]} számára a mai napon."
        )

elif oldal == "Bolygóhatárok monitor":
  st.title("🌐 Bolygóhatárok Élő Monitora (Év-alapú regenerációs bázis)")
  st.write(
      "A bolygói határ keretei, amelyek a becsült helyreállítási évek és az SRC"
      " túllépési százalékok alapján számolnak."
  )

  határ_lista = get_planetary_boundaries_data()
  df_hatar = pd.DataFrame(határ_lista)
  st.dataframe(df_hatar, use_container_width=True)

elif oldal == "⚙ Admin / Katalógus szerkesztése":
  st.title("⚙ Adminisztrációs felület - Kezelés és Finomhangolás")
  st.write(
      "Itt módosíthatod az aktivitások neveit és napértékeit, kezelheted a"
      " csomagokat, vagy törölhetsz résztvevőt."
  )

  tab1, tab2, tab3 = st.tabs(
      [
          "🌱 Aktivitás Típusok Kezelése",
          "📦 Csomagok Kezelése",
          "🗑️ Résztvevő Törlése",
      ]
  )

  with tab1:
    st.subheader("Meglévő aktivitások szerkesztése (Név, Nap, Kategória)")
    cursor.execute(
        "SELECT id, aktivitás_neve, alap_nap, kategória FROM aktivitás_típusok"
    )
    akt_lista = cursor.fetchall()

    with st.form("admin_akt_form"):
      frissitett_aktivitasok = {}
      for a_id, a_nev, a_nap, a_kat in akt_lista:
        col_n, col_p, col_k = st.columns([3, 2, 3])
        with col_n:
          uj_nev = st.text_input("Név", value=a_nev, key=f"akt_nev_{a_id}")
        with col_p:
          uj_nap = st.number_input(
              "Nap",
              value=float(a_nap),
              step=0.01,
              format="%.2f",
              key=f"akt_nap_{a_id}",
          )
        with col_k:
          uj_kat = st.text_input(
              "Kategória / Határ", value=a_kat, key=f"akt_kat_{a_id}"
          )
        frissitett_aktivitasok[a_id] = (uj_nev, uj_nap, uj_kat)
        st.divider()

      submit_akt = st.form_submit_button("Aktivitások mentése")
      if submit_akt:
        for a_id, (u_nev, u_nap, u_k) in frissitett_aktivitasok.items():
          cursor.execute(
              """
                        UPDATE aktivitás_típusok 
                        SET aktivitás_neve = ?, alap_nap = ?, kategória = ? 
                        WHERE id = ?
                    """,
              (u_nev, u_nap, u_k, a_id),
          )
        conn.commit()
        st.success("Az aktivitások adatai sikeresen frissültek!")
        st.rerun()

    st.subheader("➕ Új aktivitás hozzáadása")
    with st.form("uj_akt_form"):
      uj_a_nev = st.text_input("Új aktivitás neve:")
      uj_a_nap = st.number_input(
          "Alap napérték (akár két tizedessel):",
          value=1.0,
          step=0.01,
          format="%.2f",
      )
      uj_a_kat = st.text_input("Kapcsolódó kategória vagy bolygóhatár:")
      submit_uj_akt = st.form_submit_button("Új aktivitás rögzítése")

      if submit_uj_akt:
        if uj_a_nev.strip() and uj_a_kat.strip():
          try:
            cursor.execute(
                """
                            INSERT INTO aktivitás_típusok (aktivitás_neve, alap_nap, kategória)
                            VALUES (?, ?, ?)
                        """,
                (uj_a_nev.strip(), uj_a_nap, uj_a_kat.strip()),
            )
            conn.commit()
            st.success(f"Sikeresen létrehozva: {uj_a_nev.strip()}!")
            st.rerun()
          except sqlite3.IntegrityError:
            st.warning("Ilyen nevű aktivitás már létezik!")
        else:
          st.error(
              "Kérlek, töltsd ki az összes mezőt a név/kategória megadásához!"
          )

    st.subheader("🗑 Aktivitás törlése")
    with st.form("torol_akt_form"):
      cursor.execute("SELECT id, aktivitás_neve FROM aktivitás_típusok")
      minden_aktivitas = cursor.fetchall()
      kiv_torol_akt = st.selectbox(
          "Válaszd ki a törölni kívánt aktivitást:",
          minden_aktivitas,
          format_func=lambda x: x[1],
      )
      submit_torol_akt = st.form_submit_button("Kiválasztott aktivitás törlése")

      if submit_torol_akt:
        if kiv_torol_akt:
          cursor.execute(
              "DELETE FROM aktivitás_típusok WHERE id = ?", (kiv_torol_akt[0],)
          )
          conn.commit()
          st.success(
              f"A(z) '{kiv_torol_akt[1]}' aktivitás törölve a katalógusból!"
          )
          st.rerun()

  with tab2:
    st.subheader("Csomagok szerkesztése (Név, Ár, Hozamok)")
    cursor.execute(
        "SELECT id, csomag_neve, terület, ar_napban, passziv_hozam_naponta,"
        " bioszfera_haszon FROM csomagok"
    )
    csom_lista = cursor.fetchall()

    with st.form("admin_csom_form"):
      frissitett_csomagok = {}
      for c_id, c_nev, c_ter, c_ar, c_passz, c_biosz in csom_lista:
        st.markdown(f"**📦 {c_nev}** *(ID: {c_id})*")
        col0, col1, col2, col3, col4 = st.columns(5)
        with col0:
          uj_c_nev = st.text_input("Név", value=c_nev, key=f"c_nev_{c_id}")
        with col1:
          uj_ter = st.number_input(
              "Terület (m²)", value=float(c_ter), step=10.0, key=f"ter_{c_id}"
          )
        with col2:
          uj_ar = st.number_input(
              "Ár (nap)",
              value=float(c_ar),
              step=0.01,
              format="%.2f",
              key=f"ar_{c_id}",
          )
        with col3:
          uj_passz = st.number_input(
              "Passzív/nap",
              value=float(c_passz),
              step=1.0,
              key=f"passz_{c_id}",
          )
        with col4:
          uj_biosz = st.number_input(
              "Bioszféra/nap",
              value=float(c_biosz),
              step=10.0,
              key=f"biosz_{c_id}",
          )
        frissitett_csomagok[c_id] = (uj_c_nev, uj_ter, uj_ar, uj_passz, uj_biosz)

conn.close()