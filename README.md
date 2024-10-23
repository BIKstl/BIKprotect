		BIK protect
		BY BIKstl
ابزار قدرتمند هوش مصنوعی تست نفوذ
توسط بیکستل 

## Quick Start | شروع سریع

1. Create a virtual environment if necessary. (`virtualenv -p python3 venv`, `source venv/bin/activate`)
2. Install the project with `pip3 install git+https://github.com/BIKstl/BIKprotect`
3. **Ensure that you have link a payment method to your OpenAI account.** Export your API key with `export OPENAI_API_KEY='<your key here>'`,export API base with `export OPENAI_BASEURL='https://api.xxxx.xxx/v1'`if you need.
4. Test the connection with `BIKprotect-connection`
5. For Kali Users: use `tmux` as terminal environment. You can do so by simply run `tmux` in the native terminal.
6. To start: `BIKprotect --logging`

1. در صورت لزوم یک محیط مجازی ایجاد کنید. (`virtualenv -p python3 venv`, `source venv/bin/activate`)
2. پروژه را با `pip3 install git+https://github.com/BIKstl/Bikprotect`
3. **مطمئن شوید که یک کلید اوپن ای آی را در فایل ذکر شده وارد کنید `export OPENAI_API_KEY='<your key here>'`,export API base with `export OPENAI_BASEURL='https://api.xxxx.xxx/v1'`
4. تست اتصال با  `BIKprotect-connection`
5. یک پیام برای کاربران کالی لینوکس :از tmux برای محیط ترمینال استفاده کنید 
می توانید این کار را با اجرای tmux در ترمینال اصلی استفاده کنید
6. فایل اجرا کنید: `BIKprotect --logging`

## Getting Started | شروع به کار
- **BIKprotect** is a penetration testing tool empowered by **ChatGPT**. 
- It is designed to automate the penetration testing process. It is built on top of ChatGPT and operate in an interactive mode to guide penetration testers in both overall progress and specific operations.
- **BIKprotect** is able to solve easy to medium HackTheBox machines, and other CTF challenges. You can check [this](./resources/README.md) example in `resources` where we use it to solve HackTheBox challenge **TEMPLATED** (web challenge). 
- A sample testing process of **BIKprotect** on a target VulnHub machine (Hackable II) is available at [here](./resources/BIKprotect_Hackable2.pdf).

- **BIKprotect** یک ابزار تست نفوذ است که توسط **ChatGPT** قدرت گرفته است. 
- برای خودکارسازی فرآیند تست نفوذ طراحی شده است. این بر روی ChatGPT ساخته شده است و در حالت تعاملی عمل می کند تا آزمایش کننده های نفوذ را هم در پیشرفت کلی و هم در عملیات خاص راهنمایی کند.
- **BIKprotect** قادر است ماشین های HackTheBox آسان تا متوسط ​​و سایر چالش های CTF را حل کند. می‌توانید [این] (./resources/README.md) مثال را در «منابع» بررسی کنید، جایی که ما از آن برای حل چالش HackTheBox **TEMPLATED** (چالش وب) استفاده می‌کنیم. 
- یک نمونه فرآیند تست **BIKprotect** روی یک ماشین VulnHub هدف (Hackable II) در [اینجا] (./resources/BIKprotect_Hackable2.pdf) موجود است.

## Installation | نصب
BIKprotect is tested under `Python 3.10`. Other Python3 versions should work but are not tested.
BIKprotect تحت «Python 3.10» آزمایش شده است. سایر نسخه های Python3 باید کار کنند اما آزمایش نمی شوند.

### Install with pip | نصب با pip

**BIKprotect** relies on **OpenAI API** to achieve high-quality reasoning. You may refer to the installation video [here](https://youtu.be/tGC5z14dE24).
1. Install the latest version with `pip3 install git+https://github.com/GreyDGL/BIKprotect`
   - You may also clone the project to local environment and install for better customization and development
     - `git clone https://github.com/BIKstl/BIKprotect`
     - `cd BIKprotect`
     - `pip3 install -e .`
2. To use OpenAI API
   - **Ensure that you have link a payment method to your OpenAI account.**
   - export your API key with `export OPENAI_API_KEY='<your key here>'`
   - export API base with `export OPENAI_BASEURL='https://api.xxxx.xxx/v1'`if you need.
   - Test the connection with `BIKprotect-connection`
3. To verify that the connection is configured properly, you may run `BIKprotect-connection`. After a while, you should see some sample conversation with ChatGPT.
   - A sample output is below
   ```
   You're testing the connection for BIKprotect v 0.11.0
   #### Test connection for OpenAI api (GPT-4)
   1. You're connected with OpenAI API. You have GPT-4 access. To start BIKprotect, please use <BIKprotect --reasoning_model=gpt-4>
   
   #### Test connection for OpenAI api (GPT-3.5)
   2. You're connected with OpenAI API. You have GPT-3.5 access. To start BIKprotect, please use <BIKprotect --reasoning_model=gpt-3.5-turbo-16k>
   ```
   - notice: if you have not linked a payment method to your OpenAI account, you will see error messages.
4. The ChatGPT cookie solution is deprecated and not recommended. You may still use it by running `BIKprotect --reasoning_model=gpt-4 --useAPI=False`. 

**BIKprotect** به **OpenAI API** برای دستیابی به استدلال با کیفیت بالا متکی است. می توانید به ویدیوی نصب [اینجا] (https://youtu.be/tGC5z14dE24) مراجعه کنید.
1. آخرین نسخه را با «pip3 install git+https://github.com/GreyDGL/BIKprotect» نصب کنید
   - همچنین می توانید پروژه را در محیط محلی کلون کرده و برای سفارشی سازی و توسعه بهتر نصب کنید
     - `git clone https://github.com/BIKstl/BIKprotect`
     - "cd BIKprotect".
     - `pip3 install -e .`
2. برای استفاده از OpenAI API
   - **اطمینان حاصل کنید که یک روش پرداخت را به حساب OpenAI خود پیوند داده اید.**
   - کلید API خود را با "صادرات OPENAI_API_KEY="<کلید شما در اینجا>" صادر کنید
   - در صورت نیاز، پایه API را با "صادرات OPENAI_BASEURL='https://api.xxxx.xxx/v1" صادر کنید.
   - اتصال را با 'BIKprotect-connection' تست کنید
3. برای تأیید اینکه اتصال به درستی پیکربندی شده است، می‌توانید «BIKprotect-connection» را اجرا کنید. پس از مدتی، باید چند نمونه مکالمه با ChatGPT را مشاهده کنید.
   - یک نمونه خروجی در زیر آمده است
   ```
   شما در حال آزمایش اتصال برای BIKprotect نسخه 0.11.0 هستید
   #### تست اتصال برای OpenAI api (GPT-4)
   1. شما با OpenAI API متصل هستید. شما به GPT-4 دسترسی دارید. برای راه اندازی BIKprotect، لطفاً از <BIKprotect --reasoning_model=gpt-4> استفاده کنید
   
   #### تست اتصال برای OpenAI api (GPT-3.5)
   2. شما با OpenAI API متصل هستید. شما به GPT-3.5 دسترسی دارید. برای راه اندازی BIKprotect، لطفاً از <BIKprotect --reasoning_model=gpt-3.5-turbo-16k> استفاده کنید
   ```
   - توجه: اگر یک روش پرداخت را به حساب OpenAI خود متصل نکرده باشید، پیام های خطا را مشاهده خواهید کرد.
4. راه حل کوکی ChatGPT منسوخ شده است و توصیه نمی شود. همچنان می‌توانید با اجرای «BIKprotect --reasoning_model=gpt-4 --useAPI=False» از آن استفاده کنید.

Thank you for supporting us with your stars | BIKstl
از اینکه با ستاره هایتان از ما حمایت می کنید سپاسگزاریم | بیکستل