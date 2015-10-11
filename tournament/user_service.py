from PySide.QtSql import *


class UserService:

    def __init__(self, db):
        self.db = db
        db.Open()

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
