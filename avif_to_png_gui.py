#!/usr/bin/env python3
"""
AVIF to PNG Converter - Tkinter GUI with drag-and-drop folder support.

Requirements:
    pip install pillow pillow-avif-plugin tkinterdnd2
"""

from __future__ import annotations

import os
import queue
import subprocess
import sys
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image
import pillow_avif  # noqa: F401  # Registers AVIF support in Pillow

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except Exception:
    DND_FILES = "DND_Files"  # type: ignore[assignment]
    TkinterDnD = None  # type: ignore[assignment]
    HAS_DND = False


APP_TITLE = "AVIF to PNG Converter"
SUPPORTED_EXTENSIONS = {".avif"}


@dataclass
class ConversionResult:
    index: int
    status: str
    source: str
    output: str
    message: str


class AvifToPngApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("1280x840")
        self.root.minsize(1024, 680)

        self.worker_thread: threading.Thread | None = None
        self.stop_requested = False
        self.result_queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self.total_files = 0
        self.done_files = 0
        self.success_count = 0
        self.fail_count = 0

        self.input_folder_var = tk.StringVar()
        self.output_folder_var = tk.StringVar()
        self.recursive_var = tk.BooleanVar(value=True)
        self.overwrite_var = tk.BooleanVar(value=False)
        self.keep_structure_var = tk.BooleanVar(value=True)
        self.status_var = tk.StringVar(value="Ready")
        self.summary_var = tk.StringVar(value="Success: 0 | Failed: 0 | Total: 0")
        self.dnd_note_var = tk.StringVar(
            value=(
                "Drag and drop an input/output folder into the drop areas below."
                if HAS_DND
                else "Drag-and-drop is unavailable because tkinterdnd2 is not installed."
            )
        )

        self._build_ui()
        self._poll_queue()

    def _build_ui(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(2, weight=1)

        header = ttk.Frame(self.root, padding=(12, 12, 12, 4))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)

        ttk.Label(header, text=APP_TITLE, font=("Segoe UI", 14, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(header, textvariable=self.dnd_note_var).grid(row=1, column=0, sticky="w", pady=(4, 0))

        top_frame = ttk.Frame(self.root, padding=(12, 8, 12, 8))
        top_frame.grid(row=1, column=0, sticky="nsew")
        top_frame.columnconfigure(1, weight=1)

        ttk.Label(top_frame, text="Input Folder").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(top_frame, textvariable=self.input_folder_var).grid(row=0, column=1, sticky="ew", pady=4)
        ttk.Button(top_frame, text="Browse...", command=self._browse_input_folder).grid(row=0, column=2, padx=(8, 0), pady=4)

        ttk.Label(top_frame, text="Output Folder").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(top_frame, textvariable=self.output_folder_var).grid(row=1, column=1, sticky="ew", pady=4)
        ttk.Button(top_frame, text="Browse...", command=self._browse_output_folder).grid(row=1, column=2, padx=(8, 0), pady=4)

        drop_frame = ttk.Frame(top_frame)
        drop_frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(8, 6))
        drop_frame.columnconfigure(0, weight=1)
        drop_frame.columnconfigure(1, weight=1)

        self.input_drop = tk.Label(
            drop_frame,
            text="Drop INPUT folder here",
            relief="groove",
            bd=2,
            padx=12,
            pady=18,
            anchor="center",
        )
        self.input_drop.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        self.output_drop = tk.Label(
            drop_frame,
            text="Drop OUTPUT folder here",
            relief="groove",
            bd=2,
            padx=12,
            pady=18,
            anchor="center",
        )
        self.output_drop.grid(row=0, column=1, sticky="ew", padx=(6, 0))

        self._setup_drop_target(self.input_drop, self._handle_input_drop)
        self._setup_drop_target(self.output_drop, self._handle_output_drop)

        options_frame = ttk.Frame(top_frame)
        options_frame.grid(row=3, column=0, columnspan=3, sticky="w", pady=(8, 4))

        ttk.Checkbutton(options_frame, text="Scan subfolders", variable=self.recursive_var).grid(row=0, column=0, sticky="w", padx=(0, 16))
        ttk.Checkbutton(options_frame, text="Overwrite existing PNG", variable=self.overwrite_var).grid(row=0, column=1, sticky="w", padx=(0, 16))
        ttk.Checkbutton(options_frame, text="Preserve folder structure", variable=self.keep_structure_var).grid(row=0, column=2, sticky="w")

        actions_frame = ttk.Frame(top_frame)
        actions_frame.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(8, 0))
        actions_frame.columnconfigure(5, weight=1)

        self.start_button = ttk.Button(actions_frame, text="Start Conversion", command=self._start_conversion)
        self.start_button.grid(row=0, column=0, padx=(0, 8))

        self.stop_button = ttk.Button(actions_frame, text="Stop", command=self._request_stop, state="disabled")
        self.stop_button.grid(row=0, column=1, padx=(0, 8))

        ttk.Button(actions_frame, text="Clear Table", command=self._clear_table).grid(row=0, column=2, padx=(0, 8))
        ttk.Button(actions_frame, text="Open Output Folder", command=self._open_output_folder).grid(row=0, column=3, padx=(0, 8))
        ttk.Button(actions_frame, text="Exit", command=self.root.destroy).grid(row=0, column=4, padx=(0, 8))

        table_frame = ttk.Frame(self.root, padding=(12, 0, 12, 0))
        table_frame.grid(row=2, column=0, sticky="nsew")
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        columns = ("no", "status", "source", "output", "message")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        self.tree.heading("no", text="#")
        self.tree.heading("status", text="Status")
        self.tree.heading("source", text="Source AVIF")
        self.tree.heading("output", text="Output PNG")
        self.tree.heading("message", text="Message")

        self.tree.column("no", width=60, anchor="center", stretch=False)
        self.tree.column("status", width=100, anchor="center", stretch=False)
        self.tree.column("source", width=360, anchor="w")
        self.tree.column("output", width=360, anchor="w")
        self.tree.column("message", width=320, anchor="w")

        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        x_scroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")

        bottom_frame = ttk.Frame(self.root, padding=12)
        bottom_frame.grid(row=3, column=0, sticky="ew")
        bottom_frame.columnconfigure(0, weight=1)

        self.progress = ttk.Progressbar(bottom_frame, mode="determinate")
        self.progress.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        ttk.Label(bottom_frame, textvariable=self.status_var).grid(row=1, column=0, sticky="w")
        ttk.Label(bottom_frame, textvariable=self.summary_var).grid(row=2, column=0, sticky="w", pady=(4, 0))

    def _setup_drop_target(self, widget: tk.Widget, callback) -> None:
        if not HAS_DND:
            return
        widget.drop_target_register(DND_FILES)
        widget.dnd_bind("<<DropEnter>>", lambda event, w=widget: self._set_drop_style(w, active=True))
        widget.dnd_bind("<<DropLeave>>", lambda event, w=widget: self._set_drop_style(w, active=False))
        widget.dnd_bind("<<Drop>>", lambda event, cb=callback, w=widget: self._on_drop(event, cb, w))

    @staticmethod
    def _set_drop_style(widget: tk.Widget, active: bool) -> None:
        try:
            widget.configure(bg="#e8f4ff" if active else "SystemButtonFace")
        except Exception:
            pass

    def _on_drop(self, event, callback, widget: tk.Widget):
        self._set_drop_style(widget, active=False)
        callback(getattr(event, "data", ""))
        return event.action if hasattr(event, "action") else None

    def _parse_dropped_paths(self, data: str) -> list[str]:
        if not data:
            return []
        try:
            paths = list(self.root.tk.splitlist(data))
        except Exception:
            paths = [data]

        cleaned: list[str] = []
        for item in paths:
            text = str(item).strip()
            if text.startswith("{") and text.endswith("}"):
                text = text[1:-1]
            cleaned.append(text)
        return cleaned

    def _resolve_folder_from_drop(self, data: str) -> Path | None:
        paths = self._parse_dropped_paths(data)
        for raw in paths:
            path = Path(raw)
            if path.is_dir():
                return path
            if path.is_file():
                return path.parent
        return None

    def _handle_input_drop(self, data: str) -> None:
        folder = self._resolve_folder_from_drop(data)
        if not folder:
            messagebox.showwarning(APP_TITLE, "Please drop a valid folder or a file inside a folder.")
            return
        self.input_folder_var.set(str(folder))
        if not self.output_folder_var.get().strip():
            self.output_folder_var.set(str(folder / "png_output"))
        self.status_var.set(f"Input folder set from drag-and-drop: {folder}")

    def _handle_output_drop(self, data: str) -> None:
        folder = self._resolve_folder_from_drop(data)
        if not folder:
            messagebox.showwarning(APP_TITLE, "Please drop a valid folder or a file inside a folder.")
            return
        self.output_folder_var.set(str(folder))
        self.status_var.set(f"Output folder set from drag-and-drop: {folder}")

    def _browse_input_folder(self) -> None:
        folder = filedialog.askdirectory(title="Select input folder")
        if folder:
            self.input_folder_var.set(folder)
            if not self.output_folder_var.get().strip():
                self.output_folder_var.set(str(Path(folder) / "png_output"))

    def _browse_output_folder(self) -> None:
        folder = filedialog.askdirectory(title="Select output folder")
        if folder:
            self.output_folder_var.set(folder)

    def _open_output_folder(self) -> None:
        output_text = self.output_folder_var.get().strip()
        if not output_text:
            messagebox.showwarning(APP_TITLE, "Please select an output folder first.")
            return
        output_folder = Path(output_text)
        if not output_folder.exists():
            messagebox.showwarning(APP_TITLE, "Output folder does not exist yet.")
            return
        try:
            if sys.platform.startswith("win"):
                os.startfile(str(output_folder))  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(output_folder)])
            else:
                subprocess.Popen(["xdg-open", str(output_folder)])
        except Exception as exc:
            messagebox.showerror(APP_TITLE, f"Could not open folder:\n{exc}")

    def _clear_table(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.status_var.set("Ready")
        self.summary_var.set("Success: 0 | Failed: 0 | Total: 0")
        self.progress["value"] = 0
        self.progress["maximum"] = 100
        self.total_files = 0
        self.done_files = 0
        self.success_count = 0
        self.fail_count = 0

    def _start_conversion(self) -> None:
        if self.worker_thread and self.worker_thread.is_alive():
            messagebox.showinfo(APP_TITLE, "A conversion is already running.")
            return

        input_folder = Path(self.input_folder_var.get().strip())
        output_folder_text = self.output_folder_var.get().strip()

        if not input_folder.exists() or not input_folder.is_dir():
            messagebox.showerror(APP_TITLE, "Please select a valid input folder.")
            return

        if not output_folder_text:
            output_folder_text = str(input_folder / "png_output")
            self.output_folder_var.set(output_folder_text)

        output_folder = Path(output_folder_text)
        output_folder.mkdir(parents=True, exist_ok=True)

        avif_files = list(self._find_avif_files(input_folder, self.recursive_var.get()))
        if not avif_files:
            messagebox.showinfo(APP_TITLE, "No AVIF files were found.")
            return

        self._clear_table()
        self.stop_requested = False
        self.total_files = len(avif_files)
        self.progress["maximum"] = self.total_files
        self.status_var.set(f"Found {self.total_files} AVIF file(s). Starting conversion...")
        self.summary_var.set(f"Success: 0 | Failed: 0 | Total: {self.total_files}")

        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")

        self.worker_thread = threading.Thread(
            target=self._worker_convert,
            args=(input_folder, output_folder, avif_files),
            daemon=True,
        )
        self.worker_thread.start()

    def _request_stop(self) -> None:
        self.stop_requested = True
        self.status_var.set("Stopping after current file...")

    def _poll_queue(self) -> None:
        try:
            while True:
                event_type, payload = self.result_queue.get_nowait()
                if event_type == "row":
                    self._handle_row(payload)
                elif event_type == "done":
                    self._handle_done(payload)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self._poll_queue)

    def _handle_row(self, payload: ConversionResult) -> None:
        self.tree.insert(
            "",
            "end",
            values=(payload.index, payload.status, payload.source, payload.output, payload.message),
        )
        self.done_files += 1
        if payload.status == "OK":
            self.success_count += 1
        else:
            self.fail_count += 1

        self.progress["value"] = self.done_files
        self.status_var.set(f"Processed {self.done_files}/{self.total_files} file(s)...")
        self.summary_var.set(
            f"Success: {self.success_count} | Failed: {self.fail_count} | Total: {self.total_files}"
        )

        children = self.tree.get_children()
        if children:
            self.tree.see(children[-1])

    def _handle_done(self, payload: str) -> None:
        self.status_var.set(payload)
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")

        if self.fail_count == 0 and self.done_files > 0:
            messagebox.showinfo(APP_TITLE, payload)
        elif self.done_files > 0:
            messagebox.showwarning(APP_TITLE, payload)

    def _worker_convert(self, input_folder: Path, output_folder: Path, avif_files: list[Path]) -> None:
        overwrite = self.overwrite_var.get()
        keep_structure = self.keep_structure_var.get()

        for index, src_path in enumerate(avif_files, start=1):
            if self.stop_requested:
                self.result_queue.put(("done", f"Stopped. Processed {self.done_files}/{self.total_files} file(s)."))
                return

            ok, dst_path, message = self._convert_one(
                src_path=src_path,
                input_root=input_folder,
                output_root=output_folder,
                overwrite=overwrite,
                keep_structure=keep_structure,
            )

            result = ConversionResult(
                index=index,
                status="OK" if ok else "FAIL",
                source=str(src_path),
                output=str(dst_path) if dst_path else "",
                message=message,
            )
            self.result_queue.put(("row", result))

        self.result_queue.put(
            (
                "done",
                f"Completed. Success: {self.success_count + 0} | Failed: {self.fail_count + 0} | Total: {self.total_files}",
            )
        )

    @staticmethod
    def _find_avif_files(input_folder: Path, recursive: bool) -> Iterable[Path]:
        patterns = []
        for ext in SUPPORTED_EXTENSIONS:
            patterns.extend([f"*{ext}", f"*{ext.upper()}"])

        seen: set[Path] = set()
        for pattern in patterns:
            iterator = input_folder.rglob(pattern) if recursive else input_folder.glob(pattern)
            for path in iterator:
                resolved = path.resolve()
                if resolved not in seen:
                    seen.add(resolved)
                    yield path

    @staticmethod
    def _convert_one(
        src_path: Path,
        input_root: Path,
        output_root: Path,
        overwrite: bool,
        keep_structure: bool,
    ) -> tuple[bool, Path | None, str]:
        try:
            if keep_structure:
                relative_path = src_path.relative_to(input_root)
                dst_path = (output_root / relative_path).with_suffix(".png")
            else:
                dst_path = output_root / f"{src_path.stem}.png"

            dst_path.parent.mkdir(parents=True, exist_ok=True)

            if dst_path.exists() and not overwrite:
                return True, dst_path, "Skipped existing PNG"

            with Image.open(src_path) as img:
                if img.mode in ("RGBA", "LA") or ("transparency" in img.info):
                    converted = img.convert("RGBA")
                else:
                    converted = img.convert("RGB")
                converted.save(dst_path, format="PNG")

            return True, dst_path, "Converted successfully"
        except Exception as exc:
            return False, None, str(exc)


def main() -> None:
    if HAS_DND and TkinterDnD is not None:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()

    try:
        root.iconname(APP_TITLE)
    except Exception:
        pass

    app = AvifToPngApp(root)
    _ = app
    root.mainloop()


if __name__ == "__main__":
    main()
