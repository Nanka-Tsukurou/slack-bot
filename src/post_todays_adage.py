import json
import os
import datetime
from time import sleep
from functools import reduce
from logging import getLogger
from slack import WebClient
from slack.errors import SlackApiError

logger = getLogger(__name__)

slack_token = os.getenv('SLACK_TOKEN')
slack_user_token = os.getenv('SLACK_USER_TOKEN')
slack_channel = os.getenv('SLACK_CHANNEL')
utc = datetime.timezone.utc


def post_todays_adage():
    client = WebClient(slack_token)
    user_client = WebClient(slack_user_token)

    threshold = datetime.datetime.now(tz=utc) - datetime.timedelta(days=1)

    query = 'after:{} has:reaction'.format(threshold.strftime('%F'))
    search_result = user_client.search_all(query=query,
                                           count=1000,
                                           sort='timestamp',
                                           sort_dir='desc')

    adage_rankings = []
    for message in search_result['messages']['matches']:
        try:
            sleep(0.2)
            reactions = client.reactions_get(channel=message['channel']['id'],
                                             timestamp=message['ts'])

        except SlackApiError as e:
            logger.warning('channel={}, ts={} -> {}'.format(
                message['channel']['id'], message['ts'], e).replace('\n', ' '))
            continue

        reaction_count = reduce(lambda n, m: n + m['count'],
                                reactions['message']['reactions'], 0)

        adage_rankings.append({
            'permalink': message['permalink'],
            'ts': message['ts'],
            'count': reaction_count
        })

    adage_rankings.sort(key=lambda m: (m['count'], m['ts']), reverse=True)

    if len(adage_rankings) > 0:
        adage = adage_rankings[0]

        message = '本日の名言は、{}リアクションを集めたコイツに決まりや！！\n{}'.format(
            adage['count'], adage['permalink'])

        client.chat_postMessage(channel=slack_channel, text=message)


def lambda_handler(event, lambda_context):
    try:
        logger.info('start')
        logger.info(f'event: {json.dumps(event)}')

        post_todays_adage()

    except Exception as e:
        logger.exception('fail')

        raise e


if __name__ == '__main__':
    logger.info('start')
    post_todays_adage()
