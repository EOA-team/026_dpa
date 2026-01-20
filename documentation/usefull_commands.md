# Unit Tests
python -m pytest
python -m pytest tests/test_pywinauto_helpers_new.py -s
python -m pytest tests/test_pywinauto_helpers.py::test_set_checkbox

# Code Style
pylint code
pylint code/pywinauto_helpers_new.py 
# Static Type Checking 
mypy code 
mypy code/pywinauto_helpers_new.py

# Run a script
python -m code.scripts.automate_hyspexrad

# Autopep 8
autopep8 --in-place code/myfile.py 