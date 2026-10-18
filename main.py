import flet as ft
import sqlite3
import urllib.parse
import webbrowser

DB_NAME = "ricambi.db"

def esegui_query(query, params=()):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(query, params)
    risultati = c.fetchall()
    conn.close()
    return risultati

def esegui_comando(query, params=()):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(query, params)
    conn.commit()
    conn.close()

def main(page: ft.Page):
    page.title = "Gestione ricambi - Attrezzature Gi.Pi."
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0f172a"
    page.padding = 20

    righe_selezionate = set()
    entry_attiva = {"row": None, "col": None, "control": None}

    def carica_dati(filtro=""):
        if filtro:
            query = """
                SELECT a.id, a.matricola, a.codice_terminale, r.codice, r.descrizione, r.qta_disponibile, r.qta_ordinare
                FROM ricambi r JOIN attrezzature a ON a.id = r.id_attrezzatura
                WHERE a.id = ? OR r.codice LIKE ? OR r.descrizione LIKE ? OR a.codice_terminale LIKE ? OR a.matricola LIKE ?
                ORDER BY a.id, r.codice
            """
            return esegui_query(query, (filtro.upper(), f"%{filtro}%", f"%{filtro}%", f"%{filtro}%", f"%{filtro}%"))
        else:
            query = """
                SELECT a.id, a.matricola, a.codice_terminale, r.codice, r.descrizione, r.qta_disponibile, r.qta_ordinare
                FROM ricambi r JOIN attrezzature a ON a.id = r.id_attrezzatura
                ORDER BY a.id, r.codice LIMIT 100
            """
            return esegui_query(query)

    def on_row_select(e):
        e.control.selected = not e.control.selected
        if e.control.selected:
            righe_selezionate.add(e.control.data)
        else:
            righe_selezionate.discard(e.control.data)
        page.update()

    def abilita_modifica_in_linea(e):
        # Trova la riga e la colonna cliccata
        row_key = e.control.data
        col_index = e.control.data_index
        if col_index not in (5, 6): # Solo colonne 5 e 6 (Q.tà Disp e Q.tà Ord)
            return
        
        # Salva il riferimento
        entry_attiva["row"] = row_key
        entry_attiva["col"] = col_index
        
        # Crea un campo di testo
        valore_attuale = e.control.value
        entry = ft.TextField(
            value=str(valore_attuale), 
            width=80, 
            text_size=16, 
            bgcolor="#1e293b", 
            border_color="#38bdf8",
            on_submit=lambda ev: salva_modifica(ev, row_key, col_index)
        )
        entry_attiva["control"] = entry
        
        # Sostituisce il testo con il campo
        e.control.value = ""
        e.control.content = entry
        page.update()

    def salva_modifica(e, row, col):
        nuovo_valore = e.control.value
        try:
            nuovo_valore_int = int(nuovo_valore)
        except:
            nuovo_valore_int = 0
            
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        if col == 5:
            c.execute("UPDATE ricambi SET qta_disponibile = ? WHERE id_attrezzatura = ? AND codice = ? AND descrizione = ?", 
                      (nuovo_valore_int, row[0], row[3], row[4]))
        else:
            c.execute("UPDATE ricambi SET qta_ordinare = ? WHERE id_attrezzatura = ? AND codice = ? AND descrizione = ?", 
                      (nuovo_valore_int, row[0], row[3], row[4]))
        
        conn.commit()
        conn.close()
        
        # Ricarica la tabella per mostrare il nuovo valore
        esegui_ricerca(None)
        page.snack_bar = ft.SnackBar(ft.Text("Quantità aggiornata!"))
        page.snack_bar.open = True
        page.update()

    def costruisci_tabella(risultati):
        rows = []
        for i, item in enumerate(risultati):
            # Creiamo delle celle "Cliccabili" per le quantità
            cella_disp = ft.Text(str(item[5]), size=16, weight=ft.FontWeight.BOLD, color="#e2e8f0")
            cella_ord = ft.Text(str(item[6]), size=16, weight=ft.FontWeight.BOLD, color="#38bdf8")
            
            # Assegniamo un evento click manuale
            cella_disp.on_click = lambda e, item=item: abilita_modifica_in_linea(e)
            cella_ord.on_click = lambda e, item=item: abilita_modifica_in_linea(e)

            row = ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(str(item[0]), size=16, weight=ft.FontWeight.BOLD)),
                    ft.DataCell(ft.Text(str(item[1]), size=16)),
                    ft.DataCell(ft.Text(str(item[2]), size=16)),
                    ft.DataCell(ft.Text(str(item[3]), size=16)),
                    ft.DataCell(ft.Text(str(item[4]), size=16)),
                    ft.DataCell(cella_disp),
                    ft.DataCell(cella_ord),
                ],
                selected=False,
                on_select_change=on_row_select,
                data=item
            )
            rows.append(row)

        return ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Attrezzatura", size=16, weight=ft.FontWeight.BOLD, color="#94a3b8")),
                ft.DataColumn(ft.Text("Matricola", size=16, weight=ft.FontWeight.BOLD, color="#94a3b8")),
                ft.DataColumn(ft.Text("Codice Term.", size=16, weight=ft.FontWeight.BOLD, color="#94a3b8")),
                ft.DataColumn(ft.Text("Codice Ricambio", size=16, weight=ft.FontWeight.BOLD, color="#94a3b8")),
                ft.DataColumn(ft.Text("Descrizione", size=16, weight=ft.FontWeight.BOLD, color="#94a3b8")),
                ft.DataColumn(ft.Text("Q.tà Disp.", size=16, weight=ft.FontWeight.BOLD, color="#94a3b8")),
                ft.DataColumn(ft.Text("Q.tà Ord.", size=16, weight=ft.FontWeight.BOLD, color="#94a3b8")),
            ],
            rows=rows,
            heading_row_color="#1e293b",
            heading_row_height=50,
            data_row_min_height=50,
            data_row_max_height=50,
            data_row_color={"hovered": "#1e293b"},
            show_checkbox_column=True,
            column_spacing=20,
            border_radius=10,
            border=ft.Border.all(1, "#334155"),
        )

    table_container = ft.Container(
        content=costruisci_tabella(carica_dati()),
        bgcolor="#1e293b",
        border_radius=15,
        padding=10,
    )

    info_label = ft.Text("Pronto.", size=16, color="#94a3b8")

    def esegui_ricerca(e):
        filtro = search_field.value
        risultati = carica_dati(filtro)
        table_container.content = costruisci_tabella(risultati)
        info_label.value = f"Trovati {len(risultati)} risultati per '{filtro}'" if filtro else "Pronto."
        page.update()

    def apri_finestra_nuova_attrezzatura(e):
        def salva_attrezzatura(ev):
            id_att = input_id.value.strip().upper()
            mat = input_mat.value.strip()
            term = input_term.value.strip()
            if not id_att:
                page.snack_bar = ft.SnackBar(ft.Text("L'ID è obbligatorio!"))
                page.snack_bar.open = True
                page.update()
                return
            try:
                esegui_comando("INSERT OR REPLACE INTO attrezzature (id, matricola, codice_terminale) VALUES (?, ?, ?)", (id_att, mat, term))
                dlg.open = False
                page.snack_bar = ft.SnackBar(ft.Text(f"Attrezzatura {id_att} salvata!"))
                page.snack_bar.open = True
                page.update()
            except Exception as ex:
                page.snack_bar = ft.SnackBar(ft.Text(f"Errore: {ex}"))
                page.snack_bar.open = True
                page.update()

        input_id = ft.TextField(label="ID Attrezzatura (es. F200)", bgcolor="#0f172a")
        input_mat = ft.TextField(label="Matricola", bgcolor="#0f172a")
        input_term = ft.TextField(label="Codice Terminale", bgcolor="#0f172a")
        
        dlg = ft.AlertDialog(
            title=ft.Text("Nuova Attrezzatura"),
            content=ft.Column([input_id, input_mat, input_term], tight=True),
            actions=[
                ft.TextButton("Annulla", on_click=lambda e: chiudi_dialogo(dlg)),
                ft.Button("Salva", on_click=salva_attrezzatura, bgcolor="#0284c7")
            ]
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def apri_finestra_nuovo_ricambio(e):
        def salva_ricambio(ev):
            id_att = input_att.value.strip().upper()
            cod = input_cod.value.strip()
            descr = input_descr.value.strip()
            if not id_att or not descr:
                page.snack_bar = ft.SnackBar(ft.Text("ID e Descrizione obbligatori!"))
                page.snack_bar.open = True
                page.update()
                return
            check = esegui_query("SELECT id FROM attrezzature WHERE id = ?", (id_att,))
            if not check:
                page.snack_bar = ft.SnackBar(ft.Text(f"Attrezzatura '{id_att}' non trovata!"))
                page.snack_bar.open = True
                page.update()
                return
            try:
                esegui_comando("INSERT INTO ricambi (id_attrezzatura, codice, descrizione) VALUES (?, ?, ?)", (id_att, cod, descr))
                dlg.open = False
                page.snack_bar = ft.SnackBar(ft.Text("Ricambio aggiunto!"))
                page.snack_bar.open = True
                page.update()
            except Exception as ex:
                page.snack_bar = ft.SnackBar(ft.Text(f"Errore: {ex}"))
                page.snack_bar.open = True
                page.update()

        input_att = ft.TextField(label="ID Attrezzatura Esistente", bgcolor="#0f172a")
        input_cod = ft.TextField(label="Codice Ricambio", bgcolor="#0f172a")
        input_descr = ft.TextField(label="Descrizione", bgcolor="#0f172a")
        
        dlg = ft.AlertDialog(
            title=ft.Text("Nuovo Ricambio"),
            content=ft.Column([input_att, input_cod, input_descr], tight=True),
            actions=[
                ft.TextButton("Annulla", on_click=lambda e: chiudi_dialogo(dlg)),
                ft.Button("Salva", on_click=salva_ricambio, bgcolor="#0284c7")
            ]
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def chiudi_dialogo(dlg):
        dlg.open = False
        page.update()

    def invia_email(e):
        if not righe_selezionate:
            page.snack_bar = ft.SnackBar(ft.Text("Seleziona almeno un ricambio!"))
            page.snack_bar.open = True
            page.update()
            return

        corpo = "Buongiorno,\n\nsi richiede l'ordine dei seguenti ricambi:\n\n"
        for item in righe_selezionate:
            att, mat, term, cod, desc, qta_disp, qta_ord = item
            corpo += f"{att}-{mat}\tcod. {cod}-{desc}\tpz {qta_ord}\n"
        
        corpo += "\nGrazie,\n"
        
        oggetto = urllib.parse.quote("Ordine Ricambi")
        corpo_codificato = urllib.parse.quote(corpo)
        url = f"mailto:?subject={oggetto}&body={corpo_codificato}"
        
        webbrowser.open(url)
        
        page.snack_bar = ft.SnackBar(ft.Text("Email aperta nel client di posta!"))
        page.snack_bar.open = True
        page.update()

    search_field = ft.TextField(
        hint_text="Cerca...",
        height=50,
        text_size=16,
        bgcolor="#1e293b",
        border_color="#334155",
        border_radius=10,
        expand=True,
        on_submit=esegui_ricerca
    )

    search_button = ft.Button(
        content=ft.Text("🔍 Cerca", size=16, weight=ft.FontWeight.BOLD),
        on_click=esegui_ricerca,
        bgcolor="#0284c7",
        color="white",
        height=50,
        width=120,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
    )

    btn_nuova_att = ft.Button(
        content=ft.Text("➕ Nuova Attrezzatura", size=14, weight=ft.FontWeight.BOLD),
        on_click=apri_finestra_nuova_attrezzatura,
        bgcolor="#334155",
        color="white",
        height=40,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
    )

    btn_nuovo_ric = ft.Button(
        content=ft.Text("➕ Nuovo Ricambio", size=14, weight=ft.FontWeight.BOLD),
        on_click=apri_finestra_nuovo_ricambio,
        bgcolor="#334155",
        color="white",
        height=40,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
    )

    page.add(
        ft.Container(
            content=ft.Column([
                ft.Text("⚙️  Gestione ricambi - Attrezzature Gi.Pi.", size=28, weight=ft.FontWeight.BOLD, color="#38bdf8"),
                ft.Row([btn_nuova_att, btn_nuovo_ric], alignment=ft.MainAxisAlignment.START),
                ft.Divider(height=10, color="transparent"),
                ft.Row([search_field, search_button]),
                info_label,
                ft.Divider(height=10, color="transparent"),
                ft.Row([table_container], scroll=ft.ScrollMode.AUTO),
                ft.Divider(height=20, color="transparent"),
                ft.Row(
                    controls=[
                        ft.Button(
                            content=ft.Text("📧 Ordina (Email)", size=18, weight=ft.FontWeight.BOLD),
                            on_click=invia_email,
                            bgcolor="#0284c7",
                            color="white",
                            height=55,
                            width=250,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                )
            ]),
            padding=20,
        )
    )

if __name__ == "__main__":
    ft.run(main)