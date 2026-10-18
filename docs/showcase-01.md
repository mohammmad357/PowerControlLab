# Engineering note 01 — No universal winner

**Mohammad Javad Holghoumi · 18 October 2026**

First published on [LinkedIn](https://www.linkedin.com/feed/update/urn:li:activity:7517347706277830656/), then added here with an editable visual summary and reproduction context.

![Two scenarios produce different controller rankings in the averaged inverter simulation. Bars share a zero origin and common scale.](https://raw.githubusercontent.com/mohammmad357/PowerControlLab/main/docs/showcase-01.svg)

## The question

Does the controller with the smallest tracking error under a nonlinear load also win when L/C parameters are mismatched? In these reference cases, it does not.

| Controller | Nonlinear load RMSE [V] | L/C mismatch RMSE [V] |
|---|---:|---:|
| Cascaded PI | 7.619 | 1.136 |
| SMC | 5.909 | 2.720 |
| Adaptive SMC | 3.872 | 3.344 |
| MPC | 2.510 | 1.571 |

Lower steady tracking RMSE is better for this metric. MPC has the smallest error in the nonlinear-load case; cascaded PI has the smallest error in the mismatch case. This comparison concerns tracking error, not a universal ranking across all engineering objectives.

## Experiment context

- Averaged LC-filtered H-bridge inverter: 400 V DC to 230 Vrms, 50 Hz.
- Four controller implementations; each keeps its fixed reference tuning across scenarios. Controllers use nominal parameters in mismatch cases.
- Control rate: 20 kHz. Integration step: 5 microseconds. Noise seed: 7.
- Evaluation window: final five complete cycles, [140, 240) ms.
- These values are transcribed from the existing [reference results at source revision a322d1f](https://github.com/mohammmad357/PowerControlLab/blob/a322d1f6a9f4133fed288fff3fecb60c90cb5b35/artifacts/reference/RESULTS.md). This note does not report a new simulation run.

## Look beyond the selected cases

The full eight-scenario averaged benchmark also covers nominal operation, load steps, DC sag, noise, delay and combined disturbances:

![Reference heatmaps of steady RMSE and THD across all eight averaged scenarios](https://raw.githubusercontent.com/mohammmad357/PowerControlLab/main/artifacts/reference/figures/benchmark.png)

Inspect the [full results](https://github.com/mohammmad357/PowerControlLab/blob/main/artifacts/reference/RESULTS.md), [benchmark protocol](https://github.com/mohammmad357/PowerControlLab/blob/main/docs/benchmark.md), [plant scope](https://github.com/mohammmad357/PowerControlLab/blob/main/docs/model.md) and [controller definitions](https://github.com/mohammmad357/PowerControlLab/blob/main/docs/controllers.md) before drawing broader conclusions. THD in the reference results includes harmonics 2–40; switching ripple is evaluated separately. A printed zero is a rounded metric, not proof of zero physical distortion.

## Reproduce and challenge

Follow the [installation instructions](https://github.com/mohammmad357/PowerControlLab#quick-start), then run:

```bash
python main.py --controller all --scenario all --mode averaged --seed 7 --output results/showcase-01
```

Use a new output directory for each experiment. Keep each run's `metrics.json`, `run.json` and waveforms together; `run.json` records the configuration, dependency versions and source hash. For the original reference-generation workflow, see `python scripts/reproduce.py` and the documented dependency versions.

A useful next investigation is to vary parameter mismatch and delay systematically, then check current constraints and numerical convergence. Those are proposed experiments, not additional results claimed by this note.

## Limits

These are simulation results for the documented plant, gains, disturbances and metric window. They do not establish hardware performance, real-time feasibility or universal controller superiority. Physical calibration and validation remain future work. No experimental measurements were added here.

## خلاصهٔ فارسی

در این نتایج مرجع، MPC در بار غیرخطی خطای کمتری دارد؛ اما PI در عدم‌تطابق پارامترهای سلف و خازن بهتر است. پس نتیجه به سناریو، تنظیمات و معیار ارزیابی وابسته است. تصویر و جدول از داده‌های ثبت‌شدهٔ پروژه ساخته شده‌اند و گزارش آزمایش سخت‌افزاری یا اجرای تازه نیستند.

AI assistance was used in development and presentation. Numerical claims are tied to the cited repository results.
