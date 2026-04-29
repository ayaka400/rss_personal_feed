# RSS Personal Feed

QiitaおよびZennの新着記事をSlackに自動通知するシステムです。
GitHub Actionsで1時間ごとに実行されます。

## ディレクトリ構成

```
.
├── src/
│   └── main.py       # 全処理
├── state.json        # 既読URL管理（自動更新）
├── config.json       # 監視ユーザー設定
├── requirements.txt
└── .github/workflows/cron.yml
```

## セットアップ

### 1. リポジトリをフォーク / クローン

```bash
git clone https://github.com/your-org/rss-personal-feed.git
cd rss-personal-feed
```

### 2. 監視トピックを設定

[config.json](config.json) を編集し、通知したいトピックを指定します。

```json
{
  "services": [
    {
      "key": "qiita",
      "label": "Qiita",
      "feed_url": "https://qiita.com/tags/{topic}/feed",
      "message": "Qiitaの「{topic}」に新着記事があります\n{url}",
      "topics": ["python", "typescript"]
    },
    {
      "key": "zenn",
      "label": "Zenn",
      "feed_url": "https://zenn.dev/topics/{topic}/feed",
      "message": "Zennの「{topic}」に新着記事があります\n{url}",
      "topics": ["python", "typescript"]
    }
  ]
}
```

複数トピックも指定可能です。

```json
"topics": ["python", "typescript", "ai"]
```

### 3. Slack Webhook URLをシークレットに登録

1. [Slack App の管理画面](https://api.slack.com/apps) で Incoming Webhook を有効化し、Webhook URL を取得
2. GitHub リポジトリの **Settings → Secrets and variables → Actions** を開く
3. `SLACK_WEBHOOK_URL` という名前でシークレットを追加

### 4. ローカルで動作確認（任意）

```bash
pip install -r requirements.txt
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
python src/main.py
```

### 5. GitHub Actionsを有効化

リポジトリを GitHub にプッシュすると、スケジュールが自動的に有効になります。
手動実行は Actions タブから **Run workflow** で行えます。

## 動作仕様

| 項目 | 内容 |
|------|------|
| 実行間隔 | 1時間ごと（GitHub Actions のスケジュール） |
| 差分管理 | `state.json` に既読 URL を保存 |
| 保持上限 | ユーザーごとに最新50件 |
| 冪等性 | 同一記事の二重送信なし |
| エラー | RSS取得失敗時はスキップして継続 |

## Slack通知フォーマット

```
Qiitaに新着記事があります
https://qiita.com/...
```
