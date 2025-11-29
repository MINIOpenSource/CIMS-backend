.PHONY: build ruff black test grpc clean

build: grpc
	pip install --no-cache-dir .

ruff:
	ruff check .
	ruff format .

black:
	black --check .

test:
	pytest

grpc: clean
	python -m grpc_tools.protoc -I./cims --python_out=./cims --grpc_python_out=./cims $(shell find ./cims/Protobuf -name "*.proto")
	python fix_imports.py

clean:
	find cims/Protobuf -name "*_pb2*.py" -delete
