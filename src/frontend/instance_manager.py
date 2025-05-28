from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtNetwork import QLocalServer, QLocalSocket

from src.backend.db.db_records import OperationType
from src.utils.config import Config


class InstanceManager(QObject):
    sig_external_command: pyqtSignal = pyqtSignal(OperationType, str)

    def __init__(self):
        super().__init__()
        self._server_name: str = Config.APP_NAME
        self._server: QLocalServer = QLocalServer()
        self._server.newConnection.connect(self._on_new_connection)

    def is_running(self) -> bool:
        socket = QLocalSocket()
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

        if client and client.waitForReadyRead(1000):
            msg = bytes(client.readAll()).decode('utf-8')
            parts = msg.strip().split('|', 1)

            if len(parts) == 2:
                action, path = parts
                self.sig_external_command.emit(OperationType.ENCRYPT if action == 'encrypt' else OperationType.DECRYPT,
                                               path)

        client.disconnectFromServer()
