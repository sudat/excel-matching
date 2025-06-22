import type { JournalDataState, JournalDataAction } from "./types";

// 初期状態
export const initialState: JournalDataState = {
  // UI状態
  activeTab: "upload",
  error: null,

  // アップロード関連状態
  upload: {
    selectedFiles: [],
    fiscalYear: new Date().getFullYear(),
    fiscalMonth: new Date().getMonth() + 1,
    isUploading: false,
    uploadProgress: 0,
    uploadResult: null,
    showOverwriteDialog: false,
    pendingOverwriteData: null,
  },

  // データ一覧関連状態
  dataList: {
    journalData: [],
    totalCount: 0,
    isLoading: false,
    searchTerm: "",
    dateFilter: "",
  },

  // 操作履歴関連状態
  history: {
    historyData: [],
    historyLoading: false,
    historyTotalCount: 0,
  },

  // 統計情報関連状態
  stats: {
    statsData: null,
    statsLoading: false,
  },
};

// Reducer関数
export function journalDataReducer(
  state: JournalDataState,
  action: JournalDataAction
): JournalDataState {
  switch (action.type) {
    // UI Actions
    case "SET_ACTIVE_TAB":
      return {
        ...state,
        activeTab: action.payload,
      };

    case "SET_ERROR":
      return {
        ...state,
        error: action.payload,
      };

    // Upload Actions
    case "SET_SELECTED_FILES":
      return {
        ...state,
        upload: {
          ...state.upload,
          selectedFiles: action.payload,
        },
      };

    case "SET_FISCAL_YEAR":
      return {
        ...state,
        upload: {
          ...state.upload,
          fiscalYear: action.payload,
        },
      };

    case "SET_FISCAL_MONTH":
      return {
        ...state,
        upload: {
          ...state.upload,
          fiscalMonth: action.payload,
        },
      };

    case "SET_UPLOADING":
      return {
        ...state,
        upload: {
          ...state.upload,
          isUploading: action.payload,
        },
      };

    case "SET_UPLOAD_PROGRESS":
      return {
        ...state,
        upload: {
          ...state.upload,
          uploadProgress: action.payload,
        },
      };

    case "SET_UPLOAD_RESULT":
      return {
        ...state,
        upload: {
          ...state.upload,
          uploadResult: action.payload,
        },
      };

    case "SET_SHOW_OVERWRITE_DIALOG":
      return {
        ...state,
        upload: {
          ...state.upload,
          showOverwriteDialog: action.payload,
        },
      };

    case "SET_PENDING_OVERWRITE_DATA":
      return {
        ...state,
        upload: {
          ...state.upload,
          pendingOverwriteData: action.payload,
        },
      };

    case "RESET_UPLOAD_STATE":
      return {
        ...state,
        upload: {
          ...state.upload,
          selectedFiles: [],
          isUploading: false,
          uploadProgress: 0,
          uploadResult: null,
          showOverwriteDialog: false,
          pendingOverwriteData: null,
        },
      };

    // Data List Actions
    case "SET_JOURNAL_DATA":
      return {
        ...state,
        dataList: {
          ...state.dataList,
          journalData: action.payload,
        },
      };

    case "SET_TOTAL_COUNT":
      return {
        ...state,
        dataList: {
          ...state.dataList,
          totalCount: action.payload,
        },
      };

    case "SET_DATA_LOADING":
      return {
        ...state,
        dataList: {
          ...state.dataList,
          isLoading: action.payload,
        },
      };

    case "SET_SEARCH_TERM":
      return {
        ...state,
        dataList: {
          ...state.dataList,
          searchTerm: action.payload,
        },
      };

    case "SET_DATE_FILTER":
      return {
        ...state,
        dataList: {
          ...state.dataList,
          dateFilter: action.payload,
        },
      };

    // History Actions
    case "SET_HISTORY_DATA":
      return {
        ...state,
        history: {
          ...state.history,
          historyData: action.payload,
        },
      };

    case "SET_HISTORY_LOADING":
      return {
        ...state,
        history: {
          ...state.history,
          historyLoading: action.payload,
        },
      };

    case "SET_HISTORY_TOTAL_COUNT":
      return {
        ...state,
        history: {
          ...state.history,
          historyTotalCount: action.payload,
        },
      };

    // Stats Actions
    case "SET_STATS_DATA":
      return {
        ...state,
        stats: {
          ...state.stats,
          statsData: action.payload,
        },
      };

    case "SET_STATS_LOADING":
      return {
        ...state,
        stats: {
          ...state.stats,
          statsLoading: action.payload,
        },
      };

    default:
      return state;
  }
}
