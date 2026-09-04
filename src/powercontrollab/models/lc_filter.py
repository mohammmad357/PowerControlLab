"""LC state-space model x = [inductor current, capacitor voltage]."""

import numpy as np
from scipy.signal import cont2discrete


def continuous_matrices(inductance, capacitance, resistance, inductor_resistance):
    a = np.array(
        [
            [-inductor_resistance / inductance, -1 / inductance],
            [1 / capacitance, -1 / (resistance * capacitance)],
        ]
    )
    # Input 1 is bridge voltage; input 2 is additional load current.
    b = np.array([[1 / inductance, 0], [0, -1 / capacitance]])
    return a, b


def discrete_matrices(plant, period=None):
    a, b = continuous_matrices(
        plant.inductance, plant.capacitance, plant.load_resistance, plant.inductor_resistance
    )
    ad, bd, _, _, _ = cont2discrete(
        (a, b, np.eye(2), np.zeros((2, 2))),
        plant.period if period is None else period,
        method="zoh",
    )
    return ad, bd
