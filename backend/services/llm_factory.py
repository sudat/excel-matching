"""
LLMプロバイダーファクトリー
環境変数に基づいて適切なLLMプロバイダーを動的に生成
"""

import os
import logging
from typing import Dict, Any, Optional
from .llm_providers import LLMProvider, GeminiProvider, OpenAIProvider

logger = logging.getLogger(__name__)


class LLMFactory:
    """
    LLMプロバイダーファクトリークラス
    環境変数の設定に基づいて適切なプロバイダーを生成
    """
    
    # サポートされているプロバイダー
    SUPPORTED_PROVIDERS = {
        "gemini": {
            "class": GeminiProvider,
            "api_key_names": ["GOOGLE_API_KEY", "GOOGLE_AI_API_KEY", "GEMINI_API_KEY"],
            "default_models": {
                "flash": "gemini-2.5-flash",
                "pro": "gemini-2.5-pro"
            }
        },
        "openai": {
            "class": OpenAIProvider,
            "api_key_names": ["OPENAI_API_KEY"],
            "default_models": {
                "mini": "o4-mini",
                "high": "o4-mini-high",
                "standard": "gpt-4o",
                "turbo": "gpt-4-turbo"
            }
        }
    }
    
    @classmethod
    def create_provider(
        self,
        provider_name: Optional[str] = None,
        model_variant: Optional[str] = None,
        **kwargs
    ) -> LLMProvider:
        """
        LLMプロバイダーを作成
        
        Args:
            provider_name: プロバイダー名 (環境変数から自動取得可能)
            model_variant: モデルのバリエーション (flash, pro, mini等)
            **kwargs: プロバイダー固有の追加設定
            
        Returns:
            LLMProvider: 初期化済みのプロバイダーインスタンス
            
        Raises:
            ValueError: サポートされていないプロバイダーまたはAPIキーが見つからない場合
        """
        # 環境変数からプロバイダー名を取得（未指定の場合）
        if provider_name is None:
            provider_name = os.getenv("AI_MODEL_PROVIDER", "gemini").lower()
        
        # プロバイダーのサポート確認
        if provider_name not in self.SUPPORTED_PROVIDERS:
            raise ValueError(
                f"サポートされていないプロバイダー: {provider_name}. "
                f"サポート対象: {list(self.SUPPORTED_PROVIDERS.keys())}"
            )
        
        provider_config = self.SUPPORTED_PROVIDERS[provider_name]
        
        # APIキーの取得
        api_key = self._get_api_key(provider_config["api_key_names"])
        if not api_key:
            raise ValueError(
                f"{provider_name} プロバイダーのAPIキーが見つかりません. "
                f"以下の環境変数のいずれかを設定してください: {provider_config['api_key_names']}"
            )
        
        # モデル名の決定
        model_name = self._determine_model_name(provider_name, model_variant, **kwargs)
        
        # プロバイダーの生成と初期化
        provider_class = provider_config["class"]
        provider = provider_class(api_key=api_key, model_name=model_name, **kwargs)
        provider.initialize()
        
        logger.info(f"LLMプロバイダーが正常に作成されました: {provider_name}/{model_name}")
        
        return provider
    
    @classmethod
    def _get_api_key(cls, api_key_names: list) -> Optional[str]:
        """
        環境変数からAPIキーを取得
        
        Args:
            api_key_names: 候補となる環境変数名のリスト
            
        Returns:
            str: APIキー（見つからない場合はNone）
        """
        for key_name in api_key_names:
            api_key = os.getenv(key_name)
            if api_key:
                return api_key
        return None
    
    @classmethod
    def _determine_model_name(
        cls,
        provider_name: str,
        model_variant: Optional[str],
        **kwargs
    ) -> str:
        """
        モデル名を決定
        
        Args:
            provider_name: プロバイダー名
            model_variant: モデルのバリエーション
            **kwargs: 追加設定（model_nameの直接指定等）
            
        Returns:
            str: 決定されたモデル名
        """
        # 直接指定されている場合はそれを使用
        if "model_name" in kwargs:
            return kwargs["model_name"]
        
        # 環境変数から取得
        env_model = os.getenv("AI_MODEL_NAME")
        if env_model:
            return env_model
        
        # バリエーション指定がある場合
        provider_config = cls.SUPPORTED_PROVIDERS[provider_name]
        default_models = provider_config["default_models"]
        
        if model_variant and model_variant in default_models:
            return default_models[model_variant]
        
        # デフォルトモデルを選択
        if provider_name == "gemini":
            return default_models["flash"]  # Gemini 2.5 Flash
        elif provider_name == "openai":
            return default_models["high"]   # o4-mini-high
        
        # フォールバック
        return list(default_models.values())[0]
    
    @classmethod
    def get_available_providers(cls) -> Dict[str, Any]:
        """
        利用可能なプロバイダーの情報を取得
        
        Returns:
            Dict[str, Any]: プロバイダー情報
        """
        available = {}
        
        for provider_name, config in cls.SUPPORTED_PROVIDERS.items():
            # APIキーの存在確認
            api_key = cls._get_api_key(config["api_key_names"])
            has_api_key = api_key is not None
            
            available[provider_name] = {
                "available": has_api_key,
                "default_models": config["default_models"],
                "required_env_vars": config["api_key_names"]
            }
        
        return available
    
    @classmethod
    def get_current_config(cls) -> Dict[str, Any]:
        """
        現在の設定情報を取得
        
        Returns:
            Dict[str, Any]: 現在の設定
        """
        provider_name = os.getenv("AI_MODEL_PROVIDER", "gemini").lower()
        model_name = os.getenv("AI_MODEL_NAME", "auto")
        
        available_providers = cls.get_available_providers()
        
        return {
            "current_provider": provider_name,
            "current_model": model_name,
            "available_providers": available_providers,
            "environment_variables": {
                "AI_MODEL_PROVIDER": provider_name,
                "AI_MODEL_NAME": model_name
            }
        }