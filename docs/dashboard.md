# Using the experiment dashboard

After installing the dashboard extra from the [quick start](../README.md#quick-start),
launch from the repository root:

```sh
python -m streamlit run dashboard/app.py
```

In PowerShell without activating the virtual environment:

```powershell
.\.venv\Scripts\python.exe -m streamlit run dashboard/app.py
```

Open the local address printed by Streamlit in your browser.

## Run and inspect

1. Choose controller, scenario and plant model in the sidebar.
2. Optionally select **Compare all four controllers**.
3. Set the plant values and noise seed, then press **Run simulation**.
4. Check the **Displayed run** caption before interpreting the table.
5. Inspect **Waveforms**, **Harmonics**, and **Reproduce & download**.

Sidebar edits do not change the stored result until a new run is submitted. If a
new run fails, a previous successful result may remain visible; use the displayed
configuration rather than assuming it matches the current sidebar.

## Units and numerical settings

The sidebar takes inductance in **mH** and capacitance in **microfarads**. The CLI
takes **henry** and **farad**. A dashboard setting of 2.5 mH and 25 microfarads
corresponds to `--inductance 0.0025 --capacitance 0.000025`.

The current dashboard uses 20 integration substeps; the CLI defaults to 10.
For a comparable CLI run, specify `--substeps 20` and match the scenario, mode,
plant values and seed. Consult the exported simulation configuration rather than
assuming default CLI settings reproduce a dashboard result.

## Export formats

| Download | Contents |
|---|---|
| Report JSON | Plant, simulation configuration, provenance and metrics for the selected controllers |
| Benchmark CSV | The displayed metric rows |
| Full waveforms | Full-rate arrays with controller-prefixed keys in an NPZ archive |

The dashboard report is not the same schema as a CLI per-run `run.json`.
Preserve the report and arrays together. Graphs are subsampled for display; the
metrics use full-rate samples. Use exported arrays to inspect switching ripple.

An empty settling-time cell means the criterion was not established within the
run, not zero recovery time. Harmonic bars omit the fundamental. These simulation
results do not establish physical validation or a real-time execution guarantee.

[Metric definitions](benchmark.md) · [CLI guide](cli.md)
