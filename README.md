# slack-bot

## requirements

- npm
- pipenv
- slack botとそのトークン

## usage

```
# 環境変数を設定
$ cp .env.sample .env

# インストール
$ npm install
$ pipenv install --dev

# 実行
$ pipenv run post_new_channels

# デプロイ
$ npm run sls:deploy
```