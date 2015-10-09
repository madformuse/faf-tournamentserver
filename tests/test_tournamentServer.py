import pytest
from unittest.mock import patch
from tournament.tournamentServer import *


class TestTournamentServer:
    CHALLONGE_TOURNAMENT = {
        'id': '1',
        'name': 'test',
        'full-challonge-url': 'http://www.google.com',
        'description': 'Amazing',
        'tournament-type': 'dunno',
        'progress-meter': '0',
        'started-at': None,
        'completed-at': None,
        'open_signup': None
    }

    @pytest.fixture
    def server(self):
        return tournamentServer(db=None)

    def test_create(self, server):
        assert server

    def test_no_tournaments(self, server):
        with patch('challonge.tournaments.index', return_value={}) as fake_index:
            server.importTournaments()

        assert server.tournaments == {}

    def test_tournament_mapping(self, server):
        faf_tournament = {
            'name': self.CHALLONGE_TOURNAMENT['name'],
            'url': self.CHALLONGE_TOURNAMENT['full-challonge-url'],
            'description': self.CHALLONGE_TOURNAMENT['description'],
            'type': self.CHALLONGE_TOURNAMENT['tournament-type'],
            'progress': self.CHALLONGE_TOURNAMENT['progress-meter'],
            'state': 'open',
            'participants': []
        }

        self.import_tournament(self.CHALLONGE_TOURNAMENT, server)

        assert server.tournaments[self.CHALLONGE_TOURNAMENT['id']] == faf_tournament

    def test_started(self, server):
        self.CHALLONGE_TOURNAMENT['started-at'] = "Not None"

        self.import_tournament(self.CHALLONGE_TOURNAMENT, server)

        assert server.tournaments[self.CHALLONGE_TOURNAMENT['id']]['state'] == 'started'

    def test_finished(self, server):
        self.CHALLONGE_TOURNAMENT['completed-at'] = "Not None"

        self.import_tournament(self.CHALLONGE_TOURNAMENT, server)

        assert server.tournaments[self.CHALLONGE_TOURNAMENT['id']]['state'] == 'finished'

    def test_close_open_signups(self, server):
        self.CHALLONGE_TOURNAMENT['open_signup'] = "Not None"

        with patch('challonge.tournaments.update') as updater:
            self.import_tournament(self.CHALLONGE_TOURNAMENT, server)

        updater.assert_called_with(self.CHALLONGE_TOURNAMENT['id'], open_signup="false")

    def import_tournament(self, tournament, server):
        with patch('challonge.tournaments.index', return_value=[tournament]):
            with patch('challonge.participants.index', return_value=[]):
                server.importTournaments()