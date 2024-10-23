.PHONY: build install clean format lint unittest test

build: # force build
	poetry build

install:
	poetry install

format: updatesetup
	isort BIKprotect
	black BIKprotect

updatesetup:
	bash BIKprotect/scripts/update.sh