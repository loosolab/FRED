Using a Custom Whitelist Repository
=====================================

FRED's whitelists are stored in the publicly accessible repository `FRED_whitelists <https://github.com/loosolab/FRED_whitelists>`_. To create custom whitelists or extend existing ones, you can fork or clone this repository and configure FRED to use your own version.

Setting up a custom repository
--------------------------------

1. **Fork** the `FRED_whitelists <https://github.com/loosolab/FRED_whitelists>`_ repository on GitHub, or **clone** it locally and push it to a new repository of your own.

2. Point FRED to your custom repository by updating the ``whitelist_repo`` and ``whitelist_branch`` fields in your config file:

.. code-block:: yaml

    whitelist_repo: https://github.com/your-org/your-whitelists.git
    whitelist_branch: main

3. Extend or modify the whitelists as needed. Instructions for adding values, new whitelists, experimental factors, and organisms can be found in the other pages of this section.


Synchronizing with the official repository
-------------------------------------------

To keep your custom whitelists up to date with changes from the official repository, a GitHub Action is provided in the ``.github/workflows/sync-upstream.yml`` file of the FRED_whitelists repository.

What it does
^^^^^^^^^^^^^

The action runs automatically every Monday at 08:00 UTC. It fetches new commits from the official upstream repository and opens a pull request in your fork with the changes. If no conflicts are detected, the PR can be merged directly. If conflicts exist, the PR includes instructions for resolving them locally before merging.

Enabling the action
^^^^^^^^^^^^^^^^^^^^

GitHub Actions are disabled by default in forked repositories. To enable them, go to the **Actions** tab of your fork and click **I understand my workflows, go ahead and enable them**.

Configuration
^^^^^^^^^^^^^^

Two environment variables at the top of the workflow file can be adjusted:

.. list-table::
   :width: 100%
   :widths: 25 75

   * - ``UPSTREAM_BRANCH``
     - The branch of the official repository to sync from. Default: ``main``.
   * - ``AUTOMERGE``
     - Set to ``true`` to automatically merge conflict-free PRs. Set to ``false`` (default) to always require manual review before merging.

Triggering a manual sync
^^^^^^^^^^^^^^^^^^^^^^^^^

In addition to the weekly schedule, the action can be started at any time manually:

1. Go to your repository on GitHub.
2. Navigate to **Actions** → **Sync Upstream**.
3. Click **Run workflow**.
