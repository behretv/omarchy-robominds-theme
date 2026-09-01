# omarchy-robominds-dark
#
#   make install  clone this repo as an omarchy-managed theme and apply it
#   make update   pull latest changes in the installed theme and re-apply
#   make apply    regenerate theme files from the style guide and re-apply
#
# `make apply` needs a token source — pass one of:
#   make apply TOKENS=/path/to/tokens.css
#   make apply URL=https://brand.robominds.de
#
# The theme is installed by `omarchy theme install`, which clones this repo
# into ~/.config/omarchy/themes/$(THEME_SLUG) (keeping its .git). Omarchy then
# manages updates via `omarchy theme update` and applies it with
# `omarchy theme set`.
#
# The theme ships only colors.toml (+ shell.lock.toml, keyboard.rgb, icons,
# backgrounds); omarchy generates every per-app config (VS Code, Neovim,
# terminals, ...) from it via templates when the theme is applied.

REPO_URL  ?= git@github.com:behretv/omarchy-robominds-dark.git
PYTHON    ?= python3
THEME_SLUG := robominds-dark
THEME_DIR  := $(HOME)/.config/omarchy/themes/$(THEME_SLUG)

.PHONY: install update apply

install:
	omarchy theme install $(REPO_URL)

update:
	git -C $(CURDIR) pull --ff-only
	omarchy theme update
	omarchy theme set $(THEME_SLUG)

apply:
ifeq ($(TOKENS)$(URL),)
	$(error pass a token source: make apply TOKENS=/path/to/tokens.css  or  make apply URL=https://brand.robominds.de)
endif
ifdef TOKENS
	$(PYTHON) scripts/update_theme.py --tokens $(TOKENS)
else
	$(PYTHON) scripts/update_theme.py --url $(URL)
endif
ifeq ($(wildcard $(THEME_DIR)/.git),)
	$(error theme not installed at $(THEME_DIR); run 'make install' first)
endif
	cp -f colors.toml shell.lock.toml keyboard.rgb icons.theme LICENSE README.md $(THEME_DIR)/
	cp -rf backgrounds/* $(THEME_DIR)/backgrounds/
	cd $(THEME_DIR) && git add -A && git commit -m "Local: regenerated theme files" && git push
	omarchy theme set $(THEME_SLUG)
