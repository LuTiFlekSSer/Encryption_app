import msvcrt
import os
from io import IOBase
from typing import Optional

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtNetwork import QLocalServer, QLocalSocket

from src.backend.db.db_records import OperationType
from src.utils.config import Config


class InstanceLock:
    def __init__(self, lockfile: str):
        self.lockfile: str = lockfile
        self.fp: Optional[IOBase] = None

    def acquire(self) -> bool:
        try:
            self.fp = open(self.lockfile, 'w')
            msvcrt.locking(self.fp.fileno(), msvcrt.LK_NBLCK, 1)

            return True
        except OSError:
            if self.fp:
                self.fp.close()

            self.fp = None

            return False

    def release(self):
        if self.fp:
            try:
                msvcrt.locking(self.fp.fileno(), msvcrt.LK_UNLCK, 1)
            except Exception:
                pass

            try:
                self.fp.close()
            except Exception:
                pass

            try:
                os.remove(self.lockfile)
            except Exception:
                pass

            self.fp = None


class InstanceManager(QObject):
    sig_external_command = pyqtSignal(OperationType, str)

    def __init__(self):
        super().__init__()
        self._server_name: str = Config.APP_NAME
        self._server: QLocalServer = QLocalServer()
        self._server.newConnection.connect(self._on_new_connection)
        self._lockfile_path: str = os.path.join(
            os.path.expanduser('~'),
            f'.{self._server_name.lower()}_single_instance.lock'
        )
        self._lock: InstanceLock = InstanceLock(self._lockfile_path)
        self.is_primary_instance: bool = False

    def try_acquire_lock(self) -> bool:
        self.is_primary_instance = self._lock.acquire()
        return self.is_primary_instance

    def release_lock(self):
        self._lock.release()

    def is_running(self) -> bool:
        socket= QLocalSocket()
        socket.connectToServer(self._server_name)

        connected = socket.waitForConnected(200)
        socket.disconnectFromServer()

        return connected

    def send(self, action: str, path: str) -> bool:
        socket = QLocalSocket()
        socket.connectToServer(self._server_name)

        if not socket.waitForConnected(500):
            return False

        msg = f'{action}|{path}'
        socket.write(msg.encode('utf-8'))
        socket.flush()

        socket.waitForBytesWritten(1000)
        socket.disconnectFromServer()

        return True

    def start_server(self):
        QLocalServer.removeServer(self._server_name)
        self._server.listen(self._server_name)

    def _on_new_connection(self):
        client = self._server.nextPendingConnection()

        if client:
            client.readyRead.connect(lambda: self._on_client_ready_read(client))

    def _on_client_ready_read(self, client: QLocalSocket):
        msg = bytes(client.readAll()).decode('utf-8')
        parts = msg.strip().split('|', 1)

        if len(parts) == 2:
            action, path = parts

            if action == 'encrypt':
                self.sig_external_command.emit(OperationType.ENCRYPT, path)
            elif action == 'decrypt':
                self.sig_external_command.emit(OperationType.DECRYPT, path)

        client.disconnectFromServer()
