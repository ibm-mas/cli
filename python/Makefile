.PHONY: install build clean

venv:
	python3 -m venv venv

clean:
	rm -rf venv

install: venv
	. venv/bin/activate && python -m pip install --editable .[dev]

build: venv
	rm README.rst
	. venv/bin/activate && python -m build
