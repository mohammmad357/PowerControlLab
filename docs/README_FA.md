# راهنمای فارسی PowerControlLab

این پروژه یک آزمایشگاه شبیه‌سازی برای اینورتر تک‌فاز با ورودی ۴۰۰ ولت DC و خروجی هدف
۲۳۰ ولت مؤثر، ۵۰ هرتز است. مدل فیلتر LC، چهار کنترلر و آزمایش‌های اغتشاش در یک
پکیج قابل نصب پایتون قرار دارند.

## شروع سریع

پس از نصب Python 3.11 یا جدیدتر، مخزن را دریافت و یک محیط مجازی فعال کنید:

```bash
git clone https://github.com/mohammmad357/PowerControlLab.git
cd PowerControlLab
python -m venv .venv
```

| محیط | فعال‌سازی |
|---|---|
| Windows PowerShell | `.\.venv\Scripts\Activate.ps1` |
| Windows CMD | `.venv\Scripts\activate.bat` |
| Linux / macOS | `source .venv/bin/activate` |

اگر PowerShell اجرای اسکریپت را مسدود کرد، به تغییر سیاست امنیتی نیاز نیست؛
پایتون همان محیط را مستقیم اجرا کنید:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev,dashboard]"
.\.venv\Scripts\python.exe main.py --controller smc --load nonlinear --output results/fa-first-run
```

برای فرمان‌های بعدی نیز می‌توانید به‌جای `python` از همین مسیر استفاده کنید.
نمونه‌های زیر برای محیط فعال‌شده‌اند. همهٔ فرمان‌ها از ریشهٔ مخزن اجرا می‌شوند.

```bash
python -m pip install -e ".[dev,dashboard]"
python main.py --controller smc --load nonlinear
python main.py --controller all --scenario all
streamlit run dashboard/app.py
```

## امکانات نسخه اول

- PI آبشاری، کنترل مد لغزشی، SMC با بهره تطبیقی و MPC با حل واقعی QP.
- مدل میانگین و مدل سوئیچینگ SPWM با زمان دقیق لبه‌ها.
- تغییر بار و ولتاژ DC، نویز سنسور، عدم قطعیت L/C، تأخیر و بار پل دیودی با خازن DC.
- گزارش THD، خطای RMS، زمان بازیابی، جریان پیک، اشباع و وضعیت حل‌گر.
- ذخیره داده خام، تنظیمات و نسخه کتابخانه‌ها برای تکرارپذیری.

اعداد README از اجرای برنامه تولید می‌شوند. هیچ رتبه‌بندی از پیش تعیین‌شده‌ای میان
کنترلرها وجود ندارد. در این نسخه، Digital Twin به پایه مدل‌سازی و شبیه‌سازی اشاره
می‌کند؛ تطبیق با داده و اعتبارسنجی سخت‌افزار واقعی هنوز انجام نشده است.

THD بر اساس هارمونیک‌های ۲ تا ۴۰ و پنج سیکل کامل انتهایی محاسبه می‌شود. مدل میانگین
ریپل سوئیچینگ را ندارد. زمان نشست زمانی گزارش می‌شود که خطای RMS یک سیکل در باند
۲٪ باقی بماند؛ خروجی `null` یا `not settled` یعنی این شرط در بازه شبیه‌سازی تأیید نشد.

معادلات و فرض‌ها در [مدل فیزیکی](model.md)، قوانین و ضرایب در [کنترلرها](controllers.md)
و تعریف دقیق آزمایش‌ها در [پروتکل بنچمارک](benchmark.md) توضیح داده شده‌اند.

