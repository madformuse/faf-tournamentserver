import pytest

from tournament.tournamentServer import *

class TestTournamentServer:

    @pytest.fixture
    def server(self):
        return tournamentServer(db=None)

    def test_create(self, server):
        assert server




