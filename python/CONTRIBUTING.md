Contributing
===============================================================================

Windows Development Tips
-------------------------------------------------------------------------------

```
..\python-devops\.venv\Scripts\activate

python -m pip install --editable .\python[dev]
python -m pip install --editable ..\python-devops[dev]
```

If done correctly, this will show up in the output of `pip list` like so:

```
Package                   Version     Editable project location
------------------------- ----------- ------------------------------------------------------------
mas-cli                   100.0.0     C:\Users\xxx\Documents\GitHub\ibm-mas\cli\python
mas-devops                100.0.0     C:\Users\xxx\Documents\GitHub\ibm-mas\python-devops
```


```
.\env.ps1
python .\python\src\mas-install --help

python .\python\src\mas-install
```


PyInstaller Development Tips
-------------------------------------------------------------------------------

```
python -m venv .venv
.\.venv\Scripts\activate

cd python
python -m pip install --upgrade pip
python -m pip install .[dev]
pyinstaller --onefile --noconfirm --collect-data mas.devops --collect-data mas.cli src/mas-cli

```