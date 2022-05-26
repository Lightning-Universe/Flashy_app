<div align="center">

<img src="https://grid-hackthon.s3.amazonaws.com/flashy/logo.png" width="100%">

**The AutoML App**

</div>

## Running the app

Let's first start with setting up the environment, and installing the requirements:

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
# Because of the conflicts with dependencies and to support the app on cloud
# currently, it's required that fiftyone is installed manually locally.
# For cloud, the app will install it for you! :)
pip install fiftyone
pip install -e .
```

In order to run the app now (locally):

```bash
lightning run app app.py
```

And to run on the cloud:

```bash
lightning run app app.py --cloud
```
