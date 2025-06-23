"""
OpenAI GPTプロバイダー実装
GPT-4、GPT-4-mini等のOpenAIモデルへの統一インターフェース
"""

import logging
from typing import Dict, Any, Optional
from .base_provider import LLMProvider, LLMResponse

logger = logging.getLogger(__name__)

try:
    import openai
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI パッケージがインストールされていません")


class OpenAIProvider(LLMProvider):
    """
    OpenAI GPTプロバイダー
    """
    
    def __init__(self, api_key: str, model_name: str = "o4-mini-high", **kwargs):
        """
        Args:
            api_key: OpenAI API Key
            model_name: OpenAIモデル名 (o4-mini-high, o4-mini, gpt-4o等)
            **kwargs: その他の設定パラメータ
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI パッケージがインストールされていません。pip install openai でインストールしてください")
        
        super().__init__(api_key, **kwargs)
        self.model_name = model_name
        
    def initialize(self) -> None:
        """
        OpenAIクライアントの初期化
        """
        try:
            # OpenAIクライアントの設定
            self._client = OpenAI(api_key=self.api_key)
            
            # 接続テスト（モデル一覧を取得）
            models = self._client.models.list()
            available_models = [model.id for model in models.data]
            
            if self.model_name not in available_models:
                logger.warning(f"指定されたモデル '{self.model_name}' が利用可能モデルリストに見つかりません")
            
            logger.info(f"OpenAIクライアントが正常に初期化されました: {self.model_name}")
            
        except Exception as e:
            logger.error(f"OpenAIクライアントの初期化に失敗しました: {str(e)}")
            raise
    
    def generate_content(
        self,
        prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 2048,
        **kwargs
    ) -> LLMResponse:
        """
        OpenAI GPTでコンテンツを生成
        
        Args:
            prompt: 生成用プロンプト
            temperature: ランダム性パラメータ (0.0-1.0)
            max_tokens: 最大出力トークン数
            **kwargs: OpenAI固有のパラメータ
            
        Returns:
            LLMResponse: 生成されたコンテンツ
            
        Raises:
            Exception: 生成に失敗した場合
        """
        if not self.is_initialized():
            raise ValueError("OpenAIプロバイダーが初期化されていません")
        
        try:
            # メッセージ形式に変換
            messages = [
                {"role": "user", "content": prompt}
            ]
            
            # OpenAI API呼び出し
            response = self._client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            # レスポンス解析
            content = ""
            finish_reason = None
            
            if response.choices and len(response.choices) > 0:
                choice = response.choices[0]
                content = choice.message.content or ""
                finish_reason = choice.finish_reason
            
            # 使用量情報の取得
            usage_info = None
            if response.usage:
                usage_info = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            
            return LLMResponse(
                content=content,
                usage_info=usage_info,
                model=self.model_name,
                finish_reason=finish_reason
            )
            
        except Exception as e:
            logger.error(f"OpenAIコンテンツ生成エラー: {str(e)}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        OpenAIモデル情報を取得
        
        Returns:
            Dict[str, Any]: モデル情報
        """
        # モデル別の設定
        model_configs = {
            "o4-mini-high": {
                "max_tokens": 65536,
                "context_window": 200000,
                "supports_streaming": True,
                "version": "o4-mini-high"
            },
            "o4-mini": {
                "max_tokens": 32768,
                "context_window": 200000,
                "supports_streaming": True,
                "version": "o4-mini"
            },
            "gpt-4o": {
                "max_tokens": 4096,
                "context_window": 128000,
                "supports_streaming": True,
                "version": "4o"
            },
            "gpt-4o-mini": {
                "max_tokens": 16384,
                "context_window": 128000,
                "supports_streaming": True,
                "version": "4o-mini"
            },
            "gpt-4-turbo": {
                "max_tokens": 4096,
                "context_window": 128000,
                "supports_streaming": True,
                "version": "4-turbo"
            }
        }
        
        config = model_configs.get(self.model_name, {
            "max_tokens": 4096,
            "context_window": 8192,
            "supports_streaming": True,
            "version": "unknown"
        })
        
        return {
            "provider": self.provider_name,
            "model": self.model_name,
            **config
        }
    
    @property
    def provider_name(self) -> str:
        """プロバイダー名"""
        return "openai"
    
    def _extract_json_from_response(self, response_text: str) -> str:
        """
        レスポンステキストからJSONを抽出（OpenAI特有の処理）
        
        Args:
            response_text: OpenAIからのレスポンステキスト
            
        Returns:
            str: 抽出されたJSON文字列
        """
        response_text = response_text.strip()
        
        # JSONブロック記法の除去
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        elif response_text.startswith("```"):
            response_text = response_text[3:]
        
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        return response_text.strip()