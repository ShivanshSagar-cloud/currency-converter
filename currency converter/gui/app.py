from __future__ import annotations

import logging
import threading
import tkinter as tk
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk
from PIL import Image

from api.exchange_service import ExchangeServiceError
from config import (
    APP_NAME,
    APP_VERSION,
    ASSETS_DIR,
    DEFAULT_BASE_CURRENCY,
    DEFAULT_TARGET_CURRENCY,
    WINDOW_DEFAULT_HEIGHT,
    WINDOW_DEFAULT_WIDTH,
    WINDOW_MIN_HEIGHT,
    WINDOW_MIN_WIDTH,
)
from gui.components import HistoryPanel, ResultCard, SearchableCurrencyPicker, StatusBar
from gui.styles import DARK_THEME, FONT_FAMILY, LIGHT_THEME
from models.conversion import ConversionRequest, ConversionResult
from models.settings import AppSettings
from services.converter_service import ConverterService
from services.settings_service import SettingsService
from utils.formatters import format_money, format_timestamp
from utils.validators import parse_amount

LOGGER = logging.getLogger(__name__)


class CurrencyConverterApp(ctk.CTk):
    def __init__(self, converter_service: ConverterService, settings_service: SettingsService) -> None:
        super().__init__()
        self.converter_service = converter_service
        self.settings_service = settings_service
        self.settings = self.settings_service.load()
        self.currency_values: list[str] = []
        self.loading = False
        self.auto_refresh_job: str | None = None
        self.latest_result: ConversionResult | None = None

        ctk.set_appearance_mode(self.settings.theme)
        ctk.set_default_color_theme("blue")

        self.title(f"{APP_NAME} {APP_VERSION}")
        self.geometry(f"{WINDOW_DEFAULT_WIDTH}x{WINDOW_DEFAULT_HEIGHT}")
        self.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self._set_window_icon()

        self.amount_var = tk.StringVar(value="100")
        self.rate_var = tk.StringVar(value="Rate: --")
        self.updated_var = tk.StringVar(value="Last updated: --")
        self.status_var = tk.StringVar(value="Loading currency list...")

        self.theme_colors = DARK_THEME if self.settings.theme == "dark" else LIGHT_THEME
        self.configure(fg_color=self.theme_colors["bg"])

        self._build_layout()
        self._bind_shortcuts()
        self._load_logo()
        self._set_loading(True, "Loading currency list...")
        self._load_currencies_async()

    def _build_layout(self) -> None:
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        self.main_frame = ctk.CTkFrame(self, corner_radius=24)
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=(18, 10), pady=18)
        self.main_frame.grid_columnconfigure((0, 1), weight=1)

        self.side_frame = ctk.CTkFrame(self, corner_radius=24)
        self.side_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 18), pady=18)
        self.side_frame.grid_rowconfigure(1, weight=1)
        self.side_frame.grid_columnconfigure(0, weight=1)

        self.header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=24, pady=(24, 12))
        self.header_frame.grid_columnconfigure(1, weight=1)

        self.logo_label = ctk.CTkLabel(self.header_frame, text="", width=56)
        self.logo_label.grid(row=0, column=0, rowspan=2, padx=(0, 14))

        ctk.CTkLabel(
            self.header_frame,
            text=APP_NAME,
            font=(FONT_FAMILY, 28, "bold"),
        ).grid(row=0, column=1, sticky="w")

        ctk.CTkLabel(
            self.header_frame,
            text="Live rates, offline fallback, synchronized terminal output",
            font=(FONT_FAMILY, 13),
        ).grid(row=1, column=1, sticky="w", pady=(4, 0))

        self.amount_entry = ctk.CTkEntry(
            self.main_frame,
            textvariable=self.amount_var,
            placeholder_text="Enter amount",
            height=54,
            corner_radius=18,
            font=(FONT_FAMILY, 20),
        )
        self.amount_entry.grid(row=1, column=0, columnspan=2, sticky="ew", padx=24, pady=(0, 18))

        self.progress_bar = ctk.CTkProgressBar(self.main_frame, mode="indeterminate", height=8)
        self.progress_bar.grid(row=2, column=0, columnspan=2, sticky="ew", padx=24, pady=(0, 12))
        self.progress_bar.stop()
        self.progress_bar.grid_remove()

        self.from_picker = SearchableCurrencyPicker(self.main_frame, "From Currency", [], self._on_picker_select)
        self.from_picker.grid(row=3, column=0, sticky="ew", padx=(24, 10), pady=(0, 12))

        self.to_picker = SearchableCurrencyPicker(self.main_frame, "To Currency", [], self._on_picker_select)
        self.to_picker.grid(row=3, column=1, sticky="ew", padx=(10, 24), pady=(0, 12))

        self.actions_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.actions_frame.grid(row=4, column=0, columnspan=2, sticky="ew", padx=24, pady=(4, 16))
        for index in range(5):
            self.actions_frame.grid_columnconfigure(index, weight=1)

        self.swap_button = ctk.CTkButton(self.actions_frame, text="Swap", command=self.swap_currencies, corner_radius=14)
        self.swap_button.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self.convert_button = ctk.CTkButton(self.actions_frame, text="Convert", command=self.convert_async, corner_radius=14)
        self.convert_button.grid(row=0, column=1, sticky="ew", padx=8)

        self.clear_button = ctk.CTkButton(self.actions_frame, text="Clear", command=self.clear_inputs, corner_radius=14)
        self.clear_button.grid(row=0, column=2, sticky="ew", padx=8)

        self.copy_button = ctk.CTkButton(self.actions_frame, text="Copy", command=self.copy_result, corner_radius=14)
        self.copy_button.grid(row=0, column=3, sticky="ew", padx=8)

        self.settings_button = ctk.CTkButton(self.actions_frame, text="Settings", command=self.open_settings_window, corner_radius=14)
        self.settings_button.grid(row=0, column=4, sticky="ew", padx=(8, 0))

        self.rate_label = ctk.CTkLabel(self.main_frame, textvariable=self.rate_var, font=(FONT_FAMILY, 14))
        self.rate_label.grid(row=5, column=0, columnspan=2, sticky="w", padx=24)

        self.updated_label = ctk.CTkLabel(self.main_frame, textvariable=self.updated_var, font=(FONT_FAMILY, 12))
        self.updated_label.grid(row=6, column=0, columnspan=2, sticky="w", padx=24, pady=(4, 18))

        self.result_card = ResultCard(self.main_frame)
        self.result_card.grid(row=7, column=0, columnspan=2, sticky="ew", padx=24, pady=(0, 18))

        self.status_bar = StatusBar(self.main_frame)
        self.status_bar.grid(row=8, column=0, columnspan=2, sticky="ew", padx=24, pady=(0, 24))

        self.side_header = ctk.CTkFrame(self.side_frame, fg_color="transparent")
        self.side_header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        self.side_header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self.side_header, text="Favorites", font=(FONT_FAMILY, 18, "bold")).grid(row=0, column=0, sticky="w")
        self.theme_switch = ctk.CTkSwitch(
            self.side_header,
            text="Dark mode",
            command=self.toggle_theme,
        )
        self.theme_switch.grid(row=0, column=1, sticky="e")
        if self.settings.theme == "dark":
            self.theme_switch.select()

        self.favorite_frame = ctk.CTkFrame(self.side_frame, corner_radius=18)
        self.favorite_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 14))
        self.favorite_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.history_panel = HistoryPanel(self.side_frame, self.use_history_item)
        self.history_panel.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))

    def _load_logo(self) -> None:
        logo_path = ASSETS_DIR / "logo.png"
        if not logo_path.exists():
            self.logo_label.configure(text="FX", font=(FONT_FAMILY, 24, "bold"))
            return

        image = Image.open(logo_path).resize((52, 52))
        self.logo_image = ctk.CTkImage(light_image=image, dark_image=image, size=(52, 52))
        self.logo_label.configure(image=self.logo_image, text="")

    def _set_window_icon(self) -> None:
        icon_path = ASSETS_DIR / "icons" / "app.ico"
        if icon_path.exists():
            try:
                self.iconbitmap(default=str(icon_path))
            except tk.TclError:
                LOGGER.debug("Unable to apply window icon.", exc_info=True)

    def _bind_shortcuts(self) -> None:
        self.bind("<Return>", lambda _: self.convert_async())
        self.bind("<Control-s>", lambda _: self.swap_currencies())
        self.bind("<Control-l>", lambda _: self.clear_inputs())
        self.bind("<Control-c>", lambda _: self.copy_result())

    def _set_loading(self, is_loading: bool, status: str) -> None:
        self.loading = is_loading
        state = "disabled" if is_loading else "normal"
        self.convert_button.configure(state=state)
        self.swap_button.configure(state=state)
        if is_loading:
            self.progress_bar.grid()
            self.progress_bar.start()
        else:
            self.progress_bar.stop()
            self.progress_bar.grid_remove()
        self.status_bar.set_status(status)

    def _load_currencies_async(self) -> None:
        def worker() -> None:
            try:
                currencies = self.converter_service.load_currencies()
                values = [currency.display_name for currency in currencies]
                self.after(0, lambda: self._apply_currency_values(values))
            except Exception as error:  # noqa: BLE001
                LOGGER.exception("Failed to load currencies")
                self.after(0, lambda: self._show_error(str(error)))

        threading.Thread(target=worker, daemon=True).start()

    def _apply_currency_values(self, values: list[str]) -> None:
        self.currency_values = values
        self.from_picker.set_values(values)
        self.to_picker.set_values(values)
        self._select_initial_currency(self.from_picker, DEFAULT_BASE_CURRENCY, self.settings.default_from_currency)
        self._select_initial_currency(self.to_picker, DEFAULT_TARGET_CURRENCY, self.settings.default_to_currency)
        self._render_favorites()
        self._refresh_history()
        self._schedule_auto_refresh()
        self._set_loading(False, "Currency list loaded.")

    def _select_initial_currency(
        self,
        picker: SearchableCurrencyPicker,
        fallback_code: str,
        preferred_code: str,
    ) -> None:
        target_code = preferred_code or fallback_code
        for value in self.currency_values:
            if value.startswith(f"{target_code} "):
                picker.set(value, trigger=False)
                return
        if self.currency_values:
            picker.set(self.currency_values[0], trigger=False)

    def _render_favorites(self) -> None:
        for widget in self.favorite_frame.winfo_children():
            widget.destroy()

        favorites = self.settings.favorite_currencies or [DEFAULT_BASE_CURRENCY, DEFAULT_TARGET_CURRENCY]
        for index, code in enumerate(favorites[:9]):
            button = ctk.CTkButton(
                self.favorite_frame,
                text=code,
                height=36,
                corner_radius=12,
                command=lambda selected=code: self._apply_favorite(selected),
            )
            button.grid(row=index // 3, column=index % 3, sticky="ew", padx=8, pady=8)

    def _apply_favorite(self, code: str) -> None:
        for value in self.currency_values:
            if value.startswith(f"{code} "):
                self.from_picker.set(value)
                return

    def _refresh_history(self) -> None:
        self.history_panel.render(self.converter_service.get_history())

    def _currency_code(self, value: str) -> str:
        return value.split(" - ", maxsplit=1)[0].strip().upper()

    def convert_async(self) -> None:
        if self.loading:
            return

        try:
            amount = parse_amount(self.amount_var.get())
            from_currency = self._currency_code(self.from_picker.get())
            to_currency = self._currency_code(self.to_picker.get())
        except ValueError as error:
            self._show_error(str(error))
            return

        self._set_loading(True, "Fetching live exchange rate...")

        def worker() -> None:
            try:
                result = self.converter_service.convert(
                    ConversionRequest(
                        amount=amount,
                        from_currency=from_currency,
                        to_currency=to_currency,
                    )
                )
                self.after(0, lambda: self._apply_result(result))
            except ExchangeServiceError as error:
                self.after(0, lambda: self._show_error(str(error)))
            except Exception as error:  # noqa: BLE001
                LOGGER.exception("Conversion failed")
                self.after(0, lambda: self._show_error(f"Unexpected error: {error}"))

        threading.Thread(target=worker, daemon=True).start()

    def _apply_result(self, result: ConversionResult) -> None:
        self.latest_result = result
        source_label = "Live rate" if result.is_live_rate else "Cached offline rate"
        self.rate_var.set(
            f"Rate: 1 {result.from_currency} = {result.exchange_rate:,.4f} {result.to_currency}"
        )
        self.updated_var.set(f"Last updated: {format_timestamp(result.timestamp)}")
        self.result_card.update_content(
            format_money(result.converted_amount, result.to_currency),
            self.rate_var.get(),
            f"{source_label} | Source: {result.rate_source}",
        )
        self._refresh_history()
        self._set_loading(False, "Conversion completed.")

    def swap_currencies(self) -> None:
        from_value = self.from_picker.get()
        to_value = self.to_picker.get()
        if from_value and to_value:
            self.from_picker.set(to_value, trigger=False)
            self.to_picker.set(from_value, trigger=False)
            self.status_bar.set_status("Currencies swapped.")

    def clear_inputs(self) -> None:
        self.amount_var.set("")
        self.rate_var.set("Rate: --")
        self.updated_var.set("Last updated: --")
        self.result_card.update_content("--", "Live rate will appear here", "Waiting for conversion")
        self.status_bar.set_status("Inputs cleared.")

    def copy_result(self) -> None:
        if not self.latest_result:
            self._show_error("No conversion result to copy yet.")
            return
        self.clipboard_clear()
        self.clipboard_append(format_money(self.latest_result.converted_amount, self.latest_result.to_currency))
        self.status_bar.set_status("Converted amount copied to clipboard.")

    def open_settings_window(self) -> None:
        window = ctk.CTkToplevel(self)
        window.title("Settings")
        window.geometry("380x320")
        window.transient(self)
        window.grab_set()

        auto_refresh_var = tk.BooleanVar(value=self.settings.auto_refresh_enabled)
        refresh_seconds_var = tk.StringVar(value=str(self.settings.auto_refresh_seconds))
        favorites_var = tk.StringVar(value=", ".join(self.settings.favorite_currencies))

        ctk.CTkLabel(window, text="Application Settings", font=(FONT_FAMILY, 20, "bold")).pack(anchor="w", padx=20, pady=(20, 18))
        ctk.CTkCheckBox(window, text="Enable auto-refresh", variable=auto_refresh_var).pack(anchor="w", padx=20, pady=8)
        ctk.CTkLabel(window, text="Auto-refresh interval (seconds)").pack(anchor="w", padx=20, pady=(12, 6))
        ctk.CTkEntry(window, textvariable=refresh_seconds_var).pack(fill="x", padx=20)
        ctk.CTkLabel(window, text="Favorite currencies (comma separated)").pack(anchor="w", padx=20, pady=(12, 6))
        ctk.CTkEntry(window, textvariable=favorites_var).pack(fill="x", padx=20)

        def save_settings() -> None:
            try:
                seconds = max(15, int(refresh_seconds_var.get().strip()))
                favorites = [code.strip().upper() for code in favorites_var.get().split(",") if code.strip()]
                self.settings = AppSettings(
                    theme=self.settings.theme,
                    auto_refresh_enabled=auto_refresh_var.get(),
                    auto_refresh_seconds=seconds,
                    favorite_currencies=favorites or self.settings.favorite_currencies,
                    default_from_currency=self._currency_code(self.from_picker.get()),
                    default_to_currency=self._currency_code(self.to_picker.get()),
                )
                self.settings_service.save(self.settings)
                self._render_favorites()
                self._schedule_auto_refresh()
                self.status_bar.set_status("Settings saved.")
                window.destroy()
            except ValueError:
                self._show_error("Auto-refresh interval must be a whole number.")

        ctk.CTkButton(window, text="Save", command=save_settings).pack(side="left", padx=(20, 10), pady=24)
        ctk.CTkButton(window, text="Export History", command=self._export_history_from_settings).pack(side="left", padx=10, pady=24)

    def _export_history_from_settings(self) -> None:
        exported = self.converter_service.export_history()
        self.status_bar.set_status(f"History exported to {Path(exported).name}")
        messagebox.showinfo("Export complete", f"History exported to:\n{exported}")

    def toggle_theme(self) -> None:
        self.settings.theme = "dark" if self.theme_switch.get() else "light"
        ctk.set_appearance_mode(self.settings.theme)
        self.settings_service.save(self.settings)
        self.status_bar.set_status(f"Theme switched to {self.settings.theme}.")

    def use_history_item(self, item: dict[str, str]) -> None:
        self.amount_var.set(item["amount"])
        self._select_code(self.from_picker, item["from_currency"])
        self._select_code(self.to_picker, item["to_currency"])
        self.status_bar.set_status("History item loaded into the form.")

    def _select_code(self, picker: SearchableCurrencyPicker, code: str) -> None:
        for value in self.currency_values:
            if value.startswith(f"{code} "):
                picker.set(value, trigger=False)
                return

    def _schedule_auto_refresh(self) -> None:
        if self.auto_refresh_job:
            self.after_cancel(self.auto_refresh_job)
            self.auto_refresh_job = None

        if self.settings.auto_refresh_enabled:
            milliseconds = max(15, self.settings.auto_refresh_seconds) * 1000
            self.auto_refresh_job = self.after(milliseconds, self._auto_refresh)

    def _auto_refresh(self) -> None:
        self.auto_refresh_job = None
        if self.latest_result:
            self.convert_async()
        self._schedule_auto_refresh()

    def _on_picker_select(self, _: str) -> None:
        self.status_bar.set_status("Currency selection updated.")

    def _show_error(self, message: str) -> None:
        self._set_loading(False, message)
        messagebox.showerror("Currency Converter", message)
