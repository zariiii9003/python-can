Developer's Overview
====================


Contributing
------------

Welcome! Thank you for your interest in python-can. Whether you want to fix a bug, add a
feature, improve documentation, write examples, help solve issues reported by others, or
simply report a problem, your contribution is valued. Contributions are made via the
`python-can GitHub repository <https://github.com/hardbyte/python-can>`_. If you have
questions, feel free to open an issue or start a discussion on GitHub.

Please note: The latest release on PyPI may be behind the ``main`` branch. Always base your
contributions on the ``main`` branch.

If you're new to the codebase, see the next section for an overview of the code structure.
For more about the internals, see :ref:`internalapi` and information on extending the
``can.io`` module.

Code Structure
^^^^^^^^^^^^^^

The modules in ``python-can`` are:

+-------------------------------------+------------------------------------------------------+
|Module                               | Description                                          |
+=====================================+======================================================+
|:doc:`can.interfaces.* <interfaces>` | Contains interface dependent code.                   |
+-------------------------------------+------------------------------------------------------+
|:doc:`can.bus <bus>`                 | Contains the interface independent Bus object.       |
+-------------------------------------+------------------------------------------------------+
|:doc:`can.message <message>`         | Contains the interface independent Message object.   |
+-------------------------------------+------------------------------------------------------+
|:doc:`can.io.* <file_io>`            | Contains a range of file readers and writers.        |
+-------------------------------------+------------------------------------------------------+
|:doc:`can.broadcastmanager <bcm>`    | Contains interface independent broadcast manager     |
|                                     | code.                                                |
+-------------------------------------+------------------------------------------------------+


Step-by-Step Guide
^^^^^^^^^^^^^^^^^^

1. **Set Up Your Development Environment**

   1. Fork the python-can repository on GitHub to your own account.

   2. Clone your fork to your computer:

      .. code-block:: bash

         git clone https://github.com/<your-username>/python-can.git
         cd python-can

   3. (Recommended) Create and activate a virtual environment.
      This keeps your dependencies isolated and avoids interfering with your system Python:

      .. code-block:: bash

         python -m venv .venv
         source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
         python -m pip install --upgrade pip

   .. note::

      Some of the checks run with tox require Python 3.13 to be available on your system.
      If you want to run all checks locally, please ensure Python 3.13 is installed and accessible.

   4. Install the library in "editable" mode with development tools:

      .. code-block:: bash

         pip install --group dev -e .

      This command installs python-can and all tools needed for development (testing, formatting, etc.).

   5. Create a new branch for your work:

      .. code-block:: bash

         git checkout -b my-feature-branch

2. **Make Your Changes**

   - Edit the code, documentation, or tests as needed.
   - If you fix a bug or add a feature, try to add or update tests in the ``test/`` directory.
   - If your change affects how users interact with python-can, update the documentation in ``doc/`` and relevant docstrings.

3. **Test Your Changes**

   We use `tox <https://tox.wiki>`_ to run all checks and tests.
   Tox automates formatting, linting, type checking, running tests, and building documentation.

   To run all checks:

   .. code-block:: bash

      tox

   This may take a few minutes. If you see errors, read the output for hints on what to fix.

   If you want to check only a specific aspect, you can run an individual check:

   - **Formatting:**

     .. code-block:: bash

        tox -e format

     This only checks code formatting using ``black``. If you need to automatically format your code, run:

     .. code-block:: bash

        black .

   - **Linting:**

     .. code-block:: bash

        tox -e lint

     Checks code style using ``ruff`` and ``pylint``.

   - **Type Checking:**

     .. code-block:: bash

        tox -e type

     Checks for type errors using ``mypy``.

   - **Tests:**

     .. code-block:: bash

        tox -e py

     Runs all tests using ``pytest``.

   - **Documentation:**

     .. code-block:: bash

        tox -e docs

     Builds the documentation and runs doc tests.

4. **Add a News Fragment**

   A news fragment is a small text file describing your change (such as a bugfix, new feature, 
   or deprecation). These fragments are collected and used by towncrier to automatically 
   generate the changelog for each release.
   
   1. To create a news fragment, you can use the towncrier CLI. For example:

      .. code-block:: bash

         towncrier create -c "Describe your change here" 1234.added.md

      This will create a file in ``doc/changelog.d/`` with your message and the correct type.

   2. Alternatively, you can manually create a file in ``doc/changelog.d/``. The filename should follow
      the format ``<issue-or-pr-number>.<type>.md`` (e.g., ``1234.added.md``).
      Valid types are: `added`, `changed`, `deprecated`, `removed`, `fixed` and `security`.
   
   3. For more details, see the `towncrier documentation <https://towncrier.readthedocs.io/en/stable/>`_.

5. **Push and Submit Your Contribution**

   1. Push your branch to your fork:

      .. code-block:: bash

         git push origin my-feature-branch

   2. Open a pull request from your branch to the ``main`` branch of the main python-can repository on GitHub.

   3. Please be patient—maintainers review contributions as time allows, since this is a volunteer-run project.


Creating a new interface/backend
--------------------------------

These steps are a guideline on how to add a new backend to python-can.

- Create a module (either a ``*.py`` or an entire subdirectory depending
  on the complexity) inside ``can.interfaces``
- Implement the central part of the backend: the bus class that extends
  :class:`can.BusABC`.
  See :ref:`businternals` for more info on this one!
- Register your backend bus class in ``BACKENDS`` in the file ``can.interfaces.__init__.py``.
- Add docs where appropriate. At a minimum add to ``doc/interfaces.rst`` and add
  a new interface specific document in ``doc/interface/*``.
  It should document the supported platforms and also the hardware/software it requires.
  A small snippet of how to install the dependencies would also be useful to get people started without much friction.
- Also, don't forget to document your classes, methods and function with docstrings.
- Add tests in ``test/*`` where appropriate.
  To get started, have a look at ``back2back_test.py``:
  Simply add a test case like ``BasicTestSocketCan`` and some basic tests will be executed for the new interface.

.. attention::
    We strongly recommend using the :ref:`plugin interface` to extend python-can.
    Publish a python package that contains your :class:`can.BusABC` subclass and use
    it within the python-can API. We will mention your package inside this documentation
    and add it as an optional dependency.


Creating a new Release
----------------------

Releasing a new version of python-can is a multi-step process. 
Please follow these steps to ensure a smooth and consistent release:

1. **Preparation**

   - Check if any deprecations are pending and address them as needed.
   - Update ``CONTRIBUTORS.txt`` with any new contributors.
   - For larger changes, update ``doc/history.rst``.
   - Sanity check that documentation is up to date with the code.

2. **Build the Changelog with Towncrier**

   The changelog is generated from news fragments using `towncrier <https://towncrier.readthedocs.io>`_. 
   The workflow differs slightly for pre-releases and final releases:

   - **Pre-releases (e.g., alpha, beta, rc):**

     - Build the changelog without deleting news fragments, so they can be included in the final release.
     - Use the ``--keep`` option to keep fragments:

       .. code-block:: bash

          towncrier build --version X.Y.Zrc1 --keep

     - This will append the pre-release changelog to ``CHANGELOG.md`` but keep the fragments in ``doc/changelog.d/``.

   - **Final releases:**

     - Remove any previous pre-release changelog section from ``CHANGELOG.md`` (if present).
     - Build the changelog and delete the news fragments:

       .. code-block:: bash

          towncrier build --version X.Y.Z --yes

     - This will update ``CHANGELOG.md`` and remove all processed fragments.

   .. note::
      The version you use in the ``towncrier build --version ...`` command should 
      exactly match the release tag (e.g., ``vX.Y.Z``) you use on GitHub. 
      This ensures that the links in the generated changelog work correctly.

3. **Create the Release on GitHub**

   - Go to the `GitHub Releases page <https://github.com/hardbyte/python-can/releases>`_.
   - Click "Draft a new release".
   - Set the tag name to match the version (e.g., ``vX.Y.Z``) and target the ``main`` branch.
   - Add release notes (you can copy from the newly generated section in ``CHANGELOG.md``).
   - Publish the release. This will trigger the automated build and upload workflow 
     via GitHub Actions (see `ci.yml <https://github.com/hardbyte/python-can/blob/main/.github/workflows/ci.yml>`_).

4. **Post-release Checks**

   - Verify the release on:

     - `PyPI <https://pypi.org/project/python-can/#history>`_
     - `Read the Docs <https://readthedocs.org/projects/python-can/versions/>`_
     - `GitHub Releases <https://github.com/hardbyte/python-can/releases>`_
