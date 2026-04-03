# rinohtype - Project Context

## Overview

**rinohtype** is a Python-based batch-mode document processor that renders structured documents to PDF based on document templates and style sheets. It's designed with a focus on user-friendly document layout and style customization.

**License:** AGPL-3.0-only (Affero GPL 3.0)  
**Author:** Brecht Machiels <brecht@opqode.com>  
**Repository:** https://github.com/brechtm/rinohtype  
**Documentation:** http://www.mos6581.org/rinohtype/master/

**Key Features:**
- Powerful page layout system with columns, running headers/footers, floatable elements, and footnotes
- Support for figures and tables (including sideways rendering)
- Automatic table of contents and index generation
- Automatic numbering and cross-referencing
- CSS-inspired style sheet system
- reStructuredText and CommonMark frontends
- Sphinx builder (drop-in replacement for LaTeX builder)
- OpenType, TrueType, and Type1 font support
- Built-in support for 1000+ Google Fonts
- PDF, PNG, and JPEG image embedding

## Technology Stack

- **Language:** Python (3.10+)
- **Package Manager:** Poetry
- **Task Runner:** Nox (with nox-poetry)
- **Test Framework:** pytest (with pytest-xdist, pytest-cov, pytest-assume)
- **Dependencies:** docutils, myst-parser, packaging, various typeface packages
- **Optional:** ziamath, cairosvg (for math rendering)

## Project Structure

```
src/
└── rinoh/              # Main source code
    ├── backend/        # PDF rendering backend
    ├── frontend/       # Input format parsers (reStructuredText, CommonMark, Sphinx)
    ├── font/           # Font handling
    ├── fonts/          # Font definitions (Adobe 14, Google Fonts)
    ├── language/       # Language-specific processing
    ├── stylesheets/    # Built-in style sheets
    ├── templates/      # Document templates (article, book)
    └── [core modules]  # document.py, layout.py, paragraph.py, table.py, etc.

doc/                    # Documentation source
tests/                  # Unit tests
tests_regression/       # Regression/integration tests
examples/               # Example documents
```

## Building and Running

### Installation from source
```bash
poetry install
```

### Activation
```bash
source .venv/bin/activate
```

### CLI Usage
```bash
# Render reStructuredText to PDF
rinoh input.rst

# Render with specific template
rinoh -t book input.rst

# Help
rinoh --help
```

### Sphinx Integration
```bash
sphinx-build -b rinoh . _build/rinoh
```

### Nox Sessions (Development Tasks)

```bash
# Run all default checks and tests
nox

# Run specific sessions
nox --session unit              # Unit tests only
nox --session regression        # Regression tests only
nox --session check             # Poetry validation
nox --session check_docs        # Documentation checks
nox --session build_docs        # Build documentation (HTML + PDF)

# Run on specific Python version
nox -e unit-3.11
nox -e regression-3.11
```

### Testing Details
- **Unit tests:** Quick tests focusing on individual components
- **Regression tests:** Render tiny documents and compare PDF output against known-good references
  - Requires: Graphviz, ImageMagick, and MuPDF's `mutool` or poppler's `pdftoppm`
- Tests run against multiple Python versions (3.10, 3.11, 3.12, 3.13, 3.14, 3.15) and PyPy

## Regression Test Structure

Regression tests verify that rendered PDF output matches reference PDFs. Tests are organized by input format:

```
tests_regression/
├── helpers/
│   ├── regression.py      # Core rendering and verification logic
│   ├── diffpdf.py         # PDF comparison utilities
│   ├── pdf_linkchecker.py # Link and outline verification
│   └── util.py            # Utility functions
├── reference/             # Reference PDFs for comparison
├── rst/                   # reStructuredText test sources (.rst, .rts, .rtt)
├── rst_output/            # Generated output (created during test runs)
├── sphinx/                # Sphinx test roots (test-* directories)
├── sphinx_output/         # Sphinx-generated output
├── rinoh/                 # Direct rinoh CLI test sources
├── rinoh_output/          # CLI test output
├── images/                # Test image assets
├── conftest.py            # Pytest configuration and fixtures
├── test_rst.py            # reStructuredText frontend tests
├── test_sphinx.py         # Sphinx builder tests
├── test_rinoh.py          # CLI interface tests
└── test_rstdemo.py        # Demo document tests
```

**Test file conventions:**
- `.rst` - Input reStructuredText source files
- `.rts` - Style sheet overrides (optional, same basename as .rst)
- `.rtt` - Template configuration files (optional, same basename as .rst)
- `.pdf` - Reference PDFs in `reference/` or alongside source files
- `.pxml` - PseudoXML output (generated for debugging doctree structure)
- `.stylelog` - Expected style warnings (optional)

**How regression tests work:**
1. Parse input file (reStructuredText, CommonMark, or Sphinx) into a doctree
2. Render doctree to PDF using rinohtype
3. Compare generated PDF against reference PDF using `diff_pdf()`
4. Verify PDF links, anchors, and outlines match expected values
5. Check for expected warnings in `.stylelog` files

**Adding a regression test:**
1. Create a minimal `.rst` file in `tests_regression/rst/` that demonstrates the feature/bug
2. Add optional `.rts` style sheet or `.rtt` template config if needed
3. Run the test to generate output in `tests_regression/rst_output/`
4. Inspect the generated PDF to ensure it's correct
5. Copy the generated PDF to the `rst/` directory as the new reference
6. Commit the `.rst`, reference `.pdf`, and any `.rts`/`.rtt` files

**Sphinx tests:** Use `test-*` directory structure in `tests_regression/sphinx/` with `conf.py` and `index.rst` files.

## Development Conventions

For comprehensive details on development workflows, Nox sessions, testing
across Python versions, continuous integration, and release processes, see
**[DEVELOPING.rst](DEVELOPING.rst)**.

### Coding Style
- Follow PEP 8
- 80-column line wrapping
- 4 spaces indentation (no tabs)
- Descriptive variable/function/class names
- Organize imports: standard library → external packages → rinohtype modules
- Minimize external dependencies
- Configuration in `setup.cfg` for pytest and doc8

### Testing Practices
- Use pytest for all tests
- Unit tests focus on component functionality
- Regression tests compare PDF output against reference PDFs
- Tests parameterized across multiple Python versions and dependency versions

### Python Version Management
- `.python-version` file specifies target versions for pyenv
- `pyenv_setup.py` script installs required Python versions
- Tests run across supported Python versions via CI

### Making Changes
1. Code follows existing conventions
2. Run `nox` to verify tests pass locally
3. Add regression tests for new features/bug fixes when appropriate
4. Add an entry to the changelog (`CHANGES.rst`) for significant changes
5. Update documentation if needed

## Key Files

### Configuration & Build
- `pyproject.toml` - Poetry configuration, dependencies, entry points
- `noxfile.py` - Nox session definitions
- `noxutil.py` - Nox utility functions
- `setup.cfg` - pytest and doc8 configuration
- `poetry.lock` - Locked dependency versions
- `.coveragerc` - Coverage configuration
- `pyenv_setup.py` - Python version management script
- `run_tests.py` - Test runner script

### Core Source Modules
- `src/rinoh/__init__.py` - Package initialization with version/release info
- `src/rinoh/__main__.py` - CLI entry point (`rinoh` command)
- `src/rinoh/annotation.py` - Document annotations
- `src/rinoh/attribute.py` - Attribute handling
- `src/rinoh/color.py` - Color handling
- `src/rinoh/csl_formatter.py` - CSL citation/bibliography formatting
- `src/rinoh/dimension.py` - Dimension and measurement types
- `src/rinoh/document.py` - Document model
- `src/rinoh/draw.py` - Drawing primitives
- `src/rinoh/element.py` - Document elements
- `src/rinoh/flowable.py` - Flowable page elements
- `src/rinoh/glossary.py` - Glossary generation
- `src/rinoh/highlight.py` - Syntax/code highlighting
- `src/rinoh/hyphenator.py` - Text hyphenation
- `src/rinoh/image.py` - Image handling and embedding
- `src/rinoh/index.py` - Index generation
- `src/rinoh/inline.py` - Inline text elements
- `src/rinoh/layout.py` - Page layout system
- `src/rinoh/math.py` - Math formula rendering
- `src/rinoh/number.py` - Numbering systems
- `src/rinoh/paper.py` - Paper sizes and page dimensions
- `src/rinoh/paragraph.py` - Paragraph formatting and layout
- `src/rinoh/reference.py` - Cross-references
- `src/rinoh/resource.py` - Resource management
- `src/rinoh/strings.py` - String utilities and localization
- `src/rinoh/structure.py` - Document structure
- `src/rinoh/style.py` - Style system
- `src/rinoh/styleds.py` - Styled document elements
- `src/rinoh/styles.py` - Style management
- `src/rinoh/table.py` - Table rendering
- `src/rinoh/template.py` - Document templates
- `src/rinoh/text.py` - Text rendering and formatting
- `src/rinoh/util.py` - General utility functions
- `src/rinoh/warnings.py` - Warning system

### Subpackages
- `src/rinoh/backend/` - PDF rendering backend
- `src/rinoh/data/` - Data files and resources
- `src/rinoh/font/` - Font handling
- `src/rinoh/fonts/` - Font definitions (Adobe 14, Google Fonts)
- `src/rinoh/frontend/` - Input format parsers (reStructuredText, CommonMark, Sphinx)
- `src/rinoh/language/` - Language-specific processing
- `src/rinoh/stylesheets/` - Built-in style sheets
- `src/rinoh/templates/` - Document templates (article, book)

### Documentation & CI
- `README.rst` - Project overview and quick start
- `DEVELOPING.rst` - Detailed development workflows and CI processes
- `CONTRIBUTING.rst` - Contribution guidelines
- `CHANGES.rst` - Changelog
- `LICENSE` - AGPL-3.0 license text
- `.github/` - GitHub Actions workflows

## Additional Notes

- Single maintainer; welcomes contributions
- Commercial DITA frontend available (development on hold)
- Main development on macOS, but supports Linux and Windows
- Symlinks in repository require special Windows Git configuration
- CI uses GitHub Actions across Linux, macOS, and Windows
- Use the `gh` command-line tool to query the GitHub API for issues, CI status and test results
- Regression test artifacts (PDFs, images) are available in CI for debugging test failures
