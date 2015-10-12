import pytest
from unittest.mock import patch
from unittest import mock
from tournament.tournament_server import *
from tournament.user_service import UserService

class TestTournamentServer:

    @pytest.fixture
    def user_service(self):
        m = mock.create_autospec(UserService)

        return m

    @pytest.fixture
    def server(self, user_service):
        return TournamentServer(user_service=user_service)

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

    @pytest.fixture
    def user(self, user_service):
        test_user = {'id': 2, 'name': 'Tom', 'logged_in': True, 'renamed': False}

        user_service.lookup_user.return_value = test_user

        return test_user

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

    def test_participant_cached(self, server, challonge_tournament, user):
        # Set conditions for most thorough checks
        challonge_tournament['started-at'] = "Not None"
        challonge_tournament['progress-meter'] = 0
        participant = {
            'name': 'Tom',
            'id': 1
        }
        user.update(name='Tom', logged_in=True)

        self.import_tournament(challonge_tournament, server, participant)

        assert server.in_tournament('Tom', challonge_tournament['id'])

    def test_user_removed_when_absent(self, server, challonge_tournament, user):
        # Set condition to invoke started checks
        challonge_tournament['started-at'] = "Not None"
        challonge_tournament['progress-meter'] = 0
        # User not logged in
        user.update(logged_in=False)

        with patch('challonge.participants.destroy') as destroy_participant:
            self.import_tournament(challonge_tournament, server, {'name': 'Tom', 'id': 1})

        destroy_participant.assert_called_with(challonge_tournament['id'], 1)

    def test_not_removed_unless_started(self, server, challonge_tournament, user_service):

        # This is strange (but current) behaviour. Even if no record of user is found they remain
        # in the tournament until it starts

        # Set condition so state is not started
        challonge_tournament['started-at'] = None
        user_service.lookup_user.return_value = None

        self.import_tournament(challonge_tournament, server, {'name': 'Tom', 'id': 1})

        assert server.in_tournament('Tom', challonge_tournament['id'])

    def test_user_removed_if_missing(self, server, challonge_tournament, user_service):
        # Set condition to invoke started checks
        challonge_tournament['started-at'] = "Not None"
        challonge_tournament['progress-meter'] = 0
        user_service.lookup_user.return_value = None

        with patch('challonge.participants.destroy') as destroy_participant:
            self.import_tournament(challonge_tournament, server, {'name': 'Tom', 'id': 1})

        destroy_participant.assert_called_with(challonge_tournament['id'], 1)

    def test_name_updated(self, server, challonge_tournament, user):
        # Set conditions so extra checks are not performed
        challonge_tournament['started-at'] = None

        participant = {
            'name': 'Tom',
            'id': 1
        }

        user.update(name='Sally', renamed=True)

        with patch('challonge.participants.update') as update_participant:
            self.import_tournament(challonge_tournament, server, participant)

        # Make sure name updated on Challonge and current name is cached.
        update_participant.assert_called_with(challonge_tournament['id'], participant['id'], name='Sally')
        assert server.in_tournament('Sally', challonge_tournament['id'])

    def test_user_removed(self, challonge_tournament, server, user):
        participant = {
            'name': 'Tom',
            'id': 3
        }

        user.update(name='Tom')
        self.import_tournament(challonge_tournament, server, participant)
        assert server.in_tournament(participant['name'], challonge_tournament['id'])

        with patch('challonge.participants.destroy') as destroy:
            server.remove_participant(participant['name'], challonge_tournament['id'])

        destroy.assert_called_with(challonge_tournament['id'], participant['id'])

    def import_tournament(self, tournament, server, participants=None):
        with patch('challonge.tournaments.index', return_value=[tournament] if tournament else []):
            with patch('challonge.participants.index', return_value=[participants] if participants else []):
                server.import_tournaments()
