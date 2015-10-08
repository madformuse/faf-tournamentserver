import pytest
from unittest.mock import patch
from tournament.tournamentServer import *


class TestTournamentServer:

    @pytest.fixture
    def server(self):
        return tournamentServer(db=None)

    def test_create(self, server):
        assert server

    def test_no_tournaments(self,server):
        with patch('challonge.tournaments.index', side_affect={}) as fake_index:
            server.importTournaments()

        assert server.tournaments == {}




