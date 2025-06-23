"""
スキーマ推論サービス
複数のAIモデル（Gemini、OpenAI等）を使用してExcelヘッダーから列マッピングを推論する
"""

import logging
from typing import Dict, List, Any, Optional
import json
import os
from datetime import datetime
from .llm_factory import LLMFactory
from .llm_providers import LLMProvider

logger = logging.getLogger(__name__)


class SchemaInferenceService:
    """
    Excelヘッダーとサンプルデータを分析して、標準仕訳スキーマへの列マッピングを推論するサービス
    複数のAIモデル（Gemini、OpenAI等）に対応
    """

    # 標準仕訳スキーマの列マッピング対象
    TARGET_COLUMNS = {
        "date_column": {
            "description": "日付列（仕訳日付、発生日、支払日等）",
            "examples": ["日付", "仕訳日", "発生日", "支払日", "Date", "取引日", "精算日"],
            "data_types": ["date", "string"]
        },
        "amount_column": {
            "description": "金額列（基準金額、合計金額、税抜金額等）",
            "examples": ["金額", "基準金額", "合計金額", "税抜金額", "Amount", "支払金額", "精算金額"],
            "data_types": ["number", "integer"]
        },
        "person_column": {
            "description": "人物列（精算者、申請者、担当者等）",
            "examples": ["精算者", "申請者", "担当者", "氏名", "Name", "社員名", "従業員名"],
            "data_types": ["string", "category"]
        },
        "category_column": {
            "description": "カテゴリ列（勘定科目、費目、分類等）",
            "examples": ["勘定科目", "費目", "科目", "分類", "Category", "経費種別", "項目"],
            "data_types": ["string", "category"]
        }
    }

    def __init__(self, provider_name: Optional[str] = None, model_variant: Optional[str] = None):
        """LLMプロバイダーを初期化
        
        Args:
            provider_name: プロバイダー名（環境変数から自動取得可能）
            model_variant: モデルのバリエーション（flash, pro, mini等）
        """
        try:
            # LLMプロバイダーの作成
            self.llm_provider = LLMFactory.create_provider(
                provider_name=provider_name,
                model_variant=model_variant
            )
            
            logger.info(f"LLMプロバイダーが正常に初期化されました: {self.llm_provider.provider_name}")
            
        except Exception as e:
            logger.error(f"LLMプロバイダーの初期化に失敗しました: {str(e)}")
            raise

    def infer_schema(
        self, 
        headers: List[str], 
        sample_data: List[List[Any]],
        session_id: str
    ) -> Dict[str, Any]:
        """
        ヘッダーとサンプルデータから列マッピングを推論
        
        Args:
            headers: Excelのヘッダー行
            sample_data: サンプルデータ（最大3行）
            session_id: セッションID（ログ用）
            
        Returns:
            推論結果の辞書
        """
        try:
            logger.info(f"スキーマ推論開始 - セッション: {session_id}, 列数: {len(headers)}")
            
            # プロンプトを生成
            prompt = self._generate_inference_prompt(headers, sample_data)
            
            # LLMに推論を要求
            response = self.llm_provider.generate_content(
                prompt=prompt,
                temperature=0.1,  # 一貫性のために低い温度
                max_tokens=2048
            )
            
            # レスポンスを解析
            result = self._parse_response(response.content)
            
            # ログ出力
            logger.info(f"スキーマ推論完了 - セッション: {session_id}, 信頼度: {result.get('overall_confidence', 0)}")
            
            return result
            
        except Exception as e:
            logger.error(f"スキーマ推論エラー - セッション: {session_id}, エラー: {str(e)}")
            return self._generate_error_response(str(e))

    def _generate_inference_prompt(
        self, 
        headers: List[str], 
        sample_data: List[List[Any]]
    ) -> str:
        """
        LLM用の推論プロンプトを生成
        """
        # サンプルデータのフォーマット
        formatted_sample = ""
        for i, row in enumerate(sample_data[:3]):  # 最大3行
            row_str = [str(cell) if cell is not None else "" for cell in row]
            formatted_sample += f"行{i+1}: {row_str}\n"
        
        # ヘッダーの例示を作成
        example_mapping = {}
        for i, header in enumerate(headers[:4]):  # 最初の4列を例として使用
            example_mapping[f"インデックス{i}"] = f'"{header}"'
        
        prompt = f"""
あなたは経費精算・会計業務の専門家です。Excelファイルのヘッダーとサンプルデータを分析して、
以下の4つの列タイプに最も適した列を特定してください。

**対象列タイプ:**
1. **date_column**: 日付列（仕訳日付、発生日、支払日等）
2. **amount_column**: 金額列（基準金額、合計金額、税抜金額等）
3. **person_column**: 人物列（精算者、申請者、担当者等）
4. **category_column**: カテゴリ列（勘定科目、費目、分類等）

**分析対象データ:**
ヘッダー: {headers}
（インデックス0から{len(headers)-1}まで）

サンプルデータ:
{formatted_sample}

**重要な指示:**
- column_name には**必ず上記ヘッダー配列の実際の値をそのまま**コピーして使用してください
- 例: ヘッダーが["Date", "Amount", "Employee"]なら、column_nameは"Date"、"Amount"、"Employee"を使用
- 日本語・英語・記号問わず、絶対に元のヘッダー名を変更・翻訳・置換しないでください
- 該当する列が見つからない場合のみ null を返してください

**レスポンス形式（JSON）:**
```json
{{
    "mappings": {{
        "date_column": {{
            "column_index": [0から{len(headers)-1}の数値],
            "column_name": "[上記ヘッダー配列の実際の値をそのままコピー]",
            "confidence": [0-100の数値],
            "reasoning": "推論理由"
        }},
        "amount_column": {{
            "column_index": [0から{len(headers)-1}の数値または null],
            "column_name": "[上記ヘッダー配列の実際の値をそのままコピー]",
            "confidence": [0-100の数値],
            "reasoning": "推論理由"
        }},
        "person_column": {{
            "column_index": [0から{len(headers)-1}の数値または null],
            "column_name": "[上記ヘッダー配列の実際の値をそのままコピー]",
            "confidence": [0-100の数値],
            "reasoning": "推論理由"
        }},
        "category_column": {{
            "column_index": [0から{len(headers)-1}の数値または null],
            "column_name": "[上記ヘッダー配列の実際の値をそのままコピー]",
            "confidence": [0-100の数値],
            "reasoning": "推論理由"
        }}
    }},
    "overall_confidence": [0-100の数値],
    "analysis_notes": "分析の全体的な評価"
}}
```

必ずJSON形式で回答してください。```json ```ブロックは不要です。
"""
        return prompt

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """
        LLMのレスポンスを解析してPython辞書に変換
        """
        try:
            # JSONブロックの抽出（念のため）
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            # JSON パース
            result = json.loads(response_text)
            
            # 基本検証
            if "mappings" not in result:
                raise ValueError("mappingsフィールドが見つかりません")
            
            # 各マッピングの検証
            for column_type in self.TARGET_COLUMNS.keys():
                if column_type in result["mappings"]:
                    mapping = result["mappings"][column_type]
                    if mapping is not None:
                        if "column_index" not in mapping or "confidence" not in mapping:
                            logger.warning(f"{column_type}のマッピング情報が不完全です")
            
            # デフォルト値の設定
            result.setdefault("overall_confidence", 50)
            result.setdefault("analysis_notes", "")
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析エラー: {str(e)}")
            logger.error(f"レスポンステキスト: {response_text}")
            return self._generate_error_response(f"JSON解析エラー: {str(e)}")
        
        except Exception as e:
            logger.error(f"レスポンス解析エラー: {str(e)}")
            return self._generate_error_response(f"レスポンス解析エラー: {str(e)}")

    def _generate_error_response(self, error_message: str) -> Dict[str, Any]:
        """
        エラー時のレスポンスを生成
        """
        return {
            "mappings": {
                "date_column": None,
                "amount_column": None,
                "person_column": None,
                "category_column": None
            },
            "overall_confidence": 0,
            "analysis_notes": f"推論エラー: {error_message}",
            "error": True,
            "error_message": error_message
        }

    def validate_mapping_result(self, result: Dict[str, Any]) -> bool:
        """
        推論結果の妥当性を検証
        """
        try:
            if "mappings" not in result:
                return False
            
            mappings = result["mappings"]
            
            # 各必須フィールドの存在確認
            for column_type in self.TARGET_COLUMNS.keys():
                if column_type not in mappings:
                    return False
            
            # インデックスの重複チェック
            used_indices = set()
            for column_type, mapping in mappings.items():
                if mapping is not None and "column_index" in mapping:
                    index = mapping["column_index"]
                    if index in used_indices:
                        logger.warning(f"重複する列インデックス: {index}")
                        return False
                    used_indices.add(index)
            
            return True
            
        except Exception as e:
            logger.error(f"マッピング結果検証エラー: {str(e)}")
            return False

    def get_service_info(self) -> Dict[str, Any]:
        """
        サービス情報を返す
        """
        model_info = self.llm_provider.get_model_info() if self.llm_provider else {}
        
        return {
            "service_name": "SchemaInferenceService",
            "llm_provider": model_info.get("provider", "unknown"),
            "model": model_info.get("model", "unknown"),
            "target_columns": list(self.TARGET_COLUMNS.keys()),
            "version": "2.0.0",
            "initialized": self.llm_provider is not None and self.llm_provider.is_initialized(),
            "model_info": model_info
        }