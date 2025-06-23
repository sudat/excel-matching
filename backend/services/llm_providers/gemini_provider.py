"""
Google Gemini AIプロバイダー実装
Gemini 2.5 Flash/Proモデルへの統一インターフェース
"""

import logging
from typing import Dict, Any, Optional
import google.generativeai as genai
from .base_provider import LLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class GeminiProvider(LLMProvider):
    """
    Google Gemini AIプロバイダー
    """
    
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash", **kwargs):
        """
        Args:
            api_key: Google AI API Key
            model_name: Geminiモデル名 (gemini-2.5-flash, gemini-2.5-pro等)
            **kwargs: その他の設定パラメータ
        """
        super().__init__(api_key, **kwargs)
        self.model_name = model_name
        
    def initialize(self) -> None:
        """
        Geminiクライアントの初期化
        """
        try:
            # Google AI API設定
            genai.configure(api_key=self.api_key)
            
            # モデルの準備
            self._client = genai.GenerativeModel(self.model_name)
            
            logger.info(f"Geminiクライアントが正常に初期化されました: {self.model_name}")
            
        except Exception as e:
            logger.error(f"Geminiクライアントの初期化に失敗しました: {str(e)}")
            raise
    
    def generate_content(
        self,
        prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 2048,
        **kwargs
    ) -> LLMResponse:
        """
        Geminiでコンテンツを生成
        
        Args:
            prompt: 生成用プロンプト
            temperature: ランダム性パラメータ (0.0-1.0)
            max_tokens: 最大出力トークン数
            **kwargs: Gemini固有のパラメータ
            
        Returns:
            LLMResponse: 生成されたコンテンツ
            
        Raises:
            Exception: 生成に失敗した場合
        """
        if not self.is_initialized():
            raise ValueError("Geminiプロバイダーが初期化されていません")
        
        try:
            # Gemini生成設定
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                **kwargs
            )
            
            # コンテンツ生成
            response = self._client.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            # レスポンス解析
            content = response.text if response.text else ""
            
            # 使用量情報の取得（可能な場合）
            usage_info = None
            if hasattr(response, 'usage_metadata'):
                usage_info = {
                    "prompt_tokens": getattr(response.usage_metadata, 'prompt_token_count', None),
                    "completion_tokens": getattr(response.usage_metadata, 'candidates_token_count', None),
                    "total_tokens": getattr(response.usage_metadata, 'total_token_count', None)
                }
            
            # 終了理由の取得
            finish_reason = None
            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                if hasattr(candidate, 'finish_reason'):
                    finish_reason = str(candidate.finish_reason)
            
            return LLMResponse(
                content=content,
                usage_info=usage_info,
                model=self.model_name,
                finish_reason=finish_reason
            )
            
        except Exception as e:
            logger.error(f"Geminiコンテンツ生成エラー: {str(e)}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Geminiモデル情報を取得
        
        Returns:
            Dict[str, Any]: モデル情報
        """
        return {
            "provider": self.provider_name,
            "model": self.model_name,
            "version": "2.5",
            "supports_streaming": True,
            "max_tokens": 8192,  # モデルによって異なるが一般的な値
            "context_window": 1048576 if "pro" in self.model_name else 32768
        }
    
    @property
    def provider_name(self) -> str:
        """プロバイダー名"""
        return "gemini"
    
    def _extract_json_from_response(self, response_text: str) -> str:
        """
        レスポンステキストからJSONを抽出（Gemini特有の処理）
        
        Args:
            response_text: Geminiからのレスポンステキスト
            
        Returns:
            str: 抽出されたJSON文字列
        """
        response_text = response_text.strip()
        
        # JSONブロック記法の除去
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        return response_text.strip()