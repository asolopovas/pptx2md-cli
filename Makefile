.PHONY: help init install install-dev run clean check-imagemagick ensure-uv ensure-imagemagick

help:
	@printf "Targets:\n"
	@printf "  init         Create venv and install dev deps\n"
	@printf "  install      Install as system tool via uv\n"
	@printf "  install-force  Reinstall system tool via uv\n"
	@printf "  install-dev  Install editable package in venv\n"
	@printf "  run          Run pptx2md on a file\n"
	@printf "  clean        Remove venv and build artifacts\n"
	@printf "  check-imagemagick  Verify ImageMagick is installed\n"
	@printf "  ensure-uv    Install uv if missing\n"
	@printf "  ensure-imagemagick  Install ImageMagick + WMF support\n"

init:
	$(MAKE) ensure-uv
	uv venv
	. .venv/bin/activate && uv pip install -e .
	$(MAKE) ensure-imagemagick

install:
	./scripts/install.sh

install-force:
install-force:
	./scripts/install.sh --dependencies --force

install-dev:
	$(MAKE) ensure-uv
	uv venv
	. .venv/bin/activate && uv pip install -e .
	$(MAKE) ensure-imagemagick

run:
	@test -n "$(FILE)" || (printf "FILE is required. Example: make run FILE=deck.pptx\n" && exit 1)
	. .venv/bin/activate && pptx2md "$(FILE)"

clean:
	rm -rf .venv dist build *.egg-info

check-imagemagick:
	@command -v magick >/dev/null 2>&1 || command -v convert >/dev/null 2>&1 || \
		(printf "ImageMagick is required for WMF conversion. Install it and retry.\n" && exit 1)
	@command -v emf2svg-conv >/dev/null 2>&1 || \
		(command -v magick >/dev/null 2>&1 && magick -list format 2>/dev/null | grep -q '^ *WMF') || \
		(command -v convert >/dev/null 2>&1 && convert -list format 2>/dev/null | grep -q '^ *WMF') || \
		(printf "Install libwmf-bin or emf2svg for WMF/EMF support.\n" && exit 1)

ensure-uv:
	@command -v uv >/dev/null 2>&1 || \
		(printf "Installing uv...\n" && curl -LsSf https://astral.sh/uv/install.sh | sh)

ensure-imagemagick:
	@command -v magick >/dev/null 2>&1 || command -v convert >/dev/null 2>&1 || \
		(command -v apt-get >/dev/null 2>&1 || (printf "Install ImageMagick manually for your OS.\n" && exit 1))
	@command -v magick >/dev/null 2>&1 || command -v convert >/dev/null 2>&1 || \
		(printf "Installing ImageMagick...\n" && sudo apt-get update && sudo apt-get install -y imagemagick)
	@command -v magick >/dev/null 2>&1 && magick -list format 2>/dev/null | grep -q '^ *WMF' || \
		(command -v convert >/dev/null 2>&1 && convert -list format 2>/dev/null | grep -q '^ *WMF') || \
		(command -v apt-get >/dev/null 2>&1 || (printf "Install libwmf-bin manually for your OS.\n" && exit 1))
	@command -v magick >/dev/null 2>&1 && magick -list format 2>/dev/null | grep -q '^ *WMF' || \
		(command -v convert >/dev/null 2>&1 && convert -list format 2>/dev/null | grep -q '^ *WMF') || \
		(printf "Installing WMF delegates...\n" && sudo apt-get install -y libwmf-bin)
	@command -v emf2svg-conv >/dev/null 2>&1 || \
		(command -v apt-get >/dev/null 2>&1 || (printf "Install emf2svg manually for your OS.\n" && exit 1))
	@command -v emf2svg-conv >/dev/null 2>&1 || \
		(printf "Installing emf2svg...\n" && sudo apt-get install -y emf2svg)
	@$(MAKE) check-imagemagick
