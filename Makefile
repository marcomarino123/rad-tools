.DEFAULT_GOAL := help

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = source
BUILDDIR      = build

# Put it first so that "make" without argument is like "make help".
# help:
# 	@$(SPHINXBUILD) -M help "docs/$(SOURCEDIR)" "docs/$(BUILDDIR)" $(SPHINXOPTS) $(O)

# $(O) is meant as a shortcut for $(SPHINXOPTS).
html: 
	@$(SPHINXBUILD) -M html "docs/$(SOURCEDIR)" "docs/$(BUILDDIR)" $(SPHINXOPTS) $(O)

html-examples: 
	@make examples
	@$(SPHINXBUILD) -M html "docs/$(SOURCEDIR)" "docs/$(BUILDDIR)" $(SPHINXOPTS) $(O)

doctest: 
	@$(SPHINXBUILD) -b doctest "docs/$(SOURCEDIR)" "docs/$(BUILDDIR)" $(SPHINXOPTS) $(O)

clean:
	-@rm -r docs/build
	-@rm -r docs/source/api/generated
	-@rm -r docs/source/api/crystal/generated
	-@rm -r docs/source/api/exchange/generated
	-@rm -r docs/source/api/spinham/generated
	-@rm -r docs/source/api/magnons/generated
	-@rm -r docs/source/api/_autosummary
	-@rm -r rad_tools.egg-info
	-@rm -r build
	-@rm -r dist
	-@rm -r .env3.11/lib/python3.11/site-packages/radtools
	-@rm -r .env3.11/lib/python3.11/site-packages/rad_tools*
	-@rm -r .env3.11/bin/rad-*
	-@rm -r .env3.10/lib/python3.10/site-packages/radtools
	-@rm -r .env3.10/lib/python3.10/site-packages/rad_tools*
	-@rm -r .env3.10/bin/rad-*
	-@rm -r .env3.9/lib/python3.9/site-packages/radtools
	-@rm -r .env3.9/lib/python3.9/site-packages/rad_tools*
	-@rm -r .env3.9/bin/rad-*
	-@rm -r .env3.8/lib/python3.8/site-packages/radtools
	-@rm -r .env3.8/lib/python3.8/site-packages/rad_tools*
	-@rm -r .env3.8/bin/rad-*

install:
	@python3 -m pip install .

test: 
	@pytest -s

test-all: clean install test bravais-pictures examples html doctest
	@echo "Done"


.ONESHELL:
pip: prepare-release
	@read -p "Press Enter to publish to PyPI"
	-@rm -r dist
	-@rm -r build
	-@rm -r radtools.egg-info
	@python3 setup.py sdist bdist_wheel 
	@python3 -m twine upload --repository pypi dist/* --verbose
	@git tag -a "$(VERSION)" -m "Version $(VERSION)"


help:
	@echo "\x1b[31m"
	@echo "Please specify what do you want to do!"
	@echo "\x1b[0m"
	@echo "Available options are:\n"
	@echo "    help - show this message"
	@echo "    html - build the html docs"
	@echo "    html-examples - update examples and build html docs"
	@echo "    doctest - run doctests"
	@echo "    clean - clean all files from docs and pip routines"
	@echo "    install - install the package"
	@echo "    test - execute unit tests"
	@echo "    test-all - execute full testing suite"
	@echo "    pip - publish the package to the PyPi index"
	@echo "    bravais-pictures - update pictures of bravais lattices"
	@echo "    prepare-release - prepare the package for release"
	@echo "    docs-pictures - update pictures for the docs"
	@echo "    new-script - create templates for the new script"
	@echo "    examples - update examples for all scripts"
	@echo "    generate-script-docs - generate docs for all scripts"
	@echo

bravais-pictures:
	@python3 tools/plot-bravais-lattices.py

VERSION="None"
prepare-release:
	@python3 -u tools/prepare-release.py -v $(VERSION)

docs-pictures:
	@python3 tools/plot-data-structure.py
	@python3 tools/plot-notation.py

NAME="None"
new-script:
	@python3 tools/new-script.py -n $(NAME)

SCRIPT="all"
examples: 
	@python3 tools/plot-script-guide.py -s $(SCRIPT) 

SCRIPT="all"
generate-script-docs: 
	@python3 tools/generate-script-docs.py -s $(SCRIPT) 
