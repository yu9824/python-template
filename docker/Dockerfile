# syntax=docker/dockerfile:1

# このライブラリの利用者向けイメージ。開発用のコンテナは .devcontainer/ にある。
#
#   docker build -f docker/Dockerfile -t python-template .
#   docker run --rm -it python-template
#
# ビルドコンテキストはリポジトリのルート。送るファイルは隣の
# Dockerfile.dockerignore (この Dockerfile 専用の除外設定) で絞っている。

# ---- builder: wheel を作るだけのステージ ----
FROM python:3.14-slim AS builder

# setuptools_scm は git コマンドと .git からバージョンを決める。どちらも
# このステージにしか入れず、最終イメージには wheel だけを持ち込む。
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src
COPY . .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /dist .

# ---- runtime ----
FROM python:3.14-slim

RUN useradd --create-home app

# wheel はパッケージ名ではなくファイルのパスで指定する。名前で指定すると
# (--find-links)、手元の wheel が開発版 (.devN) のとき、index 上に同名の
# 正式版があれば pip はそちらを優先して入れてしまう。
#
# bind mount なので、wheel 自体はイメージのレイヤーに残らない。
RUN --mount=type=bind,from=builder,source=/dist,target=/tmp/dist \
    pip install --no-cache-dir "$(ls /tmp/dist/*.whl)[optional]"

USER app
WORKDIR /home/app
CMD ["python"]
