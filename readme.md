
# distbuilder

外部ライブラリをビルドするためのユーティリティ.

## config

`config-template.toml` をコピーして `config.toml` にリネームします.

`config.toml` の説明に従って記述を書き換えます.

## python venv

venv をお勧めしますが, 必須ではありません.

`pip-requirements.txt` をもとに必要なライブラリを install します.

```
python.exe -m pip install -r pip-requirements.txt
```

## build

他人に配るものでもないし, 完全に私の必要用途で最適化されていますが, libs/<ライブラリ名>/config.toml を確認します.

ビルドバリアントを設定すれば, あとは以下のコマンドでビルドが行われます.

```
python main.py <ライブラリ名>
```

`--clean` オプションで, ダウンロード済みソースを削除できます.

## 結果

config.toml の `directories.install` の階層以下に,

```
/<libraryName>/<version>/<variantName>/[<config>/]...
```

としてビルド成果物が配置されます.
