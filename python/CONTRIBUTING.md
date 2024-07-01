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