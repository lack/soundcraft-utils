Notes for those wanting to help out
===================================

- Thank you!  I appreciate all feedback, pull requests, and gentle criticism!

- Open pull requests to the default branch, currently named `release`.

- Please ensure that `pytest` passes, using `pytest` itself or `tox`.

  Github runs this for you on all branches as well, and I'm working on
  getting the feedback from that integrated into the pull requests,
  eventually.

- Try to test new code thoroughly.  I'm working on increasing code
  coverage as I go as well.

- Run `flake8` and `black` to format your code.

  The soundcraft-utils source code is written to conform to stock
  `flake8` without any extra plugins installed.

- Add yourself to the [`CONTRIBUTORS.md`](CONTRIBUTORS.html) file if you
  want, but if you do, please also run `tools/contrib_to_about.py` to
  synchronize the changes in there to the GUI about screen.


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
