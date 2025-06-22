import { useCallback, useEffect } from "react";
import { useJournalDataContext } from "../store";
import {
  setHistoryData,
  setHistoryLoading,
  setHistoryTotalCount,
  setError,
} from "../store";
import { journalDataAPI } from "../services/api";

export const useOperationHistory = () => {
  const { state, dispatch } = useJournalDataContext();

  const loadHistoryData = useCallback(async (limit = 50, offset = 0) => {
    dispatch(setHistoryLoading(true));
    try {
      const result = await journalDataAPI.getOperationHistory(limit, offset);
      dispatch(setHistoryData(result.history));
      dispatch(setHistoryTotalCount(result.total_count));
    } catch (error) {
      dispatch(setError(
        error instanceof Error ? error.message : "履歴データ取得エラー"
      ));
    } finally {
      dispatch(setHistoryLoading(false));
    }
  }, [dispatch]);

  const refreshHistory = useCallback(() => {
    loadHistoryData();
  }, [loadHistoryData]);

  // 履歴タブがアクティブになったときに自動でデータを取得
  useEffect(() => {
    if (state.activeTab === "history") {
      loadHistoryData();
    }
  }, [state.activeTab, loadHistoryData]);

  return {
    // State
    historyData: state.history.historyData,
    historyLoading: state.history.historyLoading,
    historyTotalCount: state.history.historyTotalCount,
    error: state.error,

    // Actions
    loadHistoryData,
    refreshHistory,
  };
};