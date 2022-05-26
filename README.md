<div align="center">

<img src="https://grid-hackthon.s3.amazonaws.com/flashy/logo.png" width="100%">

**The AutoML App**

</div>

## Running the app

To run the app, execute the following commands:

```bash
conda create --name lightning python=3.8
conda activate lightning

git clone https://github.com/PyTorchLightning/lightning
cd lightning
pip install -r requirements.txt
pip install -e .
python scripts/download_frontend.py

cd ../
git clone https://github.com/PyTorchLightning/lightning-auto-ml
cd lightning-auto-ml
pip install -r requirements-dev.txt
pip install -e .

lightning run app app.py
```

In case you receive a `ModuleNotFound` error for `fiftyone`, please consider installing the library manually as shown in the script above, or just use the `requirements-dev.txt` file during installation as shown in the script above.
