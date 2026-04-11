# rinohtype - Project Context

## Overview

**rinohtype** is a Python-based batch-mode document processor that renders structured documents to PDF based on document templates and style sheets.

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
    ├── templates/      # Built-in document templates (article, book)
    ├── data/           # Data files and resources
    └── [core modules]  # document.py, layout.py, paragraph.py, table.py, etc.

doc/                    # Documentation source
tests/                  # Unit tests
tests_regression/       # Regression/integration tests
examples/               # Example documents
```

## Development Workflow

- All development work makes use of a virtual environment in .venv/
  - If the .venv/ directory doesn't exist, run `poetry install -E math` to create it and install dependencies
  - Activate the virtual environment with `source .venv/bin/activate`
- Run tests using `pytest` in this dev environment
  - Unit tests in `tests/`; these cover only a small portion of the codebase
  - Regression tests in `tests_regression/`
- Do NOT run the nox sessions; these are for CI only
- Add an entry to the changelog (`CHANGES.rst`) for significant changes
- Update documentation if needed

### Testing Details

- **Unit tests:** Quick tests focusing on individual components
  - Unit test coverage is very limited; you should mainly use regression tests to verify that changes don't break existing functionality
- **Regression tests:** Render tiny documents and compare PDF output against known-good references
  - `test_rst.py` tests the reStructuredText frontend
    - Each .rst file in `tests_regression/rst/` makes for a separate test case
    - Optional .rts style sheet and .rtt template config files can be added with the same basename as the .rst file
    - Reference PDFs are stored alongside the .rst files (same basename)
    - When a test is run, the generated PDF is saved in `rst_output/` and compared against the reference
  - `test_sphinx.py` tests the Sphinx builder
    - Each `test-*` directory in `tests_regression/sphinx/` makes for a separate test case; these directories contain a minimal Sphinx project with `conf.py` and `index.rst`
    - Reference PDFs (`<name>.pdf`) are stored alongside the `test-<name>` directories
    - When a test is run, the generated PDF is saved in `sphinx_output/` and compared against the reference
  - `test_rinoh.py` tests the CLI interface (you can ignore these for most development work)

If the PDF output differs from the reference, diff images for each page are written to a `pdfdiff/` directory next to the generated PDF. Matching content will be black, while differences will be highlighted in green (reference) and red (generated). Inspect the diff images to understand what changed and whether it's an expected change (e.g. due to a bug fix or new feature) or an unexpected change (e.g. due to a regression). If the change is expected, copy the generated PDF to the reference location to update the reference for future tests. This should always be verified by the user!

If a regression test times out, the rendering process may be stuck in an infinite loop. In that case, kill the process. No PDF output will be generated in this case.

After making code changes, run the integration tests to verify that the changes work as expected and don't break existing functionality. Invoke `pytest` with the `--exitfirst` option to abort on the first failure, which speeds up the feedback loop. Regression tests can be slow to run, so when fixing a bug, run only the failing regression test while debugging. Once the bug is fixed, run the full regression test suite to ensure there are no unintended changes in PDF output.

In addition to the PDF output, you can inspect the generated PseudoXML output (saved in `*.pxml` files) to ensure the doctree structure is what you expect. You can also check the generated style log (saved in `*.stylelog` files) to verify that the styles are being applied correctly.

### Bugfixing

When fixing a bug, first write a regression test that demonstrates the bug if it does not already exist. This ensures that the bug is properly captured and prevents future changes from reintroducing it. To write a regression test for a bug, create a minimal `.rst` file (or Sphinx project) that reproduces the issue, run the test to generate the output PDF, inspect it to confirm the bug is present. Then fix the bug in the code, run the test again to verify that the output PDF is now correct, and copy it to the reference location.

### New Features

When adding new features, first implement the feature and verify it works as expected. Then add a regression test that demonstrates the new feature. This ensures that the feature is properly tested and prevents future changes from breaking it. When adding a regression test, create a minimal `.rst` file (or Sphinx project) that demonstrates the feature, run the test to generate the output PDF, inspect it to ensure it's correct, and then copy it to the reference location.

## GitHub

- Use the `gh` command-line tool to query the GitHub API for issues, CI status and test results
- Regression test artifacts (PDFs, images) are available in CI for debugging test failures

## Coding Style

- Follow existing conventions (PEP 8)
- 80-column line wrapping
- 4 spaces indentation (no tabs)
- Descriptive variable/function/class names
- Organize imports: standard library → external packages → rinohtype modules
- Minimize external dependencies

## Key Files

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
