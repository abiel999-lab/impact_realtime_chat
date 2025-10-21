import os
import sys
import threading
import mimetypes
from pathlib import Path
import requests
import socketio
from PySide6 import QtCore, QtGui, QtWidgets
from client_config import API_BASE, SOCKET_URL


class Api:
    def __init__(self):
        self.base = API_BASE.rstrip("/")
        self.token = None

    def _auth(self):
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    def register(self, email, password, name, gender="unspecified"):
        r = requests.post(
            f"{self.base}/auth/register",
            json={"email": email, "password": password, "name": name, "gender": gender},
        )
        r.raise_for_status()
        self.token = r.json()["token"]
        return r.json()

    def login(self, email, password):
        r = requests.post(
            f"{self.base}/auth/login",
            json={"email": email, "password": password},
        )
        r.raise_for_status()
        self.token = r.json()["token"]
        return r.json()

    def countries(self):
        r = requests.get(f"{self.base}/rooms/countries")
        r.raise_for_status()
        return r.json()

    def rooms(self, code):
        r = requests.get(f"{self.base}/rooms", params={"code": code})
        r.raise_for_status()
        return r.json()

    def create_room(self, code, name):
        r = requests.post(
            f"{self.base}/rooms/create",
            params={"code": code, "name": name},
            headers=self._auth(),
        )
        if r.status_code >= 400:
            raise requests.HTTPError(r.json().get("detail"))
        return r.json()

    def list_messages(self, room_id, limit=50):
        r = requests.get(
            f"{self.base}/chat/messages",
            params={"room_id": room_id, "limit": limit},
        )
        r.raise_for_status()
        return r.json()

    def list_attachments(self, room_id, limit=50):
        r = requests.get(
            f"{self.base}/chat/attachments",
            params={"room_id": room_id, "limit": limit},
        )
        r.raise_for_status()
        return r.json()

    def send_message(self, room_id, text):
        r = requests.post(
            f"{self.base}/chat/message",
            data={"room_id": room_id, "text": text},
            headers=self._auth(),
        )
        if r.status_code >= 400:
            raise requests.HTTPError(r.text)
        return r.json()

    def upload_files(self, room_id, paths):
        files = [
            (
                "files",
                (
                    Path(p).name,
                    open(p, "rb"),
                    mimetypes.guess_type(p)[0] or "application/octet-stream",
                ),
            )
            for p in paths
        ]
        try:
            r = requests.post(
                f"{self.base}/chat/upload",
                headers=self._auth(),
                files=files,
                data={"room_id": room_id},
            )
        finally:
            for _, f in files:
                f[1].close()

        if r.status_code >= 400:
            raise requests.HTTPError(r.text)
        return r.json()


class LoginDialog(QtWidgets.QDialog):
    def __init__(self, api: Api):
        super().__init__()
        self.api = api
        self.setWindowTitle("Impact Chat — Login / Register")
        self.resize(420, 210)

        self.e = QtWidgets.QLineEdit()
        self.e.setPlaceholderText("email")

        self.p = QtWidgets.QLineEdit()
        self.p.setPlaceholderText("password")
        self.p.setEchoMode(QtWidgets.QLineEdit.Password)

        self.n = QtWidgets.QLineEdit()
        self.n.setPlaceholderText("name (for register)")

        self.g = QtWidgets.QComboBox()
        self.g.addItems(["unspecified", "male", "female"])
        self.s = QtWidgets.QLabel()

        bL = QtWidgets.QPushButton("Login")
        bR = QtWidgets.QPushButton("Register")
        bL.clicked.connect(self.login)
        bR.clicked.connect(self.register)

        f = QtWidgets.QFormLayout()
        f.addRow("Email", self.e)
        f.addRow("Password", self.p)
        f.addRow("Name", self.n)
        f.addRow("Gender", self.g)

        v = QtWidgets.QVBoxLayout(self)
        v.addLayout(f)

        h = QtWidgets.QHBoxLayout()
        h.addWidget(bL)
        h.addWidget(bR)
        v.addLayout(h)
        v.addWidget(self.s)

    def login(self):
        try:
            d = self.api.login(self.e.text().strip(), self.p.text())
            self.username = d["user"]["name"]
            self.accept()
        except Exception as ex:
            self.s.setText(f"Login failed: {ex}")

    def register(self):
        try:
            d = self.api.register(
                self.e.text().strip(),
                self.p.text(),
                self.n.text().strip(),
                self.g.currentText(),
            )
            self.username = d["user"]["name"]
            self.accept()
        except Exception as ex:
            self.s.setText(f"Register failed: {ex}")


class JoinDialog(QtWidgets.QDialog):
    def __init__(self, api: Api):
        super().__init__()
        self.api = api
        self.setWindowTitle("Join Room")
        self.resize(420, 210)

        self.c = QtWidgets.QComboBox()
        self.r = QtWidgets.QComboBox()
        self.new = QtWidgets.QLineEdit()
        self.new.setPlaceholderText("or create new room name")
        self.s = QtWidgets.QLabel()

        bC = QtWidgets.QPushButton("Create Room")
        bJ = QtWidgets.QPushButton("Join")
        bC.clicked.connect(self.create)
        bJ.clicked.connect(self.accept)

        f = QtWidgets.QFormLayout()
        f.addRow("Country", self.c)
        f.addRow("Room", self.r)
        f.addRow("New", self.new)

        v = QtWidgets.QVBoxLayout(self)
        v.addLayout(f)

        h = QtWidgets.QHBoxLayout()
        h.addWidget(bC)
        h.addWidget(bJ)
        v.addLayout(h)
        v.addWidget(self.s)

        self.c.currentIndexChanged.connect(self.refresh)
        self.load()


app = App(sys.argv)
sys.exit(app.run())
