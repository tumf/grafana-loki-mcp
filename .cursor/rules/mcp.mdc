# Model Context Protocol (MCP) の基礎知識

## MCPとは

Model Context Protocol (MCP) は、大規模言語モデル (LLM) とツールを接続するための標準プロトコルです。MCPを使用することで、LLMはさまざまなツールやリソースにアクセスし、より複雑なタスクを実行できるようになります。

## MCPの主要コンポーネント

MCPは以下の主要なコンポーネントで構成されています：

1. **MCPサーバー**: ツール、リソース、プロンプトを提供するサーバー
2. **MCPクライアント**: サーバーに接続し、ツールを呼び出すクライアント
3. **LLM**: クライアントからの入力を処理し、必要に応じてツールを呼び出す

## MCPの主な機能

### 1. ツール (Tools)

ツールは、LLMが実行できる特定の機能を提供します。例えば：
- データベースクエリの実行
- 外部APIの呼び出し
- ファイルの読み書き
- 計算の実行

各ツールは名前、説明、パラメータスキーマ、戻り値スキーマを持ちます。

### 2. リソース (Resources)

リソースは、LLMがアクセスできるデータソースです。例えば：
- ドキュメント
- データベース
- コードリポジトリ
- 設定ファイル

リソースはURIで識別され、読み取り/書き込みアクセスが可能です。

### 3. プロンプト (Prompts)

プロンプトは、LLMに特定のタスクを実行させるための指示です。MCPサーバーは、特定のユースケース向けに最適化されたプロンプトを提供できます。

## MCPの通信フロー

1. **クライアントがサーバーに接続**: MCPクライアントがMCPサーバーに接続します
2. **ツール一覧の取得**: クライアントがサーバーから利用可能なツールの一覧を取得します
3. **ユーザー入力の処理**: ユーザーからの入力をLLMに送信します
4. **ツールの呼び出し**: LLMが必要に応じてツールを呼び出します
5. **結果の返却**: ツールの実行結果をLLMに返し、LLMが最終的な応答を生成します

## MCPの実装方法

### サーバー側

```python
# FastMCPを使用した例
from fastmcp import FastMCP

# サーバーの作成
mcp = FastMCP(
    "Example MCP Server",
    host="0.0.0.0",
    port=52229
)

# ツールの定義
@mcp.tool()
def example_tool(param1: str, param2: int) -> dict:
    """
    Example tool description.
    
    Args:
        param1: First parameter description
        param2: Second parameter description
        
    Returns:
        Dict containing results
    """
    # ツールの実装
    return {"result": f"{param1}: {param2}"}

# サーバーの実行
if __name__ == "__main__":
    mcp.run()
```

### クライアント側

```python
# 基本的なMCPクライアント
import requests

class MCPClient:
    def __init__(self, base_url: str = "http://localhost:52229"):
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Content-Type": "application/json",
        }
    
    def call_tool(self, tool_name: str, params: dict) -> dict:
        """ツールを呼び出す"""
        url = f"{self.base_url}/api/tools/{tool_name}"
        
        try:
            response = requests.post(url, headers=self.headers, json=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e), "status": "error"}
```

## MCPのトランスポート

MCPは複数のトランスポート方式をサポートしています：

1. **HTTP**: RESTful APIを使用した通信
2. **WebSocket**: 双方向通信
3. **stdio**: 標準入出力を使用した通信（CLIツールに適しています）
4. **SSE (Server-Sent Events)**: サーバーからクライアントへの一方向通信

## MCPのベストプラクティス

1. **エラーハンドリング**
   - ツール呼び出しは常にtry-catchブロックでラップする
   - 意味のあるエラーメッセージを提供する
   - 接続の問題を適切に処理する

2. **リソース管理**
   - 適切なクリーンアップのためのメカニズムを使用する
   - 使用後に接続を閉じる
   - サーバーの切断を処理する

3. **セキュリティ**
   - APIキーは環境変数や設定ファイルに安全に保存する
   - サーバーのレスポンスを検証する
   - ツールのアクセス権限に注意する

## MCPの利点

1. **標準化**: 異なるLLMとツール間の統一されたインターフェース
2. **モジュール性**: 新しいツールやリソースを簡単に追加できる
3. **再利用性**: 同じツールを複数のLLMやアプリケーションで使用できる
4. **セキュリティ**: ツールのアクセス権限を細かく制御できる
5. **拡張性**: 新しい機能やプロトコルの拡張が容易

## MCPの実装例

- **FastMCP**: Pythonで実装されたMCPサーバーフレームワーク
- **MCP SDK**: TypeScript/JavaScript用のMCPクライアント/サーバーSDK
- **Claude Desktop**: MCPを使用したAnthropicのデスクトップアプリケーション 