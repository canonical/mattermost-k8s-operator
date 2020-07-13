lint:
	@echo "Running flake8"
	@tox -e lint

# We actually use the build directory created by charmcraft,
# but the .charm file makes a much more convenient sentinel.
unittest: mattermost.charm
	@tox -e unit

test: lint unittest

clean:
	@echo "Cleaning files"
	@git clean -fXd

mattermost.charm: src/*.py requirements.txt
	charmcraft build

.PHONY: lint test unittest clean
