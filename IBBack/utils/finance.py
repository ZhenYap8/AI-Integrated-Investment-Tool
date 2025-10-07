# DEPRECATED: use utils.finance2 instead.
# This shim re-exports finance2 symbols for backward compatibility.
import warnings as _warnings

# Re-export everything from the refactored module
from .finance2 import *  # noqa: F401,F403

_warnings.warn(
    "utils.finance is deprecated; migrate imports to utils.finance2",
    DeprecationWarning,
    stacklevel=2,
)
