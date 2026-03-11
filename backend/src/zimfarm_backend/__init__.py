import logging
import warnings

from zimfarm_backend.common.constants import DEBUG

# The offliner configuration is dynamic and it has types built at runtime.
# However, because the database could contain data which does not meet these type
# constraints, reads from the database are often done with skip_validation set to True
# and this bypasses all validation. As a consequence, when dumping results to clients,
# Pydantic complains about types mismatch. This is often noisy and needs to be
# suppressed.
warnings.filterwarnings(
    "ignore",
    message=".*Pydantic serializer warnings.*",
    category=UserWarning,
)

logger = logging.getLogger("zimfarm_backend")

if not logger.hasHandlers():
    logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(asctime)s: %(levelname)s] %(message)s"))
    logger.addHandler(handler)
