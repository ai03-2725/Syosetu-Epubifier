# Syosetu-Epubifier

> [!NOTE]
> このアプリは現在開発中です。


このアプリは`https://syosetu.org/`などで公開されている小説を取得し、電子書籍（Epubファイル）へ変換します。


## 概要
[Narou.rb MOD](https://github.com/ponponusa/narou-mod)を参考に作っていますが、 自分用の仕様で0から作製しています。
- 小説情報の取得を[Pydoll](https://github.com/autoscrape-labs/pydoll)で行い、実際のChromiumブラウザを動かして取得
  - Cloudflare Turnstileを高頻度で食らう共有IPでも利用可能
- [改造版AozoraEpub3](https://github.com/kyukyunyorituryo/AozoraEpub3)ではなく[ebooklib](https://github.com/aerkalov/ebooklib/)でePubを手動作製
  - 依存ソフトは実質ChromiumブラウザとDockerベースイメージだけになり、それ以外はpipとnpmからインストールできるライブラリだけで済む
- [Django](https://www.djangoproject.com)で作製されたバックエンドが小説を取得・保存・変換し、[Solid](https://github.com/solidjs/solid)を利用したフロントエンドがそれを制御する方式
- Linux上での利用を想定（Dockge, Dockhand, Komodoなどでホームサーバーでの運用を想定）
- 現状ePubのメール送信機能などは無し（SyncthingなどでePub出力フォルダの同期を想定）

## 対応しているサイト

現在対応しているサイト
- `https://syosetu.org/`

将来対応したいサイト
- `http://syosetu.com/`
- `https://kakuyomu.jp/`


## 機能

実装済み  
- 小説情報の取得
- 小説の更新
- 小説のePub変換
- 小説の凍結
- ePubの後処理
  - 空白の改行の圧縮
  - 文章部分の自動字下げ
  - セパレーターの検出と自動字下げ
  - `<hr/>`タグの置き換え

実装予定
- ePub後処理のOn/Off切り替え
- 小説のバックアップ出力
- 自動更新設定
- 指定したウェブページのリストをePubへ変換
- より人間的なブラウザ操作で小説データを取得
- ログインなどのセキュリティを追加
- 小説リストにパジネーションを追加

将来追加できたら追加したい機能
- epubをメールでKindle・Koboへ送信（現状KindleやKoboのデバイスを所有していないのでテスト不可能）


# テスト環境

アプリ稼働：MacOS 26、AlmaLinux 10
出力ePub閲覧：MacOS Booksアプリ、Android（Onyx Boox）上KOReaderアプリ


# バグリスト
- 小説追加タスクが反映されなくなる
- enqueued_atが存在しない場合がある（generate_epub）
- queue pending状態のfetchタスクが表示されない


# 利用方法
1. PodmanとPodman-Compose、またはDockerとDocker-Composeをインストール
1. `compose-template-local.yaml`を`compose.yaml`へ複製し、`SECRET_KEY`を変更
1. アプリデータフォルダを作製（`prepare-data-dirs-linux/mac.sh`を参照）
1. `podman/docker compose up`