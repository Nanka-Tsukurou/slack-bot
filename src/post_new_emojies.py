import json
import os
import datetime
from logging import getLogger
from slack import WebClient
from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute

logger = getLogger(__name__)

slack_token = os.getenv('SLACK_TOKEN')
slack_channel = os.getenv('SLACK_CHANNEL')
jst = datetime.timezone(datetime.timedelta(hours=9))


class SlackEmoji(Model):
    class Meta:
        table_name = 'slack_emojies'
        region = 'ap-northeast-1'

    name = UnicodeAttribute(hash_key=True)
    url = UnicodeAttribute()
    update_at = UnicodeAttribute()


def post_new_emojies():
    client = WebClient(slack_token)
    current_date = datetime.datetime.now(
        tz=jst).strftime('%Y-%m-%dT%H:%M:%S%z')

    max_notify_count = 10

    # DynamoDBより登録済みemoji名を取得
    registered_emoji_names = list(map(lambda e: e.name, SlackEmoji.scan()))

    # Slackより登録済みemojiを取得
    emojies = client.emoji_list()
    assert emojies['ok']

    # Slackのemojiを走査し、通知対象を決定
    should_notify_emojies = []
    for name, url in emojies['emoji'].items():
        if (name not in registered_emoji_names) and url.startswith('https:'):
            # DynamoDBに未登録のemojiの場合、通知対象とする
            slack_emoji = SlackEmoji(name)
            slack_emoji.url = url
            slack_emoji.update_at = current_date
            should_notify_emojies.append(slack_emoji)

    # 通知対象が存在する場合
    if len(should_notify_emojies) > 0:
        logger.warn(f'should notify emoji count: {len(should_notify_emojies)}')

        # DynamoDBに登録
        with SlackEmoji.batch_write() as batch:
            for emoji in should_notify_emojies:
                batch.save(emoji)

        # Slack通知
        for emoji in should_notify_emojies[:max_notify_count]:
            message = '新しいemojiが追加されたで！！\n`:{}:` {}'.format(
                emoji.name, emoji.url)
            client.chat_postMessage(channel=slack_channel, text=message)

        if len(should_notify_emojies) > max_notify_count:
            message = '他にも{}個投稿されとったけど、他は自分で確認してーや！'.format(
                len(should_notify_emojies) - max_notify_count)
            client.chat_postMessage(channel=slack_channel, text=message)


def lambda_handler(event, lambda_context):
    try:
        logger.info('start')
        logger.info(f'event: {json.dumps(event)}')

        post_new_emojies()

    except Exception as e:
        logger.exception('fail')

        raise e


if __name__ == '__main__':
    logger.info('start')
    post_new_emojies()
