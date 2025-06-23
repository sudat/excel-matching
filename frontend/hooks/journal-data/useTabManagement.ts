import { useCallback } from "react";
import { useJournalDataContext } from "@/lib/journal-data/store";
import { setActiveTab, setFiscalYear, setFiscalMonth } from "@/lib/journal-data/store";

export const useTabManagement = () => {
  const { state, dispatch } = useJournalDataContext();

  const handleTabChange = useCallback((tab: string) => {
    dispatch(setActiveTab(tab));
  }, [dispatch]);

  const handleFiscalYearChange = useCallback((year: number) => {
    dispatch(setFiscalYear(year));
  }, [dispatch]);

  const handleFiscalMonthChange = useCallback((month: number) => {
    dispatch(setFiscalMonth(month));
  }, [dispatch]);

  return {
    // State
    activeTab: state.activeTab,
    fiscalYear: state.upload.fiscalYear,
    fiscalMonth: state.upload.fiscalMonth,

    // Actions
    handleTabChange,
    handleFiscalYearChange,
    handleFiscalMonthChange,
  };
};