import pytest
from unittest.mock import patch
from tournament.tournament_server import *


class TestTournamentServer:

    @pytest.fixture
    def server(self):
        return TournamentServer(db=None)

    @pytest.fixture
    def challonge_tournament(self):
        return {
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
    def test_create(self, server):
        assert server

    def test_no_tournaments(self, server):
        with patch('challonge.tournaments.index', return_value={}) as fake_index:
            server.import_tournaments()

        assert server.tournaments == {}

    def test_tournament_mapping(self, server, challonge_tournament):
        faf_tournament = {
            'name': challonge_tournament['name'],
            'url': challonge_tournament['full-challonge-url'],
            'description': challonge_tournament['description'],
            'type': challonge_tournament['tournament-type'],
            'progress': challonge_tournament['progress-meter'],
            'state': 'open',
            'participants': []
        }

        self.import_tournament(challonge_tournament, server)

        assert server.tournaments[challonge_tournament['id']] == faf_tournament

    def test_started(self, server, challonge_tournament):
        challonge_tournament['started-at'] = "Not None"

        self.import_tournament(challonge_tournament, server)

        assert server.tournaments[challonge_tournament['id']]['state'] == 'started'

    def test_finished(self, server, challonge_tournament):
        challonge_tournament['completed-at'] = "Not None"

        self.import_tournament(challonge_tournament, server)

        assert server.tournaments[challonge_tournament['id']]['state'] == 'finished'

    def test_close_open_signups(self, server, challonge_tournament):
        challonge_tournament['open_signup'] = "Not None"

        with patch('challonge.tournaments.update') as updater:
            self.import_tournament(challonge_tournament, server)

        updater.assert_called_with(challonge_tournament['id'], open_signup="false")

    def test_participant_cached(self,server, challonge_tournament):
        # Set conditions so extra checks are not performed
        challonge_tournament['started-at'] = None

        participant = {
            'name': 'Tom',
            'id': 1
        }

        with patch.object(TournamentServer, 'lookup_id_from_login', return_value=5):
            self.import_tournament(challonge_tournament, server, participant)

        assert server.tournaments[challonge_tournament['id']]['participants'][0] == {'name': 'Tom', 'id': 1}

    def test_name_updated(self, server, challonge_tournament):
        # Set conditions so extra checks are not performed
        challonge_tournament['started-at'] = None

        participant = {
            'name': 'Tom',
            'id': 1
        }

        # If FAF can't find 'Tom' it looks up the history to try and locate him. If found, challonge is updated.
        with patch.object(TournamentServer, 'lookup_id_from_login', return_value=None):  # Not found
            with patch.object(TournamentServer, 'lookup_id_from_history', return_value=2):  # Yay we used to know him!
                with patch.object(TournamentServer, 'lookup_name_by_id', return_value='Sally'):  # Each to their own
                    with patch('challonge.participants.update') as update_participant:    # Should be called
                        self.import_tournament(challonge_tournament, server, participant)

        update_participant.assert_called_with(challonge_tournament['id'], participant['id'], name='Sally')

    def import_tournament(self, tournament, server, participants=None):
        with patch('challonge.tournaments.index', return_value=[tournament] if tournament else []):
            with patch('challonge.participants.index', return_value=[participants] if participants else []):
                server.import_tournaments()
