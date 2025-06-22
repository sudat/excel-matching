import { useCallback, useEffect } from "react";
import { useJournalDataContext } from "../store";
import {
  setJournalData,
  setTotalCount,
  setDataLoading,
  setSearchTerm,
  setDateFilter,
  setError,
} from "../store";
import { journalDataAPI } from "../services/api";

export const useJournalDataList = () => {
  const { state, dispatch } = useJournalDataContext();

  const loadJournalData = useCallback(async () => {
    dispatch(setDataLoading(true));
    try {
      const result = await journalDataAPI.getJournalData(
        state.dataList.searchTerm || undefined,
        state.dataList.dateFilter || undefined
      );
      
      dispatch(setJournalData(result.data));
      dispatch(setTotalCount(result.total_count));
    } catch (error) {
      dispatch(setError(
        error instanceof Error ? error.message : "データ取得エラー"
      ));
    } finally {
      dispatch(setDataLoading(false));
    }
  }, [state.dataList.searchTerm, state.dataList.dateFilter, dispatch]);

  const handleDelete = useCallback(async (entryId: string) => {
    if (!confirm("この仕訳データを削除しますか？")) return;

    try {
      await journalDataAPI.deleteJournalEntry(entryId);
      await loadJournalData();
    } catch (error) {
      dispatch(setError(
        error instanceof Error ? error.message : "削除エラー"
      ));
    }
  }, [loadJournalData, dispatch]);

  const handleSearch = useCallback((term: string) => {
    dispatch(setSearchTerm(term));
  }, [dispatch]);

  const handleDateFilter = useCallback((filter: string) => {
    dispatch(setDateFilter(filter));
  }, [dispatch]);

  // 検索条件が変更されたときに自動でデータを再取得
  useEffect(() => {
    if (state.activeTab === "list") {
      loadJournalData();
    }
  }, [state.activeTab, state.dataList.searchTerm, state.dataList.dateFilter, loadJournalData]);

  return {
    // State
    journalData: state.dataList.journalData,
    totalCount: state.dataList.totalCount,
    isLoading: state.dataList.isLoading,
    searchTerm: state.dataList.searchTerm,
    dateFilter: state.dataList.dateFilter,
    error: state.error,

    // Actions
    loadJournalData,
    handleDelete,
    handleSearch,
    handleDateFilter,
  };
};