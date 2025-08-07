import os
import math
import shutil
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import importlib.util

# Load the existing module from a file path with a space in its name
MODULE_PATH = "/workspace/testiranje slik.py"
spec = importlib.util.spec_from_file_location("calc_mod", MODULE_PATH)
calc_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(calc_mod)

# Pull references from the loaded module
promocijski_material = getattr(calc_mod, "promocijski_material")
cenik_majice = getattr(calc_mod, "cenik_majice")
cenik_dtf = getattr(calc_mod, "cenik_dtf")
poisci_razpon = getattr(calc_mod, "poisci_razpon")
interpoliraj_ceno = getattr(calc_mod, "interpoliraj_ceno")
save_to_file = getattr(calc_mod, "save_to_file")


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Izračuni - Promocijski material in DTF")
        self.geometry("880x620")

        container = ttk.Notebook(self)
        container.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        self.tab_promo = PromoFrame(container)
        self.tab_dtf = DtfFrame(container)

        container.add(self.tab_promo, text="Promocijski material")
        container.add(self.tab_dtf, text="DTF tisk")


class PromoFrame(ttk.Frame):
    def __init__(self, parent) -> None:
        super().__init__(parent)

        # Inputs
        self.podjetje_var = tk.StringVar()
        self.artikel_var = tk.StringVar()
        self.kolicina_var = tk.StringVar()

        ttk.Label(self, text="Podjetje:").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        ttk.Entry(self, textvariable=self.podjetje_var, width=40).grid(row=0, column=1, sticky="w", padx=6, pady=6)

        ttk.Label(self, text="Artikel:").grid(row=1, column=0, sticky="w", padx=6, pady=6)
        artikel_combo = ttk.Combobox(self, textvariable=self.artikel_var, values=list(promocijski_material.keys()), state="readonly", width=37)
        artikel_combo.grid(row=1, column=1, sticky="w", padx=6, pady=6)
        if artikel_combo["values"]:
            artikel_combo.current(0)

        ttk.Label(self, text="Količina:").grid(row=2, column=0, sticky="w", padx=6, pady=6)
        ttk.Entry(self, textvariable=self.kolicina_var, width=20).grid(row=2, column=1, sticky="w", padx=6, pady=6)

        btns = ttk.Frame(self)
        btns.grid(row=3, column=0, columnspan=2, sticky="w", padx=6, pady=6)
        ttk.Button(btns, text="Izračunaj in shrani", command=self.izracunaj_in_shrani).pack(side=tk.LEFT, padx=4)

        # Output
        self.output = tk.Text(self, height=18)
        self.output.grid(row=4, column=0, columnspan=2, sticky="nsew", padx=6, pady=6)
        self.grid_rowconfigure(4, weight=1)
        self.grid_columnconfigure(1, weight=1)

    def izracunaj_in_shrani(self) -> None:
        podjetje = self.podjetje_var.get().strip()
        if not podjetje:
            messagebox.showerror("Napaka", "Ime podjetja je obvezno")
            return

        artikel = self.artikel_var.get().strip().lower()
        if artikel not in promocijski_material:
            messagebox.showerror("Napaka", "Izberi veljaven artikel")
            return

        try:
            kolicina = int(self.kolicina_var.get().strip())
            if kolicina <= 0:
                raise ValueError
        except Exception:
            messagebox.showerror("Napaka", "Količina mora biti pozitivno celo število")
            return

        cenik = promocijski_material[artikel]
        razpon = poisci_razpon(cenik, kolicina)
        if not razpon:
            messagebox.showerror("Napaka", "Količina izven razpona za izbrani artikel")
            return

        dobava = razpon["dobava"]
        prodaja = razpon["prodaja"]
        profit = round(prodaja - dobava, 2)
        cena_na_kos = round(prodaja / kolicina, 3) if kolicina else 0

        # Output
        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, f"Podjetje: {podjetje}\n")
        self.output.insert(tk.END, f"Artikel: {artikel.title()} | Količina: {kolicina}\n")
        self.output.insert(tk.END, f"Dobavna cena: {dobava} €\n")
        self.output.insert(tk.END, f"Prodajna cena: {prodaja} €\n")
        self.output.insert(tk.END, f"Profit: {profit} €\n")
        self.output.insert(tk.END, f"Cena na kos: {cena_na_kos} €\n")

        data = [
            f"Artikel: {artikel.title()}",
            f"Količina: {kolicina}",
            f"Dobavna cena: {dobava} €",
            f"Prodajna cena: {prodaja} €",
            f"Profit: {profit} €",
            f"Cena na kos: {cena_na_kos} €",
        ]
        save_to_file(podjetje, data, kolicina, artikel)


class DtfFrame(ttk.Frame):
    def __init__(self, parent) -> None:
        super().__init__(parent)

        self.podjetje_var = tk.StringVar()
        self.artikel_var = tk.StringVar()
        self.kolicina_var = tk.StringVar()
        self.pdf_path = None

        # Header inputs
        ttk.Label(self, text="Podjetje:").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        ttk.Entry(self, textvariable=self.podjetje_var, width=40).grid(row=0, column=1, sticky="w", padx=6, pady=6)

        ttk.Label(self, text="Oblačilni artikel:").grid(row=1, column=0, sticky="w", padx=6, pady=6)
        artikel_values = [r["ime"] for r in cenik_majice]
        artikel_values.insert(0, "ne potrebujem ga")
        artikel_combo = ttk.Combobox(self, textvariable=self.artikel_var, values=artikel_values, state="readonly", width=37)
        artikel_combo.grid(row=1, column=1, sticky="w", padx=6, pady=6)
        if artikel_combo["values"]:
            artikel_combo.current(0)

        ttk.Label(self, text="Skupna količina izdelkov:").grid(row=2, column=0, sticky="w", padx=6, pady=6)
        ttk.Entry(self, textvariable=self.kolicina_var, width=20).grid(row=2, column=1, sticky="w", padx=6, pady=6)

        # PDF attach
        ttk.Button(self, text="Priloži PDF", command=self.select_pdf).grid(row=0, column=2, padx=6, pady=6)
        self.pdf_label = ttk.Label(self, text="Ni izbranega PDF")
        self.pdf_label.grid(row=0, column=3, sticky="w", padx=6, pady=6)

        # Logos section
        ttk.Label(self, text="Logotipi (cm in kosi):").grid(row=3, column=0, sticky="w", padx=6, pady=6)
        self.logo_frame = ttk.Frame(self)
        self.logo_frame.grid(row=4, column=0, columnspan=4, sticky="nsew", padx=6, pady=6)
        self.grid_rowconfigure(4, weight=1)
        self.grid_columnconfigure(1, weight=1)

        header = ttk.Frame(self.logo_frame)
        header.pack(fill=tk.X)
        for idx, text in enumerate(["#", "Širina (cm)", "Višina (cm)", "Količina"]):
            ttk.Label(header, text=text, width=14).grid(row=0, column=idx, padx=2)

        self.logo_rows = []
        self.add_logo_row()

        ttk.Button(self, text="Dodaj logotip", command=self.add_logo_row).grid(row=5, column=0, padx=6, pady=6)
        ttk.Button(self, text="Izračunaj in shrani", command=self.izracunaj_in_shrani).grid(row=5, column=1, padx=6, pady=6)

        # Output
        self.output = tk.Text(self, height=16)
        self.output.grid(row=6, column=0, columnspan=4, sticky="nsew", padx=6, pady=6)
        self.grid_rowconfigure(6, weight=1)

    def select_pdf(self) -> None:
        path = filedialog.askopenfilename(title="Izberi PDF", filetypes=[("PDF datoteke", "*.pdf")])
        if path:
            self.pdf_path = path
            self.pdf_label.config(text=os.path.basename(path))

    def add_logo_row(self) -> None:
        row_frame = ttk.Frame(self.logo_frame)
        row_frame.pack(fill=tk.X, pady=2)
        index = len(self.logo_rows) + 1
        ttk.Label(row_frame, text=str(index), width=3).grid(row=0, column=0, padx=2)
        w_var = tk.StringVar()
        h_var = tk.StringVar()
        q_var = tk.StringVar()
        ttk.Entry(row_frame, textvariable=w_var, width=12).grid(row=0, column=1, padx=2)
        ttk.Entry(row_frame, textvariable=h_var, width=12).grid(row=0, column=2, padx=2)
        ttk.Entry(row_frame, textvariable=q_var, width=12).grid(row=0, column=3, padx=2)
        self.logo_rows.append((w_var, h_var, q_var))

    def izracunaj_in_shrani(self) -> None:
        podjetje = self.podjetje_var.get().strip()
        if not podjetje:
            messagebox.showerror("Napaka", "Ime podjetja je obvezno")
            return

        artikel_ime = self.artikel_var.get().strip().lower()

        try:
            skupna_kolicina = int(self.kolicina_var.get().strip())
            if skupna_kolicina <= 0:
                raise ValueError
        except Exception:
            messagebox.showerror("Napaka", "Skupna količina mora biti pozitivno celo število")
            return

        # Article cost
        if artikel_ime == "ne potrebujem ga":
            artikel_dobava = 0
            artikel_prodaja = 0
            cenik_izbira = None
        else:
            imena = [r["ime"].lower() for r in cenik_majice]
            if artikel_ime not in imena:
                messagebox.showerror("Napaka", "Neveljaven oblačilni artikel")
                return
            cenik_izbira = cenik_majice
            razpon = poisci_razpon(cenik_izbira, skupna_kolicina, artikel_ime)
            if not razpon:
                messagebox.showerror("Napaka", "Količina izven razpona za izbran artikel")
                return
            artikel_dobava = razpon["dobava"] * skupna_kolicina
            artikel_prodaja = razpon["prodaja"] * skupna_kolicina

        # Logos
        podrobnosti = []
        skupna_povrsina_cm2 = 0.0
        for idx, (w_var, h_var, q_var) in enumerate(self.logo_rows, start=1):
            if not (w_var.get().strip() and h_var.get().strip() and q_var.get().strip()):
                continue
            try:
                sirina = float(w_var.get().strip())
                visina = float(h_var.get().strip())
                kolicina = int(q_var.get().strip())
                if sirina <= 0 or visina <= 0 or kolicina <= 0:
                    raise ValueError
            except Exception:
                messagebox.showerror("Napaka", f"Vrstica #{idx}: napačni podatki")
                return

            # Layout calc matching CLI
            log_na_vrstico = math.floor(44 / sirina) if sirina > 0 else 0
            vrstic = math.ceil(kolicina / log_na_vrstico) if log_na_vrstico > 0 else 1
            visina_total = vrstic * visina

            rot_log_na_vrstico = math.floor(44 / visina) if visina > 0 else 0
            rot_vrstic = math.ceil(kolicina / rot_log_na_vrstico) if rot_log_na_vrstico > 0 else 1
            rot_visina_total = rot_vrstic * sirina

            if rot_visina_total < visina_total and rot_log_na_vrstico > 0:
                opis = (
                    f"Logotip #{idx}: {kolicina} × {visina}x{sirina} cm (ROTIRANO) → "
                    f"{rot_log_na_vrstico} na vrstico, {rot_vrstic} vrstic = {rot_visina_total:.2f} cm"
                )
            else:
                opis = (
                    f"Logotip #{idx}: {kolicina} × {sirina}x{visina} cm → "
                    f"{log_na_vrstico} na vrstico, {vrstic} vrstic = {visina_total:.2f} cm"
                )
            podrobnosti.append(opis)
            skupna_povrsina_cm2 += sirina * visina * kolicina

        if not podrobnosti:
            messagebox.showerror("Napaka", "Dodaj vsaj en veljaven logotip")
            return

        # DTF costs
        povrsinska_dolzina_m = skupna_povrsina_cm2 / (44 * 100)
        povrsinska_z_rezervo = round(povrsinska_dolzina_m + 0.2, 2)
        dtf_dobava, dtf_prodaja = interpoliraj_ceno(povrsinska_z_rezervo, cenik_dtf)

        skupna_dobava = round(dtf_dobava + artikel_dobava, 2)
        skupna_prodaja = round(dtf_prodaja + artikel_prodaja, 2)
        profit = round(skupna_prodaja - skupna_dobava, 2)
        cena_na_kos = round(skupna_prodaja / skupna_kolicina, 3) if skupna_kolicina else 0

        # Output
        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, f"Podjetje: {podjetje}\n")
        self.output.insert(tk.END, f"Artikel: {artikel_ime.title()}\n")
        self.output.insert(tk.END, f"Količina: {skupna_kolicina}\n")
        for v in podrobnosti:
            self.output.insert(tk.END, "  " + v + "\n")
        self.output.insert(tk.END, "\nDTF tisk:\n")
        self.output.insert(tk.END, f"  Referenčna dolžina: {povrsinska_z_rezervo} m\n")
        self.output.insert(tk.END, f"  Dobavna cena: {dtf_dobava} €\n")
        self.output.insert(tk.END, f"  Prodajna cena: {dtf_prodaja} €\n")
        if artikel_ime != "ne potrebujem ga":
            self.output.insert(tk.END, f"{artikel_ime.title()}:\n")
            self.output.insert(tk.END, f"  Dobavna cena: {artikel_dobava:.2f} €\n")
            self.output.insert(tk.END, f"  Prodajna cena: {artikel_prodaja:.2f} €\n")
        self.output.insert(tk.END, "Skupaj:\n")
        self.output.insert(tk.END, f"  Dobavna cena: {skupna_dobava} €\n")
        self.output.insert(tk.END, f"  Prodajna cena: {skupna_prodaja} €\n")
        self.output.insert(tk.END, f"  Profit: {profit} €\n")
        self.output.insert(tk.END, f"  Cena na kos: {cena_na_kos} €\n")

        # Save
        data = [
            f"Artikel: {artikel_ime.title()}",
            f"Količina: {skupna_kolicina}",
            *podrobnosti,
            "DTF tisk:",
            f"  Referenčna dolžina: {povrsinska_z_rezervo} m",
            f"  Dobavna cena: {dtf_dobava} €",
            f"  Prodajna cena: {dtf_prodaja} €",
        ]
        if artikel_ime != "ne potrebujem ga":
            data += [
                f"{artikel_ime.title()}:",
                f"  Dobavna cena: {artikel_dobava:.2f} €",
                f"  Prodajna cena: {artikel_prodaja:.2f} €",
            ]
        data += [
            "Skupaj:",
            f"  Dobavna cena: {skupna_dobava} €",
            f"  Prodajna cena: {skupna_prodaja} €",
            f"  Profit: {profit} €",
            f"  Cena na kos: {cena_na_kos} €",
        ]

        save_path = save_to_file(podjetje, data, skupna_kolicina, artikel_ime if artikel_ime != "ne potrebujem ga" else "dtf")
        if save_path and self.pdf_path:
            try:
                cilj_mapa = os.path.dirname(save_path)
                cilj_pdf = os.path.join(cilj_mapa, os.path.basename(self.pdf_path))
                shutil.copy2(self.pdf_path, cilj_pdf)
                messagebox.showinfo("Uspeh", f"PDF priložen: {cilj_pdf}")
            except Exception as e:
                messagebox.showwarning("Opozorilo", f"PDF ni bilo mogoče priložiti: {e}")


def main() -> None:
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()