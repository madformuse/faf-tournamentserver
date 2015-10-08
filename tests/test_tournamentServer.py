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
        # Index will return empty dict
        challonge.tournaments.index = lambda: {}

        server.importTournaments()

        assert server.tournaments == {}




