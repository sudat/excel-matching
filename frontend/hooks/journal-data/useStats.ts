import { useCallback, useEffect } from "react";
import { useJournalDataContext } from "@/lib/journal-data/store";
import { setStatsData, setStatsLoading, setError } from "@/lib/journal-data/store";
import { journalDataAPI } from "@/lib/journal-data/api";
import type { JournalDataStats } from "@/lib/journal-data/types";

export const useStats = () => {
  const { state, dispatch } = useJournalDataContext();

  const loadStats = useCallback(async () => {
    dispatch(setStatsLoading(true));
    try {
      const result = await journalDataAPI.getStats();
      dispatch(setStatsData(result.stats));
    } catch (error) {
      dispatch(
        setError(error instanceof Error ? error.message : "統計情報取得エラー")
      );
    } finally {
      dispatch(setStatsLoading(false));
    }
  }, [dispatch]);

  const refreshStats = useCallback(() => {
    loadStats();
  }, [loadStats]);

  // 統計タブがアクティブになったときに自動でデータを取得
  useEffect(() => {
    if (state.activeTab === "stats") {
      loadStats();
    }
  }, [state.activeTab, loadStats]);

  return {
    // State
    statsData: state.stats?.statsData || null,
    statsLoading: state.stats?.statsLoading || false,
    error: state.error,

    // Actions
    loadStats,
    refreshStats,
  };
};
