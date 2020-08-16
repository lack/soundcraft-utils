Notes for those wanting to help out:

- Thank you!  I appreciate all feedback, pull requests, and gentle criticism!
- Open pull requests to the default branch, currently named `release`
- Please ensure that `pytest` passes, using `pytest` itself or `tox`.  Github runs this for you on all branches as well, and I'm working on getting the feedback from that integrated into the pull requests, eventually.
-- Try to test new code thoroughly.  I'm working on increasing code coverage as I go as well
- Run `flake8` and `black` to format your code
- Add yourself to the CONTRIBUTORS.md file if you want, but if you do, please also run `tools/contrib_to_about.py` to synchronize the changes in there to the GUI about screen.
