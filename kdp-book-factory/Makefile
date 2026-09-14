PY ?= python3
SLUG ?= esempio-metodo-tre-ore

.PHONY: install test demo book plan qa clean

install:
	$(PY) -m pip install -r requirements.txt

test:
	$(PY) -m unittest discover -s tests -v

demo:            ## pipeline completa senza chiamate API (testo segnaposto)
	$(PY) -m kdpfactory --dry-run all $(SLUG)

book:            ## pipeline completa con Claude
	$(PY) -m kdpfactory all $(SLUG)

plan:
	$(PY) -m kdpfactory plan $(SLUG)

qa:
	$(PY) -m kdpfactory qa $(SLUG)

clean:
	rm -rf books/*/build books/*/manuscript books/*/state.json
