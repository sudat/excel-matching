import type {
  JournalDataAction,
  JournalEntry,
  JournalDataUploadResponse,
  HistoryItem,
  JournalDataStats,
} from "./types";

// UI Action Creators
export const setActiveTab = (tab: string): JournalDataAction => ({
  type: "SET_ACTIVE_TAB",
  payload: tab,
});

export const setError = (error: string | null): JournalDataAction => ({
  type: "SET_ERROR",
  payload: error,
});

// Upload Action Creators
export const setSelectedFiles = (files: File[]): JournalDataAction => ({
  type: "SET_SELECTED_FILES",
  payload: files,
});

export const setFiscalYear = (year: number): JournalDataAction => ({
  type: "SET_FISCAL_YEAR",
  payload: year,
});

export const setFiscalMonth = (month: number): JournalDataAction => ({
  type: "SET_FISCAL_MONTH",
  payload: month,
});

export const setUploading = (isUploading: boolean): JournalDataAction => ({
  type: "SET_UPLOADING",
  payload: isUploading,
});

export const setUploadProgress = (progress: number): JournalDataAction => ({
  type: "SET_UPLOAD_PROGRESS",
  payload: progress,
});

export const setUploadResult = (
  result: JournalDataUploadResponse | null
): JournalDataAction => ({
  type: "SET_UPLOAD_RESULT",
  payload: result,
});

export const setShowOverwriteDialog = (show: boolean): JournalDataAction => ({
  type: "SET_SHOW_OVERWRITE_DIALOG",
  payload: show,
});

export const setPendingOverwriteData = (
  data: FormData | null
): JournalDataAction => ({
  type: "SET_PENDING_OVERWRITE_DATA",
  payload: data,
});

export const resetUploadState = (): JournalDataAction => ({
  type: "RESET_UPLOAD_STATE",
});

// Data List Action Creators
export const setJournalData = (data: JournalEntry[]): JournalDataAction => ({
  type: "SET_JOURNAL_DATA",
  payload: data,
});

export const setTotalCount = (count: number): JournalDataAction => ({
  type: "SET_TOTAL_COUNT",
  payload: count,
});

export const setDataLoading = (isLoading: boolean): JournalDataAction => ({
  type: "SET_DATA_LOADING",
  payload: isLoading,
});

export const setSearchTerm = (term: string): JournalDataAction => ({
  type: "SET_SEARCH_TERM",
  payload: term,
});

export const setDateFilter = (filter: string): JournalDataAction => ({
  type: "SET_DATE_FILTER",
  payload: filter,
});

// History Action Creators
export const setHistoryData = (data: HistoryItem[]): JournalDataAction => ({
  type: "SET_HISTORY_DATA",
  payload: data,
});

export const setHistoryLoading = (isLoading: boolean): JournalDataAction => ({
  type: "SET_HISTORY_LOADING",
  payload: isLoading,
});

export const setHistoryTotalCount = (count: number): JournalDataAction => ({
  type: "SET_HISTORY_TOTAL_COUNT",
  payload: count,
});

// Stats Action Creators
export const setStatsData = (
  data: JournalDataStats | null
): JournalDataAction => ({
  type: "SET_STATS_DATA",
  payload: data,
});

export const setStatsLoading = (isLoading: boolean): JournalDataAction => ({
  type: "SET_STATS_LOADING",
  payload: isLoading,
});
