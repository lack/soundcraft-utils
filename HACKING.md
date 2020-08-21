Notes for those wanting to help out
===================================

First of all, thank you!  I appreciate all feedback, pull requests, and gentle criticism!

Development Environment
-----------------------

To ensure homogeneity of development environments, I recommend
using `pipenv` and python 3.8 (though python 3.6 is the minimum
supported version).  pipenv can be installed via pip in the usual
ways.

### Set up and use pipenv

`pipenv install --dev`
- Sets up an appropriate virtual environment and installs all
  appropriate development packages

`pipenv shell`
- Starts a subshell with the appropriate environment so that the
  sandboxed libraries and utilities are in use

### Set up pre-commit

`pre-commit install` (inside of pipenv shell)
- Set up git hooks management so every commit gets checked/fixed
- Only needs to be done once after cloning this repo

### Adding new dependencies

`pipenv install [--dev] <pgkname>`
- Installs the dependency to the local pipenv environment.  Use
  `--dev` for development-only packages, omit for run-time
  dependencies.

`pipenv-setup sync --pidfile`
- Syncs any run-time dependencies from pipenv to setup.py


Submitting Changes
------------------

- Please ensure that `pytest` passes, using `pytest` itself or `tox`.

  Github runs this for you on all branches as well, and I'm working on
  getting the feedback from that integrated into the pull requests,
  eventually.

  Try to test new code thoroughly.  I'm working on increasing code
  coverage as I go as well.  Use 'pytest' or 'tox' to test.

- Run `flake8` and `black` to format your code.

  The soundcraft-utils source code is written to conform to stock `flake8`
  without any extra plugins installed.  Using pipenv (see above) should make
  sure you have the right set of flake8 plugins installed.

  Our pre-commit hooks will do this for you automatically.

- Add yourself to the [`CONTRIBUTORS.md`](CONTRIBUTORS.html) file if you
  want, but if you do, please also run `tools/contrib_to_about.py` to
  synchronize the changes in there to the GUI about screen.

- Open pull requests to the default branch, currently named `release`.


Interfaces, Namespaces, Specifications
======================================

This lists and links to (at least some) interfaces, namespaces, and
specifications which `soundcraft-utils` comes into contact with.

  * [DBUS](https://dbus.freedesktop.org/doc/dbus-specification.html)

  * [Desktop Entry Specification](https://specifications.freedesktop.org/desktop-entry-spec/desktop-entry-spec-latest.html)

    The `.desktop` file hooks the `soundcraft_gui` GUI application
    into the desktop environment's list of applications.

  * [XDG Base Directory Specification](https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html)

    This specifies the locations the soundcraft-utils Desktop file and
    icons should be installed to.
