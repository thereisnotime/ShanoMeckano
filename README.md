# ShanoMeckano

A quick and dirty solution for automated time logging for [Meckano](https://app.meckano.co.il/#dashboard) time tracking app.

- [ShanoMeckano](#shanomeckano)
- [Usage](#usage)
    - [Requirements](#requirements)
    - [Install](#install)
    - [Start](#start)
- [Behaviour](#behaviour)
- [Todo](#todo)
- [Debugging](#debugging)


# Usage

### Requirements
* Python > 3.8
* pip3

### Install
With your shell terminal (or git bash on Windows):
```console
git clone https://github.com/thereisnotime/ShanoMeckano
cd ShanoMeckano
# Install all requirements
pip3 install -r requirements.txt
cp .env.example .env
# Edit .env and enter your credentials
```

### Start

```shell
python3 main.py
```

# Behaviour
To ensure randomness, the following methods have been implemented:
- It will add random amount of seconds when starting and ending work day.
- It will logout or just close the browser after checking in or out randomly.
- Generates random user agent on each run.
- Uses random browser (Firefox or UndetectedChromium).

# Todo
Some simple roadmap:
- [ ] Add mechanism for scraping public SOCK4/5 proxies.
- [ ] Add mechanism to autoselect a working proxy for every login.
- [ ] Add a mechanism which starts Selenium with a different process name, so it can run a long side your standard browser.
- [ ] Add mechanism for random small and big lunch breaks.
- [ ] Implement AcitonChains for smoother workflow.
- [ ] Add CLI mode for futher automation.
- [ ] Add autoloader for chromedriver.
- [ ] Add mouse jittering to increase the "human" level for reCaptcha.
- [ ] Remove sleeps and add expected condiitons.
- [ ] Remove WET code and reduce imports.
- [ ] Add support for multiple users with their separate configurations.

# Debugging
- In your .env file, change:
```shell
DEBUG_MODE='True'
```