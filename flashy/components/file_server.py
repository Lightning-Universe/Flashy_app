import os
import zipfile
from dataclasses import dataclass
from typing import Union

import requests
from lightning import BuildConfig, LightningWork
from lightning.storage import Path


@dataclass
class FileServerBuildConfig(BuildConfig):

    requirements = ["requirements.txt", "aiofiles", "fastapi", "uvicorn"]


class FileServer(LightningWork):
    def __init__(self, root: Union[str, Path], **kwargs):
        super().__init__(cloud_build_config=FileServerBuildConfig(), **kwargs)

        self.root = root if isinstance(root, Path) else Path(root)

        os.makedirs(str(self.root), exist_ok=True)

    def unzip(self, filename):
        if os.path.exists(filename):  # TODO: Error if not exists
            with zipfile.ZipFile(filename, "r") as zip_ref:
                zip_ref.extractall(self.root)
        return filename.replace(".zip", "")

    async def upload_url(self, url):
        filename = url.split("/")[-1]
        uploaded_file = os.path.join(self.root, filename)

        r = requests.get(url, stream=True, verify=False)

        with open(uploaded_file, "wb") as out_file:
            for chunk in r.iter_content(chunk_size=1024):
                out_file.write(chunk)

        return {"path": os.path.basename(self.unzip(uploaded_file))}

    async def upload_zip(self, file):
        import aiofiles

        uploaded_file = os.path.join(self.root, file.filename)

        async with aiofiles.open(uploaded_file, "wb") as out_file:
            content = await file.read(1024)
            while content:
                await out_file.write(content)
                content = await file.read(1024)

        return {"path": os.path.basename(self.unzip(uploaded_file))}

    def run(self):
        import uvicorn
        from fastapi import FastAPI, UploadFile
        from fastapi.middleware.cors import CORSMiddleware
        from fastapi.responses import FileResponse
        from pydantic import BaseModel

        app = FastAPI()

        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        )

        class Data(BaseModel):
            url: str

        @app.post("/uploadurl/")
        async def upload_url(data: Data):
            """Upload data from a URL."""
            return await self.upload_url(data.url)

        @app.post("/uploadzip/")
        async def upload_zip(file: UploadFile):
            """Upload a zip file directly as form data."""
            return await self.upload_zip(file)

        @app.get("/listdirs/{path}")
        async def get_listdirs(path: str):
            all_dirs = []

            for root, dirs, _ in os.walk(os.path.join(self.root, path)):
                root = root[len(str(self.root)) + 1 :]  # noqa: E203
                all_dirs.extend([os.path.join(root, dir) for dir in dirs])

            return all_dirs

        @app.get("/listfiles/{path}")
        async def get_listfiles(path: str):
            all_files = []

            for root, _, files in os.walk(os.path.join(self.root, path)):
                root = root[len(str(self.root)) + 1 :]  # noqa: E203
                all_files.extend([os.path.join(root, file) for file in files])

            return all_files

        @app.get("/files/{filename}")
        async def get_file(filename: str):
            return FileResponse(os.path.join(self.root, filename))

        uvicorn.run(app, host=self.host, port=self.port)
