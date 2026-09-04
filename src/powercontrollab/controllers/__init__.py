"""Controller factory: every simulation constructs fresh controller state."""

from .adaptive_smc import AdaptiveSMCController
from .mpc import MPCController
from .pi import PIController
from .smc import SMCController

CONTROLLERS = {
    "pi": PIController,
    "smc": SMCController,
    "adaptive-smc": AdaptiveSMCController,
    "mpc": MPCController,
}
LABELS = {"pi": "Cascaded PI", "smc": "SMC", "adaptive-smc": "Adaptive SMC", "mpc": "MPC"}


def make_controller(name, plant, ramp_time=0.02):
    if name not in CONTROLLERS:
        raise ValueError(f"Unknown controller {name!r}; choose from {tuple(CONTROLLERS)}")
    return CONTROLLERS[name](plant, ramp_time)
