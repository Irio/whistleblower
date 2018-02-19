import datetime
from unittest import TestCase, mock

import pandas as pd
from twitter import TwitterError

from whistleblower.targets.twitter import Post, Twitter


class TestTwitter(TestCase):

    def setUp(self):
        self.api = mock.MagicMock()
        self.database = mock.MagicMock()
        self.subject = Twitter(api=self.api, database=self.database)

    def test_profiles(self):
        self.subject = Twitter(api=self.api,
                               database=self.database,
                               profiles_file='tests/fixtures/congresspeople-social-accounts.csv')
        self.assertIsInstance(self.subject.profiles(), pd.DataFrame)

    def test_posted_reimbursements(self):
        self.database.posts.find.return_value = [
            {'document_id': 10},
            {'document_id': 20},
            {'document_id': 30},
        ]
        ids = list(self.subject.posted_reimbursements())
        self.assertEqual([10, 20, 30], ids)

    @mock.patch('whistleblower.targets.twitter.logging')
    def test_follow_congresspeople(self, logging_mock):
        profiles = pd.DataFrame([
            ['DepEduardoCunha', 'DepEduardoCunha2'],
            ['DepRodrigomaia', None],
            [None, None]
        ], columns=['twitter_profile', 'secondary_twitter_profile'])
        self.subject._profiles = profiles
        calls = [
            mock.call.CreateFriendship(screen_name='DepEduardoCunha'),
            mock.call.CreateFriendship(screen_name='DepEduardoCunha2'),
            mock.call.CreateFriendship(screen_name='DepRodrigomaia'),
        ]
        self.subject.follow_congresspeople()
        self.api.assert_has_calls(calls, any_order=True)
        self.assertEqual(3, self.api.CreateFriendship.call_count)
        self.api.CreateFriendship.side_effect = TwitterError('Not found')
        self.subject.follow_congresspeople()
        logging_mock.warning.assert_called()
        self.assertEqual(3, logging_mock.warning.call_count)

    @mock.patch('whistleblower.targets.twitter.urllib.request')
    def test_provision_database(self, request_mock):
        current_time = datetime.datetime(2017, 6, 4, 23, 50, 11)
        current_time_in_epochs = int(current_time.strftime('%s'))
        posts = [
            mock.MagicMock(created_at_in_seconds=current_time_in_epochs,
                           user=mock.MagicMock(screen_name='RosieDaSerenata'),
                           text='https://t.co/09xXzTg2Yc #SerenataDeAmor',
                           id=1),
            mock.MagicMock(created_at_in_seconds=current_time_in_epochs,
                           user=mock.MagicMock(screen_name='RosieDaSerenata'),
                           text='https://t.co/09xxztg2yc #SerenataDeAmor',
                           id=2),
        ]
        self.api.GetUserTimeline.return_value = posts
        self.subject.provision_database()
        calls = [
            mock.call.Request('https://t.co/09xXzTg2Yc', method='HEAD'),
            mock.call.Request('https://t.co/09xxztg2yc', method='HEAD'),
        ]
        request_mock.assert_has_calls(calls, any_order=True)
        self.database.posts.insert_many.assert_called_once_with([
            {
                'integration': 'chamber_of_deputies',
                'target': 'twitter',
                'id': 1,
                'screen_name': 'RosieDaSerenata',
                'created_at': current_time,
                'text': 'https://t.co/09xXzTg2Yc #SerenataDeAmor',
                'document_id': 1,
            },
            {
                'integration': 'chamber_of_deputies',
                'target': 'twitter',
                'id': 2,
                'screen_name': 'RosieDaSerenata',
                'created_at': current_time,
                'text': 'https://t.co/09xxztg2yc #SerenataDeAmor',
                'document_id': 1,
            }
        ])

    def test_posts(self):
        posts = [mock.MagicMock()]
        self.api.GetUserTimeline.return_value = posts
        self.assertEqual([posts], list(self.subject.posts()))
        self.api.GetUserTimeline.assert_called_once_with(
            screen_name='RosieDaSerenata', max_id=None)


class TestPost(TestCase):

    def setUp(self):
        self.api = mock.MagicMock()
        self.database = mock.MagicMock()
        self.reimbursement = {
            'congressperson_name': 'Eduardo Cunha',
            'document_id': 10,
            'state': 'RJ',
            'twitter_profile': 'DepEduardoCunha',
        }
        self.subject = Post(self.reimbursement,
                            api=self.api,
                            database=self.database)

    def test_publish(self):
        self.subject.publish()
        self.api.PostUpdate.assert_called_once_with(self.subject.tweet_data())
        dict_representation = dict(self.subject)
        self.database.posts.insert_one.assert_called_once_with(
            dict_representation)

    def test_tweet_data(self):
        message = (
            '🚨Gasto suspeito de Dep. @DepEduardoCunha (RJ). '
            'Você pode me ajudar a verificar? '
            'https://jarbas.serenata.ai/layers/#/documentId/10 '
            '#SerenataDeAmor na @CamaraDeputados'
        )
        self.assertEqual(message, self.subject.tweet_data())
        self.reimbursement['twitter_profile'] = None
        with self.assertRaises(ValueError):
            self.subject.tweet_data()

    def test_tweet_text(self):
        message = (
            '🚨Gasto suspeito de Dep. @DepEduardoCunha (RJ). '
            'Você pode me ajudar a verificar? '
            'https://jarbas.serenata.ai/layers/#/documentId/10 '
            '#SerenataDeAmor na @CamaraDeputados'
        )
        self.assertEqual(message, self.subject.tweet_text())

