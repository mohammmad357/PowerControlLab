"""Run with: streamlit run dashboard/app.py"""

import io
import json
from dataclasses import asdict

import numpy as np
import pandas as pd
import streamlit as st

from powercontrollab import PlantConfig, SimulationConfig, simulate
from powercontrollab.analysis import compute_metrics
from powercontrollab.analysis.harmonics import harmonic_metrics
from powercontrollab.analysis.metrics import analysis_slice
from powercontrollab.controllers import CONTROLLERS, LABELS
from powercontrollab.reporting import provenance
from powercontrollab.scenarios import SCENARIOS

st.set_page_config(page_title="PowerControlLab", page_icon="⚡", layout="wide")
st.caption("POWER ELECTRONICS / CONTROL / REPRODUCIBLE EXPERIMENTS")
st.title("PowerControlLab")
st.markdown("Explore how four controllers regulate an LC-filtered inverter under disturbances.")

with st.sidebar:
    st.header("Experiment")
    with st.form("experiment"):
        controller = st.selectbox("Controller", list(CONTROLLERS), index=1, format_func=LABELS.get)
        compare = st.checkbox("Compare all four controllers")
        scenario = st.selectbox("Scenario", list(SCENARIOS))
        mode = st.selectbox("Plant model", ["averaged", "switching"])
        dc = st.slider("DC voltage [V]", 350, 500, 400, 10)
        resistance = st.slider("Load resistance [Ω]", 25, 100, 50, 5)
        inductance = st.slider("Inductance [mH]", 1.0, 4.0, 2.0, 0.1)
        capacitance = st.slider("Capacitance [µF]", 10.0, 40.0, 20.0, 1.0)
        seed = st.number_input("Noise seed", min_value=0, value=7, step=1)
        submitted = st.form_submit_button("Run simulation", type="primary", width="stretch")
    st.caption("230 Vrms · 50 Hz · 20 kHz control and carrier frequency · 240 ms duration")
    st.caption("Simulation research tool. Hardware calibration and validation are future work.")

if submitted:
    try:
        plant = PlantConfig(
            dc_voltage=dc,
            load_resistance=resistance,
            inductance=inductance * 1e-3,
            capacitance=capacitance * 1e-6,
        )
        config = SimulationConfig(scenario=scenario, mode=mode, seed=int(seed), substeps=20)
        with st.spinner("Integrating the plant and evaluating tracking performance…"):
            selected = list(CONTROLLERS) if compare else [controller]
            results = [simulate(name, plant, config) for name in selected]
        st.session_state["results"] = results
    except (ValueError, RuntimeError) as error:
        st.error(str(error))

if "results" not in st.session_state:
    st.info("Choose an experiment in the sidebar, then run the simulation.")
    columns = st.columns(3)
    columns[0].metric("DC bus", "400 V")
    columns[1].metric("Voltage reference", "230 Vrms")
    columns[2].metric("Controllers", "4")
    st.markdown(
        "**Built to investigate tradeoffs:** tracking, harmonics, disturbance recovery, "
        "control effort and solver behavior. All benchmark values come from the model."
    )
else:
    results = st.session_state["results"]
    first = results[0]
    st.caption(
        f"Displayed run: {first.config.scenario} / {first.config.mode} / "
        f"{first.plant.dc_voltage:g} V DC / R={first.plant.load_resistance:g} Ω / "
        f"L={first.plant.inductance * 1000:g} mH / "
        f"C={first.plant.capacitance * 1e6:g} µF / seed={first.config.seed}. "
        "Sidebar changes take effect when you run again."
    )
    rows = [compute_metrics(result) for result in results]
    frame = pd.DataFrame(rows)
    st.dataframe(
        frame[
            [
                "controller",
                "thd_percent",
                "steady_rmse_v",
                "output_rms_v",
                "settling_time_s",
                "peak_inductor_current_a",
                "solver_fallbacks",
            ]
        ],
        hide_index=True,
        width="stretch",
    )
    st.caption(
        "THD uses harmonics 2–40 over the last five complete cycles. Empty settling time "
        "means the 2% cycle-RMS error band was not maintained within this run."
    )
    signals, harmonics, details = st.tabs(["Waveforms", "Harmonics", "Reproduce & download"])
    with signals:
        # Plot a display subset only; numerical metrics always use full-rate samples.
        stride = max(1, len(first.time) // 3000)
        index = first.time[::stride] * 1000
        volts = {LABELS[r.controller]: r.voltage[::stride] for r in results}
        volts["Reference"] = first.reference[::stride]
        st.subheader("Reference and output voltage")
        st.line_chart(pd.DataFrame(volts, index=index), x_label="Time [ms]", y_label="Voltage [V]")
        left, right = st.columns(2)
        with left:
            st.subheader("Tracking error")
            st.line_chart(
                pd.DataFrame(
                    {LABELS[r.controller]: (r.reference - r.voltage)[::stride] for r in results},
                    index=index,
                ),
                x_label="Time [ms]",
                y_label="Error [V]",
            )
        with right:
            st.subheader("Applied modulation")
            st.line_chart(
                pd.DataFrame(
                    {LABELS[r.controller]: r.modulation[::stride] for r in results}, index=index
                ),
                x_label="Time [ms]",
                y_label="Modulation",
            )
        st.caption(
            "Waveforms are subsampled for display. Download full-rate arrays to inspect PWM."
        )
    with harmonics:
        data = {}
        for result in results:
            h = harmonic_metrics(
                result.voltage[analysis_slice(result)],
                1 / (result.time[1] - result.time[0]),
                result.plant.frequency,
            )
            data[LABELS[result.controller]] = h["harmonic_rms_v"][1:]
        st.bar_chart(
            pd.DataFrame(data, index=np.arange(2, 41)),
            x_label="Harmonic order",
            y_label="RMS voltage [V]",
        )
        st.caption("The fundamental is omitted here so distortion is visible.")
    with details:
        payload = {
            "plant": asdict(first.plant),
            "simulation": asdict(first.config),
            "provenance": provenance(),
            "metrics": rows,
        }
        st.download_button(
            "Download report JSON",
            json.dumps(payload, indent=2, allow_nan=False),
            "powercontrollab-report.json",
            "application/json",
        )
        st.download_button(
            "Download benchmark CSV",
            frame.to_csv(index=False),
            "powercontrollab-benchmark.csv",
            "text/csv",
        )
        buffer = io.BytesIO()
        np.savez_compressed(
            buffer,
            **{
                f"{r.controller}_{key}": value for r in results for key, value in r.arrays().items()
            },
        )
        st.download_button(
            "Download full waveforms",
            buffer.getvalue(),
            "waveforms.npz",
            "application/octet-stream",
        )
        st.json(payload)
