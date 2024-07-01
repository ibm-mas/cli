.PHONY: install build lint pyinstaller clean

venv:
	python3 -m venv venv

clean:
	rm -rf venv

install: venv
	. venv/bin/activate && python -m pip install --editable ../../python-devops[dev]
	. venv/bin/activate && python -m pip install --editable .[dev]

build: venv
	rm -f README.rst
	. venv/bin/activate && python -m build

lint: venv
	rm -f README.rst
	. venv/bin/activate && flake8 src --count --select=E9,F63,F7,F82 --show-source --statistics && flake8 src --count --exit-zero --max-complexity=10 --max-line-length=200 --statistics

pyinstaller: venv
	rm -f README.rst
	. venv/bin/activate && pyinstaller src/mas-upgrade --onefile --noconfirm --add-data="src/mas/devops/templates/ibm-mas-tekton.yaml:mas/devops/templates" --add-data="src/mas/devops/templates/subscription.yml.j2:mas/devops/templates/" --add-data="src/mas/devops/templates/pipelinerun-upgrade.yml.j2:mas/devops/templates/"
