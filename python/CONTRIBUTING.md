Contributing
===============================================================================

Development Tips
-------------------------------------------------------------------------------

Your virtualenv should look something like this:

```
Package             Version     Editable project location
------------------- ----------- -----------------------------------------------
blinker             1.9.0
cachetools          5.5.0
certifi             2024.8.30
charset-normalizer  3.4.0
click               8.1.7
colorama            0.4.6
durationpy          0.9
Flask               3.1.0
google-auth         2.35.0
halo                0.0.31
idna                3.10
itsdangerous        2.2.0
Jinja2              3.1.4
kubeconfig          1.1.1
kubernetes          31.0.0
log-symbols         0.0.14
MarkupSafe          3.0.2
mas-cli             100.0.0     /home/x/github/ibm-mas/installer/python
mas-devops          100.0.0     /home/x/github/ibm-mas/python-devops
oauthlib            3.2.2
openshift           0.13.2
pip                 22.0.2
prompt_toolkit      3.0.48
pyasn1              0.6.1
pyasn1_modules      0.4.1
python-dateutil     2.9.0.post0
python-string-utils 1.0.0
PyYAML              6.0.2
requests            2.32.3
requests-oauthlib   2.0.0
rsa                 4.9
setuptools          59.6.0
six                 1.16.0
spinners            0.0.24
tabulate            0.9.0
termcolor           2.5.0
urllib3             2.2.3
wcwidth             0.2.13
websocket-client    1.8.0
Werkzeug            3.1.3
```

Then you can run the install using:

```bash
cd python/src
python mas-cli --help
```

This will be running using the code in your workspace, when you make a change you don't need to rebuild anything, just restart the cli application.
