import sys
import tempfile

from recipesauto.constants import logger
from recipesauto.entrypoint import prepare_context


def main():
    try:

        prepare_context(sys.argv[1:])

        # import this only once the Context has been initialized, so that it gets an
        # initialized context
        from recipesauto.processor import Processor

        Processor().run()

    except SystemExit:
        logger.error("Execution failed, exiting")
        raise
    except Exception as exc:
        logger.exception(exc)
        logger.error(f"Execution failed with the following error: {exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
