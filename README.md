<div align="center">

<img src="https://grid-hackthon.s3.amazonaws.com/flashy/logo.png" width="400px">

**The AutoML App**

</div>

## Running the app

To run the app, execute the following commands:
```bash
conda create --name automl python=3.8
conda activate automl
git clone https://github.com/PyTorchLightning/automl_app
cd automl_app
pip install -r requirements.txt
pip install -e .

lightning start app flashy/app.py
```
