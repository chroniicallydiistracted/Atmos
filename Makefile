PY_SRCS=services/api/src services/ingestion/src services/tiler

.PHONY: lint format format-check

lint:
	ruff check $(PY_SRCS)

format:
	ruff check --fix $(PY_SRCS)
	black $(PY_SRCS)

format-check:
	ruff check $(PY_SRCS)
	black --check $(PY_SRCS)
