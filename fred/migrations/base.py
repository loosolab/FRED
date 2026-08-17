class Migration:
    """
    Base class for a versioned FRED metadata migration.

    Each migration lives in its own ``fred/migrations/v<version>/`` package
    and exposes a module-level ``MIGRATION`` instance of a subclass of this
    class. The generic runner (``fred/migrations/runner.py``) discovers and
    dispatches to migrations purely through this interface, so a new
    migration can be added without changing ``fred/metaTools.py`` or the
    runner.
    """

    #: Human-readable FRED version this migration targets, e.g. "3.0.0".
    version = None

    def add_arguments(self, parser):
        """
        Register this migration's own CLI arguments on ``parser``.
        Called by the runner with a fresh argparse.ArgumentParser before
        parsing the remaining command line arguments.
        """
        raise NotImplementedError

    def run(self, args):
        """
        Execute the migration using the parsed arguments returned by the
        parser configured in add_arguments().
        """
        raise NotImplementedError
