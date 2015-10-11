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

import logging

from PySide import QtCore, QtNetwork
from PySide.QtSql import *

from . import tournament_server_thread
import challonge


class TournamentServer(QtNetwork.QTcpServer):
    def __init__(self, db):
        self.logger = logging.getLogger(__name__)
        self.threads = []
        self.updaters = []
        self.db = db
        self.update_timer = QtCore.QTimer()
        self.tournaments = {}

    def start(self):
        self.import_tournaments()
        self.start_update_timer()

        return self

    def start_update_timer(self):
        self.update_timer.start(60000 * 5)
        self.update_timer.timeout.connect(self.import_tournaments)

    def import_tournaments(self):
        self.tournaments = {}
        for t in challonge.tournaments.index():
            uid = t["id"]
            self.tournaments[uid] = {
                "name": t["name"],
                "url": t["full-challonge-url"],
                "description": t["description"],
                "type": t["tournament-type"],
                "progress": t["progress-meter"],
                "state": "open"
            }
            check_participants = False

            if t["started-at"] is not None:
                self.tournaments[uid]["state"] = "started"
                if t["progress-meter"] == 0:
                    check_participants = True
            if t["completed-at"] is not None:
                self.tournaments[uid]["state"] = "finished"

            if t["open_signup"] is not None:
                challonge.tournaments.update(uid, open_signup="false")

            self.tournaments[uid]["participants"] = []

            for p in challonge.participants.index(uid):
                found = self.lookup_user(p["name"])

                if check_participants and not (found and found['logged_in']):
                    challonge.participants.destroy(uid, p["id"])
                else:
                    if found and found['renamed']:
                        self.logger.debug("player is replaced by %s", found['name'])
                        challonge.participants.update(uid, p["id"], name=found['name'])

                    self.tournaments[uid]["participants"].append({
                        "id": p["id"],
                        "name": found['name'] if found else p['name']
                    })

                # if self.tournaments[uid]["state"] == "started":
                #     for conn in self.updaters:
                #         conn.sendJSON(dict(command="tournaments_info", data=self.tournaments))

    def in_tournament(self, name, tournament_id):
        return any(p['name'] == name for p in self.tournaments[tournament_id]['participants'])

    def lookup_user(self, name):
        fafuid = self.lookup_id_from_login(name)
        real_name = name

        if not fafuid:
            fafuid = self.lookup_id_from_history(name)

            if not fafuid:
                return None

            real_name = self.lookup_name_by_id(fafuid)

        return {
            'name': str(real_name),
            'id': fafuid,
            'logged_in': self.is_logged_in(fafuid),
            'renamed': real_name != name
        }

    def lookup_id_from_login(self, name):
        query = QSqlQuery(self.db)
        query.prepare("SELECT id FROM login WHERE login = ?")
        query.addBindValue(name)
        if query.exec_():
            if query.size() == 1:
                query.first()
                return int(query.value(0))

    def lookup_id_from_history(self, name):
        query = QSqlQuery(self.db)
        query.prepare("SELECT user_id FROM name_history WHERE previous_name LIKE ?")
        query.addBindValue(name)
        if query.exec_():
            if query.size() == 1:
                query.first()
                return int(query.value(0))

    def lookup_name_by_id(self, fafuid):
        query = QSqlQuery(self.db)
        query.prepare("SELECT login FROM login WHERE id =  ?")
        query.addBindValue(fafuid)
        if query.exec_():
            if query.size() == 1:
                query.first()
                return query.value(0)

    def is_logged_in(self, fafuid):
        query = QSqlQuery(self.db)
        query.prepare("SELECT session FROM login WHERE id = ?")
        query.addBindValue(fafuid)
        if query.exec_():
            if query.size() == 1:
                query.first()
                return int(query.value(0)) != 0
        return False

    def incomingConnection(self, socket_id):

        reload(tournament_server_thread)
        # self.logger.debug("Incoming tourney Connection")
        self.updaters.append(tournament_server_thread.TournamentServerThread(socket_id, self))

    def remove_updater(self, updater):
        if updater in self.updaters:
            self.updaters.remove(updater)
            updater.deleteLater()
