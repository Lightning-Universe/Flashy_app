import json
import os
import tarfile
import traceback
import uuid
import zipfile
from dataclasses import dataclass
from functools import wraps
from typing import Dict, List, Optional, Tuple, Union

import lightning as L
import requests
from lightning.app.storage import Drive


@dataclass
class FileServerBuildConfig(L.BuildConfig):
    def build_commands(self) -> List[str]:
        return ["python -m pip install Flask==2.1.2 Flask-Cors==3.0.10 python-magic==0.4.27"]


def handle_error(fn):
    @wraps(fn)
    def inner(*args, **kwargs):
        from flask import abort, make_response
        from werkzeug.exceptions import HTTPException

        try:
            return fn(*args, **kwargs)
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            else:
                abort(make_response(({"error": repr(e), "traceback": traceback.format_exc()}, 500)))

    return inner


class FileServer(L.LightningWork):
    def __init__(self, drive: Drive, base_dir: str = ".", chunk_size=10240, **kwargs):
        super().__init__(cloud_build_config=FileServerBuildConfig(), **kwargs)

        self.drive = drive
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

        self.chunk_size = chunk_size

        self.uploaded_files: Dict[str, Dict[str, Union[Tuple[int, int], bool]]] = dict()

        self.ready = False

    def get_filepath(self, path: str) -> str:
        return os.path.join(self.base_dir, path)

    def get_random_filename(self) -> str:
        return uuid.uuid4().hex

    @handle_error
    def upload_url(self, url):
        import magic

        original_file = url.split("/")[-1]
        uploaded_file = self.get_random_filename()
        meta_file = uploaded_file + ".meta"

        with requests.get(url, stream=True, verify=False) as r:
            full_size = r.headers["content-length"]
            self.uploaded_files[original_file] = {
                "progress": (0, full_size),
                "done": False,
            }
            with open(self.get_filepath(uploaded_file), "wb") as out_file:
                for chunk in r.iter_content(chunk_size=self.chunk_size):
                    written_size = out_file.write(chunk)
                    self.uploaded_files[original_file]["progress"] = (
                        self.uploaded_files[original_file]["progress"][0] + written_size,
                        full_size,
                    )

        self.drive.put(self.get_filepath(uploaded_file))
        self.uploaded_files[original_file] = {
            "progress": (full_size, full_size),
            "done": True,
        }

        meta = {
            "original_path": original_file,
            "display_name": os.path.splitext(original_file)[0],
            "size": full_size,
            "mime_type": magic.from_file(self.get_filepath(uploaded_file), mime=True),
            "drive_path": uploaded_file,
        }
        with open(self.get_filepath(meta_file), "w") as f:
            json.dump(meta, f)

        self.drive.put(self.get_filepath(meta_file))

        return meta

    @handle_error
    def upload_file(self, file):
        import magic

        original_file = file.filename
        uploaded_file = self.get_random_filename()
        meta_file = uploaded_file + ".meta"

        self.uploaded_files[original_file] = {"progress": (0, None), "done": False}

        with open(self.get_filepath(uploaded_file), "wb") as out_file:
            content = file.read(self.chunk_size)
            while content:
                written_size = out_file.write(content)
                self.uploaded_files[original_file]["progress"] = (
                    self.uploaded_files[original_file]["progress"][0] + written_size,
                    None,
                )
                content = file.read(self.chunk_size)

        full_size = self.uploaded_files[original_file]["progress"][0]
        self.drive.put(self.get_filepath(uploaded_file))
        self.uploaded_files[original_file] = {
            "progress": (full_size, full_size),
            "done": True,
        }

        meta = {
            "original_path": original_file,
            "display_name": os.path.splitext(original_file)[0],
            "size": full_size,
            "mime_type": magic.from_file(self.get_filepath(uploaded_file), mime=True),
            "drive_path": uploaded_file,
        }
        with open(self.get_filepath(meta_file), "w") as f:
            json.dump(meta, f)

        self.drive.put(self.get_filepath(meta_file))

        return meta

    def get_file_by_path_local(self, file_path):
        from flask import send_file

        if not os.path.exists(file_path):
            return None

        return send_file(os.path.abspath(file_path))

    def get_file_by_path_drive(self, file_path):
        from flask import send_file

        dir_path = os.path.dirname(os.path.join(".", file_path))
        if file_path not in self.drive.list(dir_path):
            return None

        if not os.path.exists(file_path):
            self.drive.get(file_path)

        return send_file(os.path.abspath(file_path))

    def get_file_by_id(self, file_id):
        from flask import send_file

        file_path = self.get_filepath(file_id)
        meta_path = self.get_filepath(file_id + ".meta")

        drive_files = self.drive.list(self.base_dir)

        if file_path not in drive_files or meta_path not in drive_files:
            return None

        if not os.path.exists(file_path):
            self.drive.get(file_path)
        if not os.path.exists(meta_path):
            self.drive.get(meta_path)

        with open(meta_path) as f:
            meta = json.load(f)

        return send_file(
            os.path.abspath(file_path),
            mimetype=meta["mime_type"],
            download_name=meta["original_path"],
            attachment_filename=meta["original_path"],
        )

    @handle_error
    def get_file(self, file_id_or_path):
        from flask import abort, make_response

        methods = [
            self.get_file_by_id,
            self.get_file_by_path_local,
            self.get_file_by_path_drive,
        ]
        result = None

        for method in methods:
            result = method(file_id_or_path)
            if result is not None:
                return result

        if result is None:
            abort(
                make_response(
                    {"error": f"The file with identifier {file_id_or_path} could not be found!"},
                    404,
                )
            )

    @handle_error
    def get_asset_names(
        self,
        file_id: str,
        ext: Optional[str] = None,
    ):
        file_path = self.get_filepath(file_id)

        if not os.path.exists(file_path):
            self.drive.get(file_path)

        if zipfile.is_zipfile(file_path):
            with zipfile.ZipFile(file_path, "r") as zf:
                result = zf.namelist()
        elif tarfile.is_tarfile(file_path):
            with tarfile.TarFile(file_path, "r") as tf:
                result = tf.getnames()
        else:
            raise ValueError("Cannot open archive file!")

        if ext is not None:
            ext = ext.lower()
            ext = ext[1:] if ext.startswith(".") else ext
            result = [filename for filename in result if os.path.splitext(filename)[1].lower()[1:] == ext]

        return {"asset_names": result}

    @handle_error
    def get_subdirs(
        self,
        file_id: str,
    ):
        result = {os.path.dirname(file) for file in self.get_asset_names(file_id)["asset_names"]}
        return {"asset_names": list(result)}

    def run(self):
        from flask import Flask, request
        from flask_cors import CORS

        app = Flask(__name__)
        CORS(app)

        @app.post("/uploadurl/")
        def upload_url():
            """Upload data from a URL."""
            url = request.form["url"]
            return self.upload_url(url)

        @app.post("/uploadfile/")
        def upload_file():
            """Upload a file directly as form data."""
            f = request.files["file"]
            return self.upload_file(f)

        @app.get("/listarchive/<path>/")
        @app.get("/listarchive/<path>/<ext>/")
        def get_listarchive(path: str, ext: Optional[str] = None):
            """Get a list of files contained in a zip file or the file itself if it is not."""
            return self.get_asset_names(path, ext)

        @app.get("/listsubdirs/<path>/")
        def get_listsubdirs(path: str):
            """Get a list of subdirectories contained in a zip file."""
            return self.get_subdirs(path)

        @app.get("/file/<path:file_id>")
        def get_file(file_id: str):
            return self.get_file(file_id)

        self.ready = True
        app.run(host=self.host, port=self.port, load_dotenv=False)
