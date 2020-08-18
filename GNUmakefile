# GNUmakefile - Automate a few tasks for hacking on soundcraft-utils
#
# This GNUmakefile is only to help while developing on
# soundcraft-utils.
#
# It has nothing to do with actually building or installing
# soundcraft-utils which goes by the well-known `setup.py` method.
#
# Targets:
#    make        The same as `make all`.
#    make all    Run code formatting checks, format sources properly.
#    make check  Run all checks and tests, including those of 'make all'.


########################################################################
# Tools used
########################################################################

BLACK = black
FLAKE8 = flake8
MARKDOWN = markdown
PYTEST = pytest
TOX = tox


########################################################################
# Well-known make targets
########################################################################

.PHONY: all
all: all-local

.PHONY: check
check: all check-local


########################################################################
# The actual targets to be hooked into the well-known targets
########################################################################

SOURCES.md = $(wildcard *.md)
ALL_TARGETS += $(SOURCES.md:.md=.html)
%.html: %.md
	$(MARKDOWN) -o $@ $<


# TODO: Eventually, there should be no FLAKE8_IGNORE content at all.

# Import sequence and formatting
# FLAKE8_IGNORE += I100
# FLAKE8_IGNORE += I201

# I202 makes flake8 complain about a newline added by black. Have
# flake8 ignore it to allow a consistent state of affairs.
FLAKE8_IGNORE += I202

# Missing docstrings
FLAKE8_IGNORE += D100
FLAKE8_IGNORE += D101
FLAKE8_IGNORE += D102
FLAKE8_IGNORE += D103
FLAKE8_IGNORE += D104
FLAKE8_IGNORE += D106
FLAKE8_IGNORE += D107

# Docstring contents
FLAKE8_IGNORE += D200
FLAKE8_IGNORE += D205
FLAKE8_IGNORE += D208

# The DBUS XML in the docstrings cannot have the first line ending in
# a period, so we need to ignore D400.
FLAKE8_IGNORE += D400

FLAKE8_FLAGS += --extend-ignore=$(shell echo "$(sort $(FLAKE8_IGNORE))" | tr ' ' ,)

ALL_TARGETS += run-flake8
.PHONY: run-flake8
run-flake8:
	$(FLAKE8) $(FLAKE8_FLAGS)


ALL_TARGETS += run-black
.PHONY: run-black
run-black:
	$(BLACK) .


CHECK_TARGETS += check-pytest
.PHONY: check-pytest
check-pytest:
	$(PYTEST)


CHECK_TARGETS += check-tox
.PHONY: check-tox
check-tox:
	$(TOX)


########################################################################
# The hooking mechanism for the the well-known targets
########################################################################

.PHONY: all-local
all-local: $(ALL_TARGETS)

.PHONY: check-local
check-local: $(CHECK_TARGETS)
