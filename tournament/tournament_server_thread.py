# -------------------------------------------------------------------------------
# Copyright (c) 2014 Gael Honorez.
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the GNU Public License v3.0
# which accompanies this distribution, and is available at
# http://www.gnu.org/licenses/gpl.html
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# -------------------------------------------------------------------------------


import operator
import logging
import json

from PySide.QtCore import QObject
from PySide.QtCore import QByteArray, QDataStream, QIODevice, QFile, QCoreApplication
from PySide import QtCore, QtNetwork
from PySide.QtSql import *

import challonge


class TournamentServerThread(QObject):
    """
    FA server thread spawned upon every incoming connection to
    prevent collisions.
    """

    def __init__(self, socket_id, parent=None):
        super(TournamentServerThread, self).__init__(parent)

        self.log = logging.getLogger(__name__)

        self.app = None

        self.socket = QtNetwork.QTcpSocket(self)
        self.socket.setSocketDescriptor(socket_id)
        self.parent = parent

        if self.socket.state() == 3 and self.socket.isValid():
            self.nextBlockSize = 0

            self.blockSize = 0

            self.socket.readyRead.connect(self.readDatas)
            self.socket.disconnected.connect(self.disconnection)

            self.parent.db.open()
            self.pingTimer = QtCore.QTimer(self)
            self.pingTimer.start(31000)
            self.pingTimer.timeout.connect(self.ping)

    def ping(self):
        self.sendJSON(dict(command="ping"))

    def command_pong(self, message):
        return

    def command_add_participant(self, message):
        uid = message["uid"]
        login = message["login"]

        self.parent.add_participant(login, uid)

        self.log.debug("sending ata")
        self.sendJSON(dict(command="tournaments_info", data=self.parent.tournaments))

    def command_remove_participant(self, message):
        uid = message["uid"]
        login = message["login"]

        self.parent.remove_participant(login, uid)
        self.sendJSON(dict(command="tournaments_info", data=self.parent.tournaments))
        # for conn in self.parent.updaters:
        #     conn.sendJSON(dict(command="tournaments_info", data=self.parent.tournaments))

    def command_get_tournaments(self, message):
        self.sendJSON(dict(command="tournaments_info", data=self.parent.tournaments))

    def handleAction(self, action, stream):
        self.receiveJSON(action, stream)
        return 1

    def readDatas(self):
        if self.socket is not None:
            if self.socket.isValid():
                ins = QDataStream(self.socket)
                ins.setVersion(QDataStream.Qt_4_2)
                loop = 0
                while not ins.atEnd():
                    QCoreApplication.processEvents()
                    loop += 1
                    if self.socket is not None:
                        if self.socket.isValid():
                            if self.blockSize == 0:
                                if self.socket.isValid():
                                    if self.socket.bytesAvailable() < 4:
                                        return
                                    self.blockSize = ins.readUInt32()
                                else:
                                    return
                            if not self.socket.isValid():
                                return
                            action = ins.readQString()
                            self.handleAction(action, ins)
                            self.blockSize = 0
                        else:
                            return
                    else:
                        return
                return

    def disconnection(self):
        self.done()

    def sendJSON(self, data_dictionary):
        """
        Simply dumps a dictionary into a string and feeds it into the QTCPSocket
        """
        try:
            data_string = json.dumps(data_dictionary)
            self.sendReply(data_string)
        except:
            self.log.warning("wrong data")
            self.socket.abort()
            return

    def receiveJSON(self, data_string, stream):
        """
        A fairly pythonic way to process received strings as JSON messages.
        """
        try:
            message = json.loads(data_string)

            cmd = "command_" + message['command']
            if hasattr(self, cmd):
                getattr(self, cmd)(message)
        except:
            self.log.warning("command error")
            self.socket.abort()
            return

    def sendReply(self, action, *args, **kwargs):
        try:
            if hasattr(self, "socket"):
                reply = QByteArray()
                stream = QDataStream(reply, QIODevice.WriteOnly)
                stream.setVersion(QDataStream.Qt_4_2)
                stream.writeUInt32(0)

                stream.writeQString(action)

                for arg in args:
                    if type(arg) is LongType:
                        stream.writeQString(str(arg))
                    if type(arg) is IntType:
                        stream.writeInt(int(arg))
                    elif type(arg) is StringType:
                        stream.writeQString(arg)
                    elif isinstance(arg, str):
                        stream.writeQString(arg)
                    elif type(arg) is FloatType:
                        stream.writeFloat(arg)
                    elif type(arg) is ListType:
                        stream.writeQString(str(arg))
                    elif type(arg) is QFile:
                        arg.open(QIODevice.ReadOnly)
                        fileDatas = QByteArray(arg.readAll())
                        stream.writeInt32(fileDatas.size())
                        stream.writeRawData(fileDatas.data())
                        arg.close()
                        # stream << action << options
                stream.device().seek(0)

                stream.writeUInt32(reply.size() - 4)
                if self.socket:
                    self.socket.write(reply)


        except:
            self.log.exception("Something awful happened when sending reply !")

    def done(self):
        self.parent.remove_updater(self)
        if self.socket:
            self.socket.deleteLater()
