# distbuilder

外部ライブラリをビルドするためのユーティリティ.

## preference

`preference-template.toml` をコピーして `preference.toml` にリネームします.

`preference.toml` の説明に従って記述を書き換えます.

## python venv

venv をお勧めしますが, 必須ではありません.

`pip-requirements.txt` をもとに必要なライブラリを install します.

```
python.exe -m pip install -r pip-requirements.txt
```

## build

他人に配るものでもないし, 完全に私の必要用途で最適化されていますが, libs/<ライブラリ名>/config.toml を確認します.

ここまだ暫定：

```
python run.py test <ライブラリ名> --config Debug
```

`--config` は今は使ってないけどとりあえず Debug か Release か指定してください

ライブラリ名は、 libs の下にあるディレクトリをフルで指定するか, "." の下のみを指定します.

## 結果

config.toml の `directories.install` の階層以下に,

```
/<libraryName>/<version>/<variantName>/[<config>/]...
```

としてビルド成果物が配置されます.
