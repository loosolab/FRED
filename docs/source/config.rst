Config File
============

FRED's functions rely on information defined in a config file. You can create your own config file to modify FRED and pass it as an parameter when calling a function.
If no config is stated, FRED uses the default configuration.

Default config
^^^^^^^^^^^^^^^^

.. code-block:: yaml

        structure: fred
        whitelist_repository: https://github.com/loosolab/FRED_whitelists
        private_access:
            name: 
            token: 
        branch: main
        whitelist_path: fred
        update_whitelists: True
        output_path: .
        filename: '_metadata' 
        email: example@email.de

Config Keys
^^^^^^^^^^^^^^^^

.. list-table::
   :width: 100%
   :widths: 30 35 35

   * - Key
     - Description
     - Default
   * - structure
     - path to a structure YAML file (keys.yaml) or 'fred' to use the default structure
     - fred
   * - whitelist_repository
     - URL to a repository holding whitelists
     - https://github.com/loosolab/FRED_whitelists
   * - private access
     - Information for accessing the whitelist repository with an access token if the repository is private
     - keys: name, token
   * - private access - name 
     - username for access token (github) or oauth2 for project access token (gitlab)
     - 
   * - private access - token
     - personal (github) or project (gitlab) access token
     - 
   * - branch
     - The branch of the whitelist repository; can also be set to versions if version tags are used (e.g. 1.2.0 or 1.2.*)
     - main
   * - whitelist_path
     - path the whitelist repository is cloned to or 'fred' to use the default path
     - fred
   * - update_whitelists
     - bool to define if whitelists should be updated/pulled when running FRED
     - True 
   * - output_path
     - path plots and valiadtion reporst should be saved to
     - .
   * - filename
     - identifier added to the filenames to distinguish them as metadata files (e.g. '_metadata' leads to naming <my_file>_metadata.yaml)
     - '_metadata'
   * - email
     - Email address needed to extract publication records from PUBMED
     - example@email.de
