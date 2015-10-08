import pytest
from unittest.mock import patch
from tournament.tournamentServer import *


class TestTournamentServer:
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
        challonge_tournament = {
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

        faf_tournament = {
            'name': challonge_tournament['name'],
            'url': challonge_tournament['full-challonge-url'],
            'description': challonge_tournament['description'],
            'type': challonge_tournament['tournament-type'],
            'progress': challonge_tournament['progress-meter'],
            'state': 'open',
            'participants': []
        }

        with patch('challonge.tournaments.index', return_value=[challonge_tournament]):
            with patch('challonge.participants.index', return_value=[]):
                server.importTournaments()

        assert server.tournaments['1'] == faf_tournament
