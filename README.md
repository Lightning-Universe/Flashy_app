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
pip install -r requirements.txt
pip install fiftyone
pip install -e .

lightning run app app.py
```
