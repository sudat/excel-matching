import type {
  JournalEntry,
  JournalDataUploadResponse,
  HistoryItem,
  JournalDataStats,
} from "../types";

// 外部から使用する型の再エクスポート
export type {
  JournalEntry,
  JournalDataUploadResponse,
  HistoryItem,
  JournalDataStats,
} from "../types";

// 状態の型定義
export interface JournalDataState {
  // UI状態
  activeTab: string;
  error: string | null;

  // アップロード関連状態
  upload: {
    selectedFiles: File[];
    fiscalYear: number;
    fiscalMonth: number;
    isUploading: boolean;
    uploadProgress: number;
    uploadResult: JournalDataUploadResponse | null;
    showOverwriteDialog: boolean;
    pendingOverwriteData: FormData | null;
  };

  // データ一覧関連状態
  dataList: {
    journalData: JournalEntry[];
    totalCount: number;
    isLoading: boolean;
    searchTerm: string;
    dateFilter: string;
  };

  // 操作履歴関連状態
  history: {
    historyData: HistoryItem[];
    historyLoading: boolean;
    historyTotalCount: number;
  };

  // 統計情報関連状態
  stats: {
    statsData: JournalDataStats | null;
    statsLoading: boolean;
  };
}

// アクションの型定義
export type JournalDataAction =
  // UI Actions
  | { type: "SET_ACTIVE_TAB"; payload: string }
  | { type: "SET_ERROR"; payload: string | null }

  // Upload Actions
  | { type: "SET_SELECTED_FILES"; payload: File[] }
  | { type: "SET_FISCAL_YEAR"; payload: number }
  | { type: "SET_FISCAL_MONTH"; payload: number }
  | { type: "SET_UPLOADING"; payload: boolean }
  | { type: "SET_UPLOAD_PROGRESS"; payload: number }
  | { type: "SET_UPLOAD_RESULT"; payload: JournalDataUploadResponse | null }
  | { type: "SET_SHOW_OVERWRITE_DIALOG"; payload: boolean }
  | { type: "SET_PENDING_OVERWRITE_DATA"; payload: FormData | null }
  | { type: "RESET_UPLOAD_STATE" }

  // Data List Actions
  | { type: "SET_JOURNAL_DATA"; payload: JournalEntry[] }
  | { type: "SET_TOTAL_COUNT"; payload: number }
  | { type: "SET_DATA_LOADING"; payload: boolean }
  | { type: "SET_SEARCH_TERM"; payload: string }
  | { type: "SET_DATE_FILTER"; payload: string }

  // History Actions
  | { type: "SET_HISTORY_DATA"; payload: HistoryItem[] }
  | { type: "SET_HISTORY_LOADING"; payload: boolean }
  | { type: "SET_HISTORY_TOTAL_COUNT"; payload: number }

  // Stats Actions
  | { type: "SET_STATS_DATA"; payload: JournalDataStats | null }
  | { type: "SET_STATS_LOADING"; payload: boolean };
