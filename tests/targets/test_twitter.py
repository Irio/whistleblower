import datetime
from unittest import TestCase, mock
from io import BytesIO, BufferedReader

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
            'applicant_id': 10,
            'year': 2015,
            'state': 'RJ',
            'twitter_profile': 'DepEduardoCunha',
        }
        self.subject = Post(self.reimbursement,
                            api=self.api,
                            database=self.database)

    def test_publish(self):
        self.subject.publish()
        text, reimbursement_image = self.subject.tweet_data()
        self.api.PostUpdate.assert_called_once_with(
            media=reimbursement_image, status=text)
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

    def test_camara_image_url(self):
        url = 'http://www.camara.gov.br/cota-parlamentar/documentos/publ/10/2015/10.pdf'
        self.assertEqual(url, self.subject.camara_image_url())

    @mock.patch('whistleblower.targets.twitter.urllib.request.urlopen')
    def test_tweet_image(self, urlopen_mock):
        with open('tests/fixtures/10.pdf', 'rb') as pdf_fixture:
            mock_response = pdf_fixture
            mock_response_read = BytesIO(pdf_fixture.read())
        urlopen_mock.return_value = mock_response_read
        self.assertIsInstance(
            self.subject.tweet_image(), BufferedReader)

        urlopen_mock.side_effect = Exception()
        self.assertIsNone(self.subject.tweet_image())
