# 単体テスト
ファイルごとに *_test.py のファイル名でテストを実装しています。
テストケースは単体テスト仕様書に沿って作成しました。

## 全件実行
```
cd baogw-script-dev/alertscripts/
python3 -m unittest discover -s tests/ -p "*_test.py"
```

## ファイル指定で実行
```
python3 <テストファイル名>
```

# 注意点
* python3.4.X 環境で実行すること
    * 武田さんが残された 202004_TM試験環境 を利用中 オリジナルは共有フォルダに
* 開発環境のDBみなおしすること
    * 最新の仕様どおりになっているか
        * gw_events, gw_rescue_events の kisys_status の次のカラムは host
            * zabbix_id は削除
        * gw_events, gw_rescue_events の summary カラムのサイズは 512 ではなく 10000
    * DB baogw を baogw_test1, baogw_test2 で複製しておく

# Tips
## `@patch()`
モック使用の宣言。複数モックを宣言した場合は下から順に引数と結びつく。

## `subTest`
パターンをfor文でまわすようなテストをパターンごとに成否判定できるようにする仕組み。

## プロジェクト特有の実装
### unittestフラグ
無限ループしてしまうモジュールのテストのため、unittestフラグが立っていたらbreakするよう実装した。
test_helper.py を参照のこと。
