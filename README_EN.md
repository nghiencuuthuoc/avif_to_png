# AVIF to PNG Converter — Tkinter GUI with Drag-and-Drop Folder Support

A desktop Python application for converting `.avif` images to `.png` using a Tkinter GUI.

This version supports:
- selecting folders with **Browse** buttons
- **drag-and-drop folder input/output**
- recursive scanning of subfolders
- preserving folder structure
- overwrite or skip existing PNG files
- progress bar
- conversion log table
- background threading to keep the GUI responsive

## Features

- Convert all `.avif` files in an input folder to `.png`
- Drag and drop an **input folder**
- Drag and drop an **output folder**
- Option to scan subfolders recursively
- Option to preserve source folder structure in the output folder
- Option to overwrite existing PNG files
- Table view for status tracking
- Open output folder directly from the app

## Requirements

- Python 3.10+
- Tkinter
- `pillow`
- `pillow-avif-plugin`
- `tkinterdnd2`

## Install

```bash
pip install -r requirements.txt
```

Or install manually:

```bash
pip install pillow pillow-avif-plugin tkinterdnd2
```

## Run

```bash
python avif_to_png_tk_gui.py
```

## How to use

1. Launch the application.
2. Choose the input folder using **Browse...** or drag a folder into **Drop INPUT folder here**.
3. Choose the output folder using **Browse...** or drag a folder into **Drop OUTPUT folder here**.
4. Select your options:
   - **Scan subfolders**
   - **Overwrite existing PNG**
   - **Preserve folder structure**
5. Click **Start Conversion**.
6. Review the results in the table.

## Notes

- If you drop a file instead of a folder, the app will use the file's parent folder.
- If the output folder is empty, the app will automatically create `png_output` inside the input folder.
- AVIF support is provided through `pillow-avif-plugin`.
- Drag-and-drop support is provided through `tkinterdnd2`.

## Project structure

```text
avif_to_png_tk_gui/
├── avif_to_png_tk_gui.py
├── README_EN.md
├── README_VI.md
└── requirements.txt
```

## License

You can add your preferred license before publishing to GitHub.
