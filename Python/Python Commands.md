To create a virtual environment:
python3 -m venv venv

To activate the virtual environment:
source venv/bin/activate

Install packages:
pip install <package_name>
pip install jupyter ipykernel

Add kernel to Jupyter (CRITICAL for notebooks):
python -m ipykernel install --user --name=venv --display-name "Python (venv)"

To use the environment on a new machine:

1. Create and activate venv (see above)
2. Install everything from the list:
   pip install -r requirements.txt

To save your current package list:
pip freeze > requirements.txt

To deactivate the virtual environment:
deactivate

---
