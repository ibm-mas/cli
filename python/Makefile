.PHONY: install build lint clean

.venv:
	python3 -m venv .venv

clean:
	rm -rf .venv

install: .venv
	. .venv/bin/activate && python -m pip install --upgrade pip && python -m pip install --editable ../../python-devops[dev]
	. .venv/bin/activate && cd .. && python -m pip install --editable .[dev]

build: install
	. .venv/bin/activate && cd .. && python -m build

test: .venv install
	. .venv/bin/activate && cd .. && pytest python/test python/tests

lint: .venv
	. .venv/bin/activate && flake8 src --count --select=E9,F63,F7,F82 --show-source --statistics && flake8 src --count --exit-zero --max-complexity=10 --max-line-length=200 --statistics

.PHONY: run-help
run-help:
	. .venv/bin/activate && python src/mas-cli --help
