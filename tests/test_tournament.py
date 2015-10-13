import pytest

from tournament.tournament import Tournament


class TestTournament:

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

    def test_basic_conversion(self, challonge_tournament):
        expected = Tournament("test", "http://www.google.com", "Amazing", "dunno", 0, "open")
        actual = Tournament.from_challonge(challonge_tournament)
        assert expected.name == actual.name
        assert expected.url == actual.url
        assert expected.type == actual.type
        assert expected.description == actual.description

    def test_serialize(self,challonge_tournament):

        # Client expects the a certain subset of data back in a dictionary.
        expected_format = {
            "name": 'test',
            "url": 'http://www.google.com',
            "description": 'Amazing',
            "type": 'dunno',
            "state": 'open',
            "participants": []
        }

        assert Tournament.from_challonge(challonge_tournament).serialize() == expected_format


