# pptx2md-cli

Modern CLI wrapper around the upstream `pptx2md` library.

## Install (local dev)

```sh
uv venv
source .venv/bin/activate
uv pip install -e .
```

## Install (system tool)

```sh
make install
```

The install target will:

- Install `uv` if missing.
- Install ImageMagick + WMF/EMF support on Debian/Ubuntu.

If you want to run the installer directly:

```sh
./scripts/install.sh --dependencies
```

## Usage

```sh
pptx2md deck.pptx
pptx2md deck.pptx -o output/index.md -i output/img
pptx2md deck.pptx -t titles.txt --enable-slides
```

By default, `pptx2md deck.pptx` writes to `deck/index.md` with images in
`deck/img`.

Run `pptx2md --help` to see all options. The CLI mirrors the upstream arguments.

### Example Help Output

```text
Usage: pptx2md [OPTIONS] PPTX_PATH

Convert PPTX files to markdown with assets.

Options:
  -t, --title PATH              Path to custom titles file.
  -o, --output PATH             Output markdown file path.
  -i, --image-dir PATH          Directory for extracted images.
      --image-width INTEGER     Maximum image width in pixels.
      --disable-image           Disable image extraction.
      --disable-escaping        Do not escape special characters.
      --disable-notes           Do not include presenter notes.
      --disable-wmf             Keep WMF images untouched.
      --disable-color           Disable color tags in HTML.
      --enable-slides           Add slide delimiters (---).
      --try-multi-column        Detect multi-column slides (slow).
      --min-block-size INTEGER  Minimum number of characters for a text block.
      --wiki                    Output TiddlyWiki markup.
      --mdk                     Output Madoko markup.
      --qmd                     Output Quarto markdown.
      --page INTEGER            Only convert a specific slide number.
      --keep-similar-titles     Keep similar titles and add "(cont.)".
      --version                 Show version and exit.
  --help                        Show this message and exit.
```

## Notes

- Requires Python 3.10+.
- WMF images are converted to PNG when ImageMagick is available. Install it
  with WMF support (for example, `apt install imagemagick libwmf-bin`).
- By default the wrapper skips upstream WMF conversion and post-processes
  images itself. Use `--enable-wmf` to attempt upstream conversion.
- Upstream project: https://github.com/ssine/pptx2md
