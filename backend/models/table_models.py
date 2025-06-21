"""
表検出関連のデータモデル
"""

from typing import Optional, List, Dict, Any
import pandas as pd
import openpyxl


class TableCandidate:
    """検出された表の候補を表すクラス"""

    def __init__(
        self,
        table_id: str,
        sheet_name: str,
        start_row: int,
        end_row: int,
        start_col: int,
        end_col: int,
        header_row: Optional[int] = None,
        quality_score: float = 0.0,
        data_density: float = 0.0,
        row_count: int = 0,
        col_count: int = 0,
        estimated_records: int = 0,
        headers: Optional[List[str]] = None,
        sample_data: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.table_id = table_id
        self.sheet_name = sheet_name
        self.start_row = start_row
        self.end_row = end_row
        self.start_col = start_col
        self.end_col = end_col
        self.header_row = header_row
        self.quality_score = quality_score
        self.data_density = data_density
        self.row_count = row_count
        self.col_count = col_count
        self.estimated_records = estimated_records
        self.headers = headers or []
        self.sample_data = sample_data or []
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "table_id": self.table_id,
            "sheet_name": self.sheet_name,
            "range": {
                "start_row": self.start_row,
                "end_row": self.end_row,
                "start_col": self.start_col,
                "end_col": self.end_col,
                "excel_range": f"{openpyxl.utils.get_column_letter(self.start_col)}{self.start_row}:{openpyxl.utils.get_column_letter(self.end_col)}{self.end_row}",
            },
            "header_row": self.header_row,
            "quality_score": round(self.quality_score, 3),
            "data_density": round(self.data_density, 3),
            "dimensions": {
                "row_count": self.row_count,
                "col_count": self.col_count,
                "estimated_records": self.estimated_records,
            },
            "headers": self.headers,
            "sample_data": self.sample_data,
            "metadata": self.metadata,
        }


class SessionData:
    """セッションデータを管理するクラス"""

    def __init__(self):
        self.raw_data: Optional[pd.DataFrame] = None
        self.processed_data: Optional[pd.DataFrame] = None
        self.analysis_result: Dict[str, Any] = {}
        self.metadata: Dict[str, Any] = {}
        self.file_info: Dict[str, Any] = {}
