class Tournament:
    def __init__(self, name, url, description, type, progress, state):
        self.name = name
        self.url = url
        self.description = description
        self.type = type
        self.progress = progress
        self.state = state

    def serialize(self):
        return {
            'name': self.name,
            'url': self.url,
            'description': self.description,
            'type': self.type,
            'state': self.state,
            'participants': []
        }

    @classmethod
    def from_challonge(cls, challonge_tournament):

        return Tournament(
            challonge_tournament['name'],
            challonge_tournament['full-challonge-url'],
            challonge_tournament['description'],
            challonge_tournament['tournament-type'],
            challonge_tournament['progress-meter'],
            cls._calculate_state(challonge_tournament)
        )

    @classmethod
    def _calculate_state(cls, tournament):
        if tournament["completed-at"]:
            return "finished"
        elif tournament["started-at"]:
            return "started"
        else:
            return "open"

