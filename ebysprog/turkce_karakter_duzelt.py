from __future__ import annotations

import os
from pathlib import Path
from tkinter import Tk, messagebox
from tkinter.filedialog import askdirectory


TRANSLATION_TABLE = str.maketrans(
    {
        "ç": "c",
        "Ç": "C",
        "ğ": "g",
        "Ğ": "G",
        "ı": "i",
        "İ": "I",
        "ö": "o",
        "Ö": "O",
        "ş": "s",
        "Ş": "S",
        "ü": "u",
        "Ü": "U",
    }
)


def replace_turkish_chars(value: str) -> str:
    return value.translate(TRANSLATION_TABLE)


def unique_target_path(path: Path) -> Path:
    if not path.exists():
        return path

    parent = path.parent
    stem = path.stem
    suffix = path.suffix
    counter = 1
    while True:
        candidate = parent / f"{stem}{counter:02d}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def rename_path(path: Path) -> tuple[Path, Path] | None:
    new_name = replace_turkish_chars(path.name)
    if new_name == path.name:
        return None

    target = unique_target_path(path.with_name(new_name))
    path.rename(target)
    return path, target


def collect_paths(root: Path) -> tuple[list[Path], list[Path]]:
    files: list[Path] = []
    dirs: list[Path] = []

    for current_root, dir_names, file_names in os.walk(root):
        current_path = Path(current_root)
        files.extend(current_path / file_name for file_name in file_names)
        dirs.extend(current_path / dir_name for dir_name in dir_names)

    dirs.sort(key=lambda path: len(path.parts), reverse=True)
    return files, dirs


def rename_all(root: Path) -> list[tuple[Path, Path]]:
    renamed: list[tuple[Path, Path]] = []
    files, dirs = collect_paths(root)

    for path in files:
        result = rename_path(path)
        if result:
            renamed.append(result)

    for path in dirs:
        if not path.exists():
            continue
        result = rename_path(path)
        if result:
            renamed.append(result)

    root_result = rename_path(root)
    if root_result:
        renamed.append(root_result)

    return renamed


def main() -> None:
    window = Tk()
    window.withdraw()

    selected = askdirectory(title="Türkçe karakterleri değiştirilecek klasörü seçin")
    if not selected:
        return

    root = Path(selected)
    answer = messagebox.askyesno(
        "Onay",
        f"Seçilen klasör ve tüm alt klasörlerdeki dosya/klasör adları değiştirilecek:\n\n{root}\n\nDevam edilsin mi?",
    )
    if not answer:
        return

    try:
        renamed = rename_all(root)
    except OSError as exc:
        messagebox.showerror("Hata", f"Yeniden adlandırma sırasında hata oluştu:\n\n{exc}")
        return

    messagebox.showinfo(
        "Tamamlandı",
        f"İşlem tamamlandı.\n\nDeğiştirilen dosya/klasör sayısı: {len(renamed)}",
    )


if __name__ == "__main__":
    main()
