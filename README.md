<div align="center">

<img src="https://grid-hackthon.s3.amazonaws.com/flashy/logo.png" width="100%">

**The AutoML App**

</div>

## Running the app

Let's first start with setting up the environment, and installing the requirements:

```bash
conda create --name lightning python=3.8
conda activate lightning

git clone https://github.com/Lightning-AI/lightning
cd lightning
pip install -r requirements.txt
pip install -e .
python scripts/download_frontend.py

cd ../
git clone https://github.com/Lightning-AI/LAI-Flashy-App
cd LAI-Flashy-App
# For local install, we keep a separate requirements file. The cloud app uses requirements.txt file.
pip install -r requirements-dev.txt
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

In case you receive a `ModuleNotFound` error for `fiftyone`, please consider installing the library manually as shown in the script above, or just use the `requirements-dev.txt` file during installation as shown in the script above.
