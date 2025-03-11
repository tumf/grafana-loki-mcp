---
description: use `uv` packagemanager better than pip 
globs: 
alwaysApply: false
---
# uv - 高速なPythonパッケージマネージャー

uvは、Rustで書かれた非常に高速なPythonパッケージマネージャーです。従来のpip、pip-tools、poetry、pyenv、virtualenvなどの複数のツールの機能を1つにまとめたものです。

## 主な特徴

- **高速**: pipと比較して10〜100倍速い
- **Rustで実装**: Pythonに依存しない独立したバイナリとして提供
- **多機能**: パッケージ管理、仮想環境管理、Pythonバージョン管理など
- **キャッシュ機能**: 共通の依存関係を再利用して高速化

## 基本コマンド

### インストールと初期設定

```bash
# プロジェクトの初期化
uv init  # pyproject.tomlを作成し、基本的なプロジェクト構造を設定

# Pythonのインストールと管理
uv python install  # 最新バージョンのPythonをインストール
uv python install 3.12  # 特定のバージョンをインストール
```

### パッケージ管理

```bash
# パッケージの追加
uv add パッケージ名  # pyproject.tomlに追加し、インストール

# パッケージの削除
uv remove パッケージ名  # パッケージの削除

# 依存関係の同期
uv sync  # pyproject.tomlとuv.lockに基づいて依存関係をインストール

# ロックファイルの作成
uv lock  # 依存関係をロックファイルに記録
```

### 実行とスクリプト

```bash
# スクリプトの実行
uv run python script.py  # 仮想環境を明示的に有効化せずにスクリプトを実行
uv run コマンド  # 任意のコマンドを実行
```

### 仮想環境の管理

```bash
# 仮想環境の作成
uv venv  # デフォルトの仮想環境を作成
uv venv 環境名 --python 3.12.4  # 特定の名前とPythonバージョンで仮想環境を作成
```

## uvの利点

1. **速度**: パッケージのインストールが非常に高速
2. **シンプルさ**: 複数のツールの機能を1つに統合
3. **依存関係の管理**: ロックファイルによる再現性の高い環境
4. **Pythonバージョン管理**: pyenvのような機能も内蔵
5. **キャッシュ機能**: 共通の依存関係を再利用して高速化

## 使用例

### 新しいプロジェクトの作成

```bash
# 新しいディレクトリを作成
mkdir my-project
cd my-project

# プロジェクトを初期化
uv init

# パッケージを追加
uv add requests pandas

# スクリプトを実行
uv run python main.py
```

### 既存のプロジェクトでの使用

```bash
# 依存関係をインストール
uv sync

# スクリプトを実行
uv run python main.py
```

## まとめ

uvは従来のPythonパッケージ管理ツールと比較して、速度と使いやすさに優れています。特に、複数のツールの機能を1つにまとめることで、Pythonプロジェクトの管理が簡単になります。また、Rustで実装されているため、非常に高速に動作します。 
