from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

import customtkinter as ctk

from gui.styles import FONT_FAMILY


class SearchableCurrencyPicker(ctk.CTkFrame):
    def __init__(
        self,
        master: ctk.CTkBaseClass,
        title: str,
        values: list[str],
        on_select: Callable[[str], None],
    ) -> None:
        super().__init__(master, fg_color="transparent")
        self.values = values
        self.filtered_values = list(values)
        self.on_select = on_select
        self.current_value = values[0] if values else ""
        self.popup: ctk.CTkToplevel | None = None

        self.columnconfigure(0, weight=1)
        self.label = ctk.CTkLabel(self, text=title, anchor="w", font=(FONT_FAMILY, 13))
        self.label.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        self.button = ctk.CTkButton(
            self,
            text=self.current_value or "Select currency",
            command=self.open_popup,
            height=42,
            corner_radius=14,
            anchor="w",
            font=(FONT_FAMILY, 14),
        )
        self.button.grid(row=1, column=0, sticky="ew")

    def set_values(self, values: list[str]) -> None:
        self.values = values
        self.filtered_values = list(values)
        if self.current_value not in values and values:
            self.set(values[0], trigger=False)

    def set(self, value: str, trigger: bool = True) -> None:
        self.current_value = value
        self.button.configure(text=value)
        if trigger:
            self.on_select(value)

    def get(self) -> str:
        return self.current_value

    def open_popup(self) -> None:
        if self.popup and self.popup.winfo_exists():
            self.popup.focus()
            return

        self.popup = ctk.CTkToplevel(self)
        self.popup.title("Search currency")
        self.popup.geometry("360x420")
        self.popup.transient(self.winfo_toplevel())
        self.popup.grab_set()

        search_var = tk.StringVar()
        entry = ctk.CTkEntry(self.popup, textvariable=search_var, placeholder_text="Search by code or name")
        entry.pack(fill="x", padx=16, pady=(16, 10))

        listbox = tk.Listbox(
            self.popup,
            activestyle="none",
            font=(FONT_FAMILY, 12),
            bg="#172033",
            fg="#F3F4F6",
            selectbackground="#3B82F6",
            relief="flat",
            borderwidth=0,
        )
        listbox.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        def render(items: list[str]) -> None:
            listbox.delete(0, tk.END)
            for item in items:
                listbox.insert(tk.END, item)

        def filter_values(*_: object) -> None:
            query = search_var.get().strip().lower()
            self.filtered_values = [
                item for item in self.values if query in item.lower()
            ] or self.values[:]
            render(self.filtered_values)

        def select_current(_: object | None = None) -> None:
            if not listbox.curselection():
                return
            selected = self.filtered_values[listbox.curselection()[0]]
            self.set(selected)
            if self.popup:
                self.popup.destroy()

        render(self.values)
        search_var.trace_add("write", filter_values)
        listbox.bind("<Double-Button-1>", select_current)
        listbox.bind("<Return>", select_current)
        entry.focus()


class ResultCard(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkBaseClass) -> None:
        super().__init__(master, corner_radius=20)
        self.grid_columnconfigure(0, weight=1)

        self.title = ctk.CTkLabel(self, text="Converted Amount", font=(FONT_FAMILY, 14))
        self.title.grid(row=0, column=0, sticky="w", padx=20, pady=(18, 4))

        self.result_label = ctk.CTkLabel(self, text="--", font=(FONT_FAMILY, 30, "bold"))
        self.result_label.grid(row=1, column=0, sticky="w", padx=20)

        self.rate_label = ctk.CTkLabel(self, text="Live rate will appear here", font=(FONT_FAMILY, 13))
        self.rate_label.grid(row=2, column=0, sticky="w", padx=20, pady=(8, 4))

        self.meta_label = ctk.CTkLabel(self, text="Waiting for conversion", font=(FONT_FAMILY, 12))
        self.meta_label.grid(row=3, column=0, sticky="w", padx=20, pady=(0, 18))

    def update_content(self, result_text: str, rate_text: str, meta_text: str) -> None:
        self.result_label.configure(text=result_text)
        self.rate_label.configure(text=rate_text)
        self.meta_label.configure(text=meta_text)


class StatusBar(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkBaseClass) -> None:
        super().__init__(master, corner_radius=14, height=40)
        self.grid_columnconfigure(0, weight=1)
        self.message = ctk.CTkLabel(self, text="Ready", anchor="w", font=(FONT_FAMILY, 12))
        self.message.grid(row=0, column=0, sticky="ew", padx=14, pady=8)

    def set_status(self, text: str) -> None:
        self.message.configure(text=text)


class HistoryPanel(ctk.CTkScrollableFrame):
    def __init__(self, master: ctk.CTkBaseClass, on_use: Callable[[dict[str, str]], None]) -> None:
        super().__init__(master, corner_radius=18, label_text="Conversion History")
        self.on_use = on_use
        self.items: list[dict[str, str]] = []

    def render(self, history_items: list[dict[str, str]]) -> None:
        self.items = history_items
        for widget in self.winfo_children():
            widget.destroy()

        if not history_items:
            ctk.CTkLabel(self, text="No conversions yet.", font=(FONT_FAMILY, 12)).pack(anchor="w", padx=6, pady=8)
            return

        for row in history_items[:25]:
            text = f"{row['amount']} {row['from_currency']} -> {row['converted_amount']} {row['to_currency']}"
            button = ctk.CTkButton(
                self,
                text=text,
                anchor="w",
                height=38,
                corner_radius=12,
                command=lambda item=row: self.on_use(item),
            )
            button.pack(fill="x", pady=5, padx=4)
