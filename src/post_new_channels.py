import json
import os
import datetime
from logging import getLogger
from slack import WebClient

logger = getLogger(__name__)

slack_token = os.getenv('SLACK_TOKEN')
slack_channel = os.getenv('SLACK_CHANNEL')
jst = datetime.timezone(datetime.timedelta(hours=9))


def post_new_channels():
    threshold = datetime.datetime.now() - datetime.timedelta(hours=24)
    client = WebClient(slack_token)

    channels = client.channels_list()
    assert channels['ok']

    target_channels = list(
        filter(lambda c: c['created'] >= int(threshold.timestamp()),
               channels['channels']))

    if len(target_channels) == 0:
        logger.warning('target channels unfound...')
        return

    users = client.users_list()
    assert users['ok']

    for channel in target_channels:
        user = next(
            filter(lambda m: m['id'] == channel['creator'], users['members']))

        message = '{} が新しいチャンネル {} を {} 頃に作ったみたいや！\n要チェックやでー！！'.format(
            user['profile']['real_name_normalized'],
            '<#{}>'.format(channel['id']),
            datetime.datetime.fromtimestamp(channel['created'],
                                            jst).strftime('%Y/%m/%d %H:%M'))

        client.chat_postMessage(channel=slack_channel, text=message)


def lambda_handler(event, lambda_context):
    try:
        logger.info('start')
        logger.info(f'event: {json.dumps(event)}')

        post_new_channels()

    except Exception as e:
        logger.exception('fail')

        raise e


if __name__ == '__main__':
    logger.info('start')
    post_new_channels()
