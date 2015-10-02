import pytest

from tournament.tournamentServer import *

class TestTournamentServer:

    def test_create(self):
        assert tournamentServer(db=None)
