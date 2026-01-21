from __future__ import annotations

import importlib.metadata
import logging
import shutil
import subprocess
import tempfile
from urllib.parse import quote
from pathlib import Path

import typer

from pptx2md import ConversionConfig, convert


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(importlib.metadata.version("pptx2md-cli"))
        raise typer.Exit()


def main(
    pptx_path: Path = typer.Argument(
        ...,
        metavar="PPTX_PATH",
        help="Path to the PPTX file to convert.",
    ),
    title_path: Path | None = typer.Option(
        None,
        "-t",
        "--title",
        help="Path to custom titles file.",
    ),
    output_path: Path | None = typer.Option(
        None,
        "-o",
        "--output",
        help="Output markdown file path.",
    ),
    image_dir: Path | None = typer.Option(
        None,
        "-i",
        "--image-dir",
        help="Directory for extracted images.",
    ),
    image_width: int | None = typer.Option(
        None,
        "--image-width",
        help="Maximum image width in pixels.",
    ),
    disable_image: bool = typer.Option(
        False,
        "--disable-image",
        help="Disable image extraction.",
    ),
    disable_escaping: bool = typer.Option(
        False,
        "--disable-escaping",
        help="Do not escape special characters.",
    ),
    disable_notes: bool = typer.Option(
        False,
        "--disable-notes",
        help="Do not include presenter notes.",
    ),
    disable_wmf: bool = typer.Option(
        True,
        "--disable-wmf/--enable-wmf",
        help="Skip upstream WMF conversion (wrapper converts after).",
    ),
    disable_color: bool = typer.Option(
        False,
        "--disable-color",
        help="Disable color tags in HTML.",
    ),
    enable_slides: bool = typer.Option(
        False,
        "--enable-slides",
        help="Add slide delimiters (---).",
    ),
    try_multi_column: bool = typer.Option(
        False,
        "--try-multi-column",
        help="Detect multi-column slides (slow).",
    ),
    min_block_size: int | None = typer.Option(
        None,
        "--min-block-size",
        help="Minimum number of characters for a text block.",
    ),
    wiki: bool = typer.Option(
        False,
        "--wiki",
        help="Output TiddlyWiki markup.",
    ),
    mdk: bool = typer.Option(
        False,
        "--mdk",
        help="Output Madoko markup.",
    ),
    qmd: bool = typer.Option(
        False,
        "--qmd",
        help="Output Quarto markdown.",
    ),
    page: int | None = typer.Option(
        None,
        "--page",
        help="Only convert a specific slide number.",
    ),
    keep_similar_titles: bool = typer.Option(
        False,
        "--keep-similar-titles",
        help='Keep similar titles and add "(cont.)".',
    ),
    version: bool = typer.Option(
        False,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    output_path, image_dir = _resolve_output_paths(
        pptx_path=pptx_path,
        output_path=output_path,
        image_dir=image_dir,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image_dir.mkdir(parents=True, exist_ok=True)

    config_kwargs = {
        "pptx_path": pptx_path,
        "output_path": output_path,
        "image_dir": image_dir,
        "title_path": title_path,
        "image_width": image_width,
        "disable_image": disable_image,
        "disable_escaping": disable_escaping,
        "disable_notes": disable_notes,
        "disable_wmf": disable_wmf,
        "disable_color": disable_color,
        "enable_slides": enable_slides,
        "try_multi_column": try_multi_column,
        "min_block_size": min_block_size,
        "wiki": wiki,
        "mdk": mdk,
        "qmd": qmd,
        "page": page,
        "keep_similar_titles": keep_similar_titles,
    }
    config = ConversionConfig(**{key: value for key, value in config_kwargs.items() if value is not None})
    if disable_wmf:
        logging.getLogger("pptx2md.parser").setLevel(logging.ERROR)
    """Convert PPTX files to markdown with assets."""
    convert(config)
    _normalize_images(output_path, image_dir)


def _resolve_output_paths(
    *,
    pptx_path: Path,
    output_path: Path | None,
    image_dir: Path | None,
) -> tuple[Path, Path]:
    base_dir = pptx_path.parent
    if output_path is not None and not output_path.is_absolute():
        output_path = base_dir / output_path
    if image_dir is not None and not image_dir.is_absolute():
        image_dir = base_dir / image_dir

    if output_path is None and image_dir is None:
        output_dir = base_dir / pptx_path.stem
        return output_dir / "index.md", output_dir / "img"

    if output_path is None and image_dir is not None:
        return image_dir.parent / "index.md", image_dir

    if output_path is not None and image_dir is None:
        return output_path, output_path.parent / "img"

    return output_path or Path("index.md"), image_dir or Path("img")


def _normalize_images(output_path: Path, image_dir: Path) -> None:
    replacements: dict[str, str] = {}

    for image_path in image_dir.iterdir():
        if not image_path.is_file():
            continue

        suffix = image_path.suffix.lower()
        if suffix == ".png":
            continue

        new_path = image_path.with_suffix(".png")
        if suffix in {".jpg", ".jpeg"}:
            _convert_with_pillow(image_path, new_path)
        elif suffix == ".wmf":
            _convert_wmf(image_path, new_path)
        else:
            continue

        image_path.unlink(missing_ok=True)
        replacements[image_path.name] = new_path.name

    content = output_path.read_text(encoding="utf-8")
    if replacements:
        for old_name, new_name in replacements.items():
            content = content.replace(old_name, new_name)
    content = _normalize_image_links(content, output_path, image_dir)
    content = _append_images_if_missing(content, output_path, image_dir)
    output_path.write_text(content, encoding="utf-8")


def _convert_with_pillow(source: Path, target: Path) -> None:
    from PIL import Image

    with Image.open(source) as image:
        image.save(target, "PNG")


def _convert_wmf(source: Path, target: Path) -> None:
    if _convert_with_imagemagick(source, target):
        return

    if _convert_with_wand(source, target):
        return

    if _convert_with_emf2svg(source, target):
        return

    typer.echo(
        "WMF conversion failed. Install ImageMagick with WMF support or emf2svg."
    )
    raise typer.Exit(1)


def _convert_with_imagemagick(source: Path, target: Path) -> bool:
    for cmd in ("magick", "convert"):
        if not shutil.which(cmd):
            continue
        result = subprocess.run(
            [cmd, str(source), str(target)],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if result.returncode == 0 and target.exists():
            return True
    return False


def _convert_with_wand(source: Path, target: Path) -> bool:
    try:
        from wand.image import Image as WandImage
    except ImportError:
        return False

    try:
        with WandImage(filename=str(source)) as image:
            image.format = "png"
            image.save(filename=str(target))
        return True
    except Exception:
        return False


def _convert_with_emf2svg(source: Path, target: Path) -> bool:
    if not shutil.which("emf2svg-conv"):
        return False

    with tempfile.TemporaryDirectory() as tmpdir:
        svg_path = Path(tmpdir) / "image.svg"
        result = subprocess.run(
            ["emf2svg-conv", "-i", str(source), "-o", str(svg_path)],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if result.returncode != 0 or not svg_path.exists():
            return False

        result = subprocess.run(
            ["convert", str(svg_path), str(target)],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return result.returncode == 0 and target.exists()


def _append_images_if_missing(content: str, output_path: Path, image_dir: Path) -> str:
    if "img/" in content or "<img" in content:
        return content

    image_paths = sorted(
        path for path in image_dir.iterdir() if path.is_file() and path.suffix.lower() == ".png"
    )
    if not image_paths:
        return content

    rel_dir = image_dir.relative_to(output_path.parent)
    lines = ["", "", "# Images", ""]
    for image_path in image_paths:
        rel_path = rel_dir / image_path.name
        lines.append(f"![]({_quote_path(rel_path.as_posix())})")
        lines.append("")
    return content + "\n".join(lines)


def _normalize_image_links(content: str, output_path: Path, image_dir: Path) -> str:
    rel_dir = image_dir.relative_to(output_path.parent)
    for image_path in image_dir.iterdir():
        if not image_path.is_file():
            continue
        rel_path = rel_dir / image_path.name
        raw = rel_path.as_posix()
        encoded = _quote_path(raw)
        if raw != encoded:
            content = content.replace(raw, encoded)
    return content


def _quote_path(path: str) -> str:
    return quote(path, safe="/()[]-._")


if __name__ == "__main__":
    typer.run(main)


def run() -> None:
    typer.run(main)
