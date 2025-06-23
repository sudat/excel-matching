"""
LLMプロバイダーの抽象基底クラス
複数のAIモデル（Gemini、OpenAI等）の統一インターフェースを提供
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """
    LLMからのレスポンスを統一的に表現するデータクラス
    """
    content: str
    usage_info: Optional[Dict[str, Any]] = None
    model: Optional[str] = None
    finish_reason: Optional[str] = None
    
    
class LLMProvider(ABC):
    """
    LLMプロバイダーの抽象基底クラス
    各AIモデル（Gemini、OpenAI等）の具象クラスはこのインターフェースを実装
    """
    
    def __init__(self, api_key: str, **kwargs):
        """
        Args:
            api_key: APIキー
            **kwargs: プロバイダー固有の設定パラメータ
        """
        self.api_key = api_key
        self.config = kwargs
        self._client = None
    
    @abstractmethod
    def initialize(self) -> None:
        """
        プロバイダーの初期化
        クライアントの設定や認証を行う
        """
        pass
    
    @abstractmethod
    def generate_content(
        self,
        prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 2048,
        **kwargs
    ) -> LLMResponse:
        """
        プロンプトに基づいてコンテンツを生成
        
        Args:
            prompt: 生成用プロンプト
            temperature: ランダム性パラメータ (0.0-1.0)
            max_tokens: 最大出力トークン数
            **kwargs: プロバイダー固有のパラメータ
            
        Returns:
            LLMResponse: 生成されたコンテンツとメタデータ
            
        Raises:
            Exception: 生成に失敗した場合
        """
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        使用しているモデルの情報を取得
        
        Returns:
            Dict[str, Any]: モデル情報
        """
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """プロバイダー名を返す"""
        pass
    
    def is_initialized(self) -> bool:
        """
        プロバイダーが初期化済みかどうか確認
        
        Returns:
            bool: 初期化済みの場合True
        """
        return self._client is not None
    
    def validate_response(self, response: LLMResponse) -> bool:
        """
        レスポンスの妥当性を検証
        
        Args:
            response: 検証対象のレスポンス
            
        Returns:
            bool: 妥当な場合True
        """
        if not response or not response.content:
            logger.warning(f"{self.provider_name}: 空のレスポンスが返されました")
            return False
        
        if len(response.content.strip()) == 0:
            logger.warning(f"{self.provider_name}: 空白のみのレスポンスが返されました")
            return False
        
        return True