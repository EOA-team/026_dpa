# Unit Tests
python -m pytest
python -m pytest tests/test_pywinauto_helpers_new.py -s
python -m pytest tests/test_pywinauto_helpers.py::test_set_checkbox

# Code Style with Ruff 
ruff check          # Show linting errors (lint + complexity + security)
ruff check --diff   # Preview what --fix would change
ruff check --fix    # Auto-fix what it can

ruff format         # Auto-format
ruff format --check # Check formatting, show what would change
ruff format --diff  # Preview formatting diff
# Static Type Checking 
mypy code 
mypy code/pywinauto_helpers_new.py

# Run a script
python -m code.scripts.automate_hyspexrad

# Autopep 8
autopep8 --in-place code/myfile.py 