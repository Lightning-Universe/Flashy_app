if [ -z $(ls | grep "setup.py") ]; then
    echo "no setup.py"
else
    python -m pip install -e .
fi