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

実装予定
- 小説のバックアップ出力
- 自動更新設定
- 指定したウェブページのリストをePubへ変換