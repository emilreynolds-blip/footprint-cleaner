from __future__ import annotations

import csv
import os
import sqlite3
import subprocess
import sys
import webbrowser
from datetime import datetime, timezone
from pathlib import Path
from tkinter import END, LEFT, RIGHT, BOTH, X, Y, filedialog, messagebox
import tkinter as tk
from tkinter import ttk
from urllib.parse import quote_plus


APP_NAME = "Footprint Cleaner"
APP_DIR = Path(os.getenv("LOCALAPPDATA", Path.home())) / "FootprintCleaner"
DB_PATH = APP_DIR / "footprint.db"

STATUSES = ("DISCOVERED", "VERIFY", "RECOVER", "REQUEST SENT", "FOLLOW UP", "REMOVED", "KEEP", "NOT ME")
PLATFORMS = {
    "Facebook": {
        "recovery": "https://www.facebook.com/login/identify",
        "compromised": "https://www.facebook.com/hacked",
        "privacy": "https://www.facebook.com/help/contact/507739850846588",
        "note": "Recovery or Meta identity verification is normally required before deletion.",
    },
    "Instagram": {
        "recovery": "https://www.instagram.com/hacked/",
        "privacy": "https://help.instagram.com/contact/505535973176353",
        "note": "Use login recovery; video-selfie verification may be offered for accounts showing your face.",
    },
    "WhatsApp": {
        "support": "https://www.whatsapp.com/contact/",
        "privacy": "https://www.whatsapp.com/contact/noclient/",
        "note": "Ask WhatsApp to disassociate/delete data tied to a number you no longer control. Never request codes sent to its current owner.",
    },
    "Viber": {
        "support": "https://help.viber.com/hc/en-us/requests/new",
        "privacy": "https://www.viber.com/en/terms/viber-privacy-policy/",
        "note": "Submit a privacy deletion request and document that the historical number is no longer controlled by you.",
    },
    "Google": {
        "removal": "https://myactivity.google.com/results-about-you",
        "note": "Remove at the source first, then request eligible search-result removal.",
    },
    "Other": {"note": "Locate the site's official privacy or account-recovery route."},
}


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class Store:
    def __init__(self) -> None:
        APP_DIR.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(DB_PATH)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS targets(
              id INTEGER PRIMARY KEY, platform TEXT NOT NULL, identifier TEXT NOT NULL,
              url TEXT DEFAULT '', access TEXT DEFAULT 'NO ACCESS', status TEXT DEFAULT 'DISCOVERED',
              protected INTEGER DEFAULT 0, notes TEXT DEFAULT '', created_at TEXT, updated_at TEXT
            );
            CREATE TABLE IF NOT EXISTS actions(
              id INTEGER PRIMARY KEY, target_id INTEGER, action TEXT, detail TEXT, created_at TEXT,
              FOREIGN KEY(target_id) REFERENCES targets(id)
            );
            """
        )
        if not self.db.execute("SELECT 1 FROM targets LIMIT 1").fetchone():
            seed = [
                ("Facebook", "Gim Tyme / gim.tyme", "https://www.facebook.com/gim.tyme/", "NO ACCESS", "RECOVER", 0, "Old email and phone unavailable"),
                ("Instagram", "flipp_beatz", "https://www.instagram.com/flipp_beatz", "UNKNOWN", "RECOVER", 0, "Confirm whether recognizable photos are present"),
                ("Facebook", "Taptical Conneissour's Club", "", "NO ACCESS", "DISCOVERED", 0, "Locate exact group URL and administrator status"),
                ("WhatsApp", "Historical phone association", "", "NO ACCESS", "VERIFY", 0, "Disassociate the former number; do not request SMS codes"),
                ("Viber", "Historical phone association", "", "NO ACCESS", "VERIFY", 0, "Submit privacy deletion request"),
                ("Other", "LinkedIn", "https://www.linkedin.com/", "ACCESS", "KEEP", 1, "Protected professional presence"),
            ]
            for row in seed:
                self.db.execute(
                    "INSERT INTO targets(platform,identifier,url,access,status,protected,notes,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)",
                    (*row, now(), now()),
                )
            self.db.commit()

    def targets(self):
        return self.db.execute("SELECT * FROM targets ORDER BY protected DESC, id").fetchall()

    def get(self, target_id: int):
        return self.db.execute("SELECT * FROM targets WHERE id=?", (target_id,)).fetchone()

    def add(self, platform, identifier, url, access, status, protected, notes):
        self.db.execute(
            "INSERT INTO targets(platform,identifier,url,access,status,protected,notes,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)",
            (platform, identifier, url, access, status, protected, notes, now(), now()),
        )
        self.db.commit()

    def update_status(self, target_id: int, status: str):
        self.db.execute("UPDATE targets SET status=?,updated_at=? WHERE id=?", (status, now(), target_id))
        self.db.execute("INSERT INTO actions(target_id,action,detail,created_at) VALUES(?,?,?,?)", (target_id, "STATUS", status, now()))
        self.db.commit()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("1120x700")
        self.minsize(900, 600)
        self.store = Store()
        self.selected_id: int | None = None
        self._style()
        self._ui()
        self.refresh()

    def _style(self):
        style = ttk.Style(self)
        if "vista" in style.theme_names():
            style.theme_use("vista")
        style.configure("Title.TLabel", font=("Segoe UI", 20, "bold"))
        style.configure("Sub.TLabel", font=("Segoe UI", 10))
        style.configure("Treeview", rowheight=28, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

    def _ui(self):
        top = ttk.Frame(self, padding=16)
        top.pack(fill=X)
        ttk.Label(top, text="Footprint Cleaner", style="Title.TLabel").pack(anchor="w")
        ttk.Label(top, text="Find, verify, remove, and track your public digital footprint. Protected items are never targeted.", style="Sub.TLabel").pack(anchor="w")

        bar = ttk.Frame(self, padding=(16, 0, 16, 10))
        bar.pack(fill=X)
        ttk.Button(bar, text="Add target", command=self.add_dialog).pack(side=LEFT, padx=(0, 6))
        ttk.Button(bar, text="Search selected", command=self.search_selected).pack(side=LEFT, padx=6)
        ttk.Button(bar, text="Official recovery / privacy route", command=self.open_route).pack(side=LEFT, padx=6)
        ttk.Button(bar, text="Create request letter", command=self.make_request).pack(side=LEFT, padx=6)
        ttk.Button(bar, text="Export audit", command=self.export).pack(side=RIGHT)

        body = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        body.pack(fill=BOTH, expand=True, padx=16, pady=(0, 16))
        left = ttk.Frame(body)
        right = ttk.Frame(body, padding=12)
        body.add(left, weight=3)
        body.add(right, weight=2)

        cols = ("platform", "identifier", "access", "status", "protected")
        self.tree = ttk.Treeview(left, columns=cols, show="headings", selectmode="browse")
        for col, width in zip(cols, (120, 270, 100, 110, 80)):
            self.tree.heading(col, text=col.title())
            self.tree.column(col, width=width, stretch=col == "identifier")
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        scroll = ttk.Scrollbar(left, orient="vertical", command=self.tree.yview)
        scroll.pack(side=RIGHT, fill=Y)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        ttk.Label(right, text="Selected target", font=("Segoe UI", 13, "bold")).pack(anchor="w")
        self.detail = tk.Text(right, wrap="word", height=18, font=("Segoe UI", 10), relief="flat", background="#f6f6f6", padx=10, pady=10)
        self.detail.pack(fill=BOTH, expand=True, pady=(8, 12))
        row = ttk.Frame(right)
        row.pack(fill=X)
        ttk.Label(row, text="Set status:").pack(side=LEFT)
        self.status = ttk.Combobox(row, values=STATUSES, state="readonly", width=18)
        self.status.pack(side=LEFT, padx=8)
        ttk.Button(row, text="Update", command=self.set_status).pack(side=LEFT)

        ttk.Label(self, text="Privacy note: Data stays on this computer. Never enter passwords, recovery codes, SSNs, or ID images.", padding=(16, 0, 16, 12)).pack(anchor="w")

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for r in self.store.targets():
            self.tree.insert("", END, iid=str(r["id"]), values=(r["platform"], r["identifier"], r["access"], r["status"], "YES" if r["protected"] else "NO"))

    def on_select(self, _event=None):
        selection = self.tree.selection()
        if not selection:
            return
        self.selected_id = int(selection[0])
        r = self.store.get(self.selected_id)
        route = PLATFORMS.get(r["platform"], PLATFORMS["Other"])
        text = f"Platform: {r['platform']}\nIdentifier: {r['identifier']}\nAccess: {r['access']}\nStatus: {r['status']}\nProtected: {'YES' if r['protected'] else 'NO'}\nURL: {r['url'] or 'Not recorded'}\n\nNotes\n{r['notes'] or 'None'}\n\nPlatform guidance\n{route.get('note','')}"
        self.detail.delete("1.0", END)
        self.detail.insert("1.0", text)
        self.status.set(r["status"])

    def require_selected(self):
        if not self.selected_id:
            messagebox.showinfo(APP_NAME, "Select a target first.")
            return None
        return self.store.get(self.selected_id)

    def search_selected(self):
        r = self.require_selected()
        if not r:
            return
        if r["protected"]:
            messagebox.showinfo(APP_NAME, "This item is protected. Search is allowed, but removal actions remain disabled.")
        q = quote_plus(f'"{r["identifier"]}" {r["platform"]}')
        webbrowser.open(f"https://www.google.com/search?q={q}")
        webbrowser.open(f"https://www.bing.com/search?q={q}")

    def open_route(self):
        r = self.require_selected()
        if not r:
            return
        if r["protected"]:
            messagebox.showwarning(APP_NAME, "Protected targets cannot enter removal workflows.")
            return
        route = PLATFORMS.get(r["platform"], PLATFORMS["Other"])
        urls = [v for k, v in route.items() if k != "note"]
        if not urls:
            webbrowser.open("https://www.google.com/search?q=" + quote_plus(f"{r['platform']} official privacy deletion request"))
        else:
            for url in urls:
                webbrowser.open(url)

    def make_request(self):
        r = self.require_selected()
        if not r:
            return
        if r["protected"]:
            messagebox.showwarning(APP_NAME, "Protected targets cannot generate deletion requests.")
            return
        template = f"""Subject: Ownership verification and deletion request — {r['identifier']}

I am requesting assistance concerning the {r['platform']} account or record identified as:
{r['identifier']}
{r['url']}

This is an older account or association belonging to me. I no longer have access to the historical email address or telephone number connected to it. I am willing to complete the platform's lawful identity and ownership-verification process. My purpose in recovering access is to permanently delete the account and associated personal data.

Please do not send verification codes to a telephone number I no longer control. Please provide an alternative identity-verification or privacy-request procedure.

I understand that I may need to provide identifying evidence directly through your secure official process. Please do not request passwords, authentication codes, or identity documents by ordinary email.

Sincerely,
[Your name]
[A current secure contact email]
"""
        path = filedialog.asksaveasfilename(defaultextension=".txt", initialfile=f"{r['platform']}_deletion_request.txt", filetypes=[("Text", "*.txt")])
        if path:
            Path(path).write_text(template, encoding="utf-8")
            messagebox.showinfo(APP_NAME, "Request letter created. Review it before submitting through the official channel.")

    def set_status(self):
        r = self.require_selected()
        if not r:
            return
        if r["protected"] and self.status.get() != "KEEP":
            messagebox.showwarning(APP_NAME, "Protected targets must remain KEEP unless protection is removed explicitly.")
            return
        self.store.update_status(r["id"], self.status.get())
        self.refresh()

    def add_dialog(self):
        win = tk.Toplevel(self)
        win.title("Add cleanup target")
        win.transient(self)
        win.grab_set()
        fields = {}
        for i, (label, default) in enumerate((("Platform", "Other"), ("Identifier", ""), ("Public URL", ""), ("Access", "NO ACCESS"), ("Notes", ""))):
            ttk.Label(win, text=label).grid(row=i, column=0, sticky="w", padx=12, pady=7)
            if label == "Platform":
                w = ttk.Combobox(win, values=tuple(PLATFORMS), state="readonly", width=42)
                w.set(default)
            else:
                w = ttk.Entry(win, width=45)
                w.insert(0, default)
            w.grid(row=i, column=1, padx=12, pady=7)
            fields[label] = w
        protected = tk.BooleanVar(value=False)
        ttk.Checkbutton(win, text="Protect / keep this item", variable=protected).grid(row=5, column=1, sticky="w", padx=12, pady=7)
        def save():
            if not fields["Identifier"].get().strip():
                messagebox.showerror(APP_NAME, "Identifier is required.")
                return
            self.store.add(fields["Platform"].get(), fields["Identifier"].get().strip(), fields["Public URL"].get().strip(), fields["Access"].get().strip(), "KEEP" if protected.get() else "DISCOVERED", int(protected.get()), fields["Notes"].get().strip())
            win.destroy(); self.refresh()
        ttk.Button(win, text="Save", command=save).grid(row=6, column=1, sticky="e", padx=12, pady=12)

    def export(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile="digital-footprint-audit.csv", filetypes=[("CSV", "*.csv")])
        if not path:
            return
        rows = self.store.targets()
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(rows[0].keys() if rows else ["id"])
            writer.writerows([tuple(r) for r in rows])
        messagebox.showinfo(APP_NAME, "Audit exported.")


if __name__ == "__main__":
    App().mainloop()
