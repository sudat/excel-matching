"""
セッション管理
"""

from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
import logging

from models.table_models import SessionData

logger = logging.getLogger(__name__)


class SessionManager:
    """セッション管理クラス"""

    def __init__(self, timeout_minutes: int = 30):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.timestamps: Dict[str, datetime] = {}
        self.timeout = timedelta(minutes=timeout_minutes)

    def cleanup_expired_sessions(self) -> int:
        """期限切れのセッションをクリーンアップ"""
        current_time = datetime.now()
        expired_sessions = []

        for session_id, timestamp in self.timestamps.items():
            if current_time - timestamp > self.timeout:
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            if session_id in self.sessions:
                del self.sessions[session_id]
            if session_id in self.timestamps:
                del self.timestamps[session_id]
            logger.info(f"Expired session cleaned up: {session_id}")

        return len(expired_sessions)

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """セッションデータを取得"""
        self.cleanup_expired_sessions()

        if session_id not in self.sessions:
            return None

        # アクセス時刻を更新
        self.timestamps[session_id] = datetime.now()
        return self.sessions[session_id]

    def get_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """セッションデータを取得（エイリアス）"""
        return self.get_session(session_id)
    
    def save_session_data(self, session_id: str, data: Dict[str, Any]) -> bool:
        """セッションデータを保存"""
        if session_id not in self.sessions:
            return False
        
        self.sessions[session_id].update(data)
        self.timestamps[session_id] = datetime.now()  # アクセス時刻を更新
        
        logger.info(f"Session data updated: {session_id}")
        return True

    def create_session(self, session_id: str) -> Dict[str, Any]:
        """新しいセッションを作成"""
        self.cleanup_expired_sessions()

        self.sessions[session_id] = {
            "raw_data": None,
            "processed_data": None,
            "analysis_result": {},
            "metadata": {},
            "file_info": {},
        }
        self.timestamps[session_id] = datetime.now()
        return self.sessions[session_id]

    def delete_session(self, session_id: str) -> bool:
        """セッションを削除"""
        deleted = False
        if session_id in self.sessions:
            del self.sessions[session_id]
            deleted = True
        if session_id in self.timestamps:
            del self.timestamps[session_id]

        if deleted:
            logger.info(f"Session deleted: {session_id}")
        return deleted

    def list_active_sessions(self) -> List[Dict[str, Any]]:
        """アクティブなセッション一覧を取得"""
        self.cleanup_expired_sessions()

        sessions_info = []
        for session_id, timestamp in self.timestamps.items():
            session = self.sessions.get(session_id, {})
            file_info = session.get("file_info", {})

            sessions_info.append(
                {
                    "session_id": session_id,
                    "created_at": timestamp.isoformat(),
                    "filename": file_info.get("filename", "Unknown"),
                    "file_type": file_info.get("file_type", "Unknown"),
                    "total_rows": file_info.get("total_rows", 0),
                    "total_columns": file_info.get("total_columns", 0),
                    "total_sheets": file_info.get("total_sheets", 0),
                }
            )

        return sessions_info

    def get_current_time(self) -> datetime:
        """現在時刻を取得"""
        return datetime.now()
