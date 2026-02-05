import flet as ft
import sqlite3
import datetime

# --- CONFIGURAZIONE ---
DB_NAME = "premi_famiglia.db"
GIORNI_SCADENZA = 5

def main(page: ft.Page):
    page.title = "Premi Famiglia"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 10
    page.scroll = "adaptive"  # Abilita lo scroll della pagina se serve

    # Variabili di stato
    visualizza_cestino = False
    
    # Liste Dati (Per i suggerimenti)
    suggerimenti_premi = ["Buono Spesa 5€", "Sconto 10%", "Giga Illimitati", "Buono Amazon"]
    suggerimenti_device = ["Smartphone Mamma", "Smartphone Papà", "Tablet Cucina"]

    # --- DATABASE ---
    def init_db():
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS premi
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      nome_premio TEXT,
                      dispositivo TEXT,
                      data_vincita DATE,
                      data_scadenza DATE,
                      usato INTEGER DEFAULT 0,
                      cancellato INTEGER DEFAULT 0)''')
        try: c.execute("ALTER TABLE premi ADD COLUMN cancellato INTEGER DEFAULT 0")
        except: pass
        conn.commit()
        conn.close()

    init_db()

    # --- LOGICA ---
    def calcola_giorni_rimasti(data_scadenza_str):
        oggi = datetime.date.today()
        scadenza = datetime.datetime.strptime(data_scadenza_str, "%Y-%m-%d").date()
        return (scadenza - oggi).days

    def get_color_for_row(giorni, usato):
        if usato: return ft.colors.WHITE
        # Colori VIVI (+20% saturazione)
        if giorni == 5: return ft.colors.LIGHT_BLUE_200
        if giorni == 4: return ft.colors.GREEN_ACCENT_400 # Verde molto acceso
        if giorni == 3: return ft.colors.YELLOW_400
        if giorni == 2: return ft.colors.ORANGE_400
        if giorni == 1: return ft.colors.RED_200
        if giorni == 0: return ft.colors.GREY_200
        if giorni < 0: return ft.colors.GREY_800 # Scaduto
        return ft.colors.WHITE

    def get_text_style_for_row(giorni, usato):
        colore_testo = ft.colors.BLACK
        peso = ft.FontWeight.NORMAL
        
        if giorni < 0 and not usato:
            colore_testo = ft.colors.WHITE
        elif giorni == 0 and not usato:
            colore_testo = ft.colors.RED_700 # Scritta rossa per oggi
            peso = ft.FontWeight.BOLD
        elif usato:
            colore_testo = ft.colors.GREY_500
            
        return colore_testo, peso

    # --- INTERFACCIA ---
    
    # Tabella
    tabella = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Dispositivo")),
            ft.DataColumn(ft.Text("Premio")),
            ft.DataColumn(ft.Text("Giorni"), numeric=True),
            ft.DataColumn(ft.Text("U")), # Usato
        ],
        rows=[],
        column_spacing=20,
    )

    # Campi Input (Dialogo)
    txt_premio = ft.TextField(label="Premio", hint_text="Es. Buono Amazon")
    # Qui usiamo un TextField così puoi scrivere quello che vuoi (Manuale)
    txt_dispositivo = ft.TextField(label="Dispositivo", hint_text="Es. Tablet") 
    txt_data = ft.TextField(label="Data (gg/mm/aaaa)", value=datetime.datetime.now().strftime("%d/%m/%Y"))

    def chiudi_dialogo(e):
        dlg_aggiungi.open = False
        page.update()

    def salva_premio(e):
        premio = txt_premio.value
        device = txt_dispositivo.value
        data_str = txt_data.value

        if not premio or not device:
            txt_premio.error_text = "Compila tutto"
            page.update()
            return

        try:
            dt_vincita = datetime.datetime.strptime(data_str, "%d/%m/%Y")
            dt_scadenza = dt_vincita + datetime.timedelta(days=GIORNI_SCADENZA)
            
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("INSERT INTO premi (nome_premio, dispositivo, data_vincita, data_scadenza) VALUES (?, ?, ?, ?)",
                      (premio, device, dt_vincita.strftime("%Y-%m-%d"), dt_scadenza.strftime("%Y-%m-%d")))
            conn.commit()
            conn.close()
            
            dlg_aggiungi.open = False
            carica_dati()
        except ValueError:
            txt_data.error_text = "Data errata"
            page.update()

    dlg_aggiungi = ft.AlertDialog(
        title=ft.Text("Nuovo Premio"),
        content=ft.Column([txt_premio, txt_dispositivo, txt_data], height=200),
        actions=[
            ft.TextButton("Annulla", on_click=chiudi_dialogo),
            ft.TextButton("Salva", on_click=salva_premio),
        ],
    )

    def apri_aggiungi(e):
        page.dialog = dlg_aggiungi
        dlg_aggiungi.open = True
        page.update()

    # --- GESTIONE RIGHE (Selezione e Click) ---
    def on_row_select(e, id_premio):
        # Simuliamo la selezione cambiando stato (semplificato per mobile: tap = azione)
        pass 

    def azione_elimina(id_premio):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        if visualizza_cestino:
            c.execute("DELETE FROM premi WHERE id = ?", (id_premio,)) # Elimina def.
        else:
            c.execute("UPDATE premi SET cancellato = 1 WHERE id = ?", (id_premio,))
        conn.commit()
        conn.close()
        carica_dati()

    def azione_usa(id_premio, stato_attuale):
        nuovo_stato = 0 if stato_attuale == 1 else 1
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("UPDATE premi SET usato = ? WHERE id = ?", (nuovo_stato, id_premio))
        conn.commit()
        conn.close()
        carica_dati()

    def azione_ripristina(id_premio):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("UPDATE premi SET cancellato = 0 WHERE id = ?", (id_premio,))
        conn.commit()
        conn.close()
        carica_dati()

    # Menu contestuale (bottom sheet) quando clicchi una riga
    def mostra_azioni(e, id_p, nome, usato):
        def elimina_click(e):
            azione_elimina(id_p)
            bs.open = False
            bs.update()
        
        def usa_click(e):
            azione_usa(id_p, usato)
            bs.open = False
            bs.update()

        def ripristina_click(e):
            azione_ripristina(id_p)
            bs.open = False
            bs.update()

        azioni = []
        if visualizza_cestino:
            azioni.append(ft.ListTile(leading=ft.Icon(ft.icons.RESTORE), title=ft.Text("Ripristina"), on_click=ripristina_click))
            azioni.append(ft.ListTile(leading=ft.Icon(ft.icons.DELETE_FOREVER, color=ft.colors.RED), title=ft.Text("Elimina Definitivamente"), on_click=elimina_click))
        else:
            txt_uso = "Segna come NUOVO" if usato else "Segna come USATO"
            icon_uso = ft.icons.UNDO if usato else ft.icons.CHECK
            azioni.append(ft.ListTile(leading=ft.Icon(icon_uso, color=ft.colors.BLUE), title=ft.Text(txt_uso), on_click=usa_click))
            azioni.append(ft.ListTile(leading=ft.Icon(ft.icons.DELETE, color=ft.colors.RED), title=ft.Text("Sposta nel Cestino"), on_click=elimina_click))

        bs = ft.BottomSheet(
            ft.Container(
                ft.Column(
                    [ft.Text(f"Azioni per: {nome}", weight="bold", size=16)] + azioni,
                    tight=True,
                ),
                padding=20,
            ),
        )
        page.overlay.append(bs)
        bs.open = True
        page.update()

    def carica_dati(e=None):
        tabella.rows.clear()
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        filtro_del = 1 if visualizza_cestino else 0
        c.execute("SELECT * FROM premi WHERE cancellato = ?", (filtro_del,))
        rows = c.fetchall()
        conn.close()

        # Ordinamento Python (Per Dispositivo)
        # Indice 2 è 'dispositivo'
        rows.sort(key=lambda x: x[2].lower())

        for row in rows:
            id_p, nome, device, vincita, scadenza, usato, cancellato = row
            giorni = calcola_giorni_rimasti(scadenza)
            
            # Colori e Stili
            bg_color = get_color_for_row(giorni, usato)
            text_color, weight = get_text_style_for_row(giorni, usato)
            
            marker_usato = "★" if usato else "" # Stella se usato

            # Creazione Cella con click
            # Usiamo on_long_press per il menu o tap sulla riga
            
            cells = [
                ft.DataCell(ft.Text(device, color=text_color, weight=weight)),
                ft.DataCell(ft.Text(nome, color=text_color, weight=weight)),
                ft.DataCell(ft.Text(str(giorni), color=text_color, weight=weight)),
                ft.DataCell(ft.Text(marker_usato, color=ft.colors.BLUE, weight="bold")),
            ]

            # In Flet la riga cliccabile si fa così
            data_row = ft.DataRow(
                cells=cells,
                color=ft.MaterialStateProperty.all(bg_color),
                on_select_changed=lambda e, i=id_p, n=nome, u=usato: mostra_azioni(e, i, n, u),
            )
            tabella.rows.append(data_row)
        
        page.update()

    def toggle_cestino(e):
        nonlocal visualizza_cestino
        visualizza_cestino = not visualizza_cestino
        btn_cestino.icon = ft.icons.DELETE_OUTLINE if not visualizza_cestino else ft.icons.HOME
        btn_cestino.tooltip = "Vai al Cestino" if not visualizza_cestino else "Torna alla Home"
        lb_titolo.value = "Cestino" if visualizza_cestino else "I Miei Premi"
        fab.visible = not visualizza_cestino
        carica_dati()

    # --- LAYOUT PRINCIPALE ---
    lb_titolo = ft.Text("I Miei Premi", size=20, weight="bold")
    btn_cestino = ft.IconButton(ft.icons.DELETE_OUTLINE, on_click=toggle_cestino, tooltip="Cestino")
    
    header = ft.Row([lb_titolo, btn_cestino], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
    
    # Contenitore scrollabile per la tabella
    table_container = ft.Column([tabella], scroll="adaptive", expand=True)

    fab = ft.FloatingActionButton(
        icon=ft.icons.ADD, bgcolor=ft.colors.BLUE, on_click=apri_aggiungi
    )

    page.add(header, table_container, fab)
    carica_dati()

ft.app(target=main, view=ft.WEB_BROWSER)
