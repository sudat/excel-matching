import { useCallback } from "react";
import { useJournalDataContext } from "../store";
import {
  setSelectedFiles,
  setError,
  setUploading,
  setUploadProgress,
  setUploadResult,
  setShowOverwriteDialog,
  setPendingOverwriteData,
} from "../store";
import { journalDataAPI } from "../services/api";
import { isValidFileType, isValidFileSize } from "../utils/formatters";

export const useFileUpload = () => {
  const { state, dispatch } = useJournalDataContext();

  const validateFiles = useCallback((files: File[]): string | null => {
    if (files.length === 0) {
      return "ファイルを選択してください";
    }

    for (const file of files) {
      if (!isValidFileType(file)) {
        return `サポートされていないファイル形式です: ${file.name}`;
      }
      if (!isValidFileSize(file)) {
        return `ファイルサイズが大きすぎます: ${file.name}`;
      }
    }

    return null;
  }, []);

  const handleFileSelect = useCallback((files: File[]) => {
    const validationError = validateFiles(files);
    if (validationError) {
      dispatch(setError(validationError));
      return;
    }

    dispatch(setSelectedFiles(files));
    dispatch(setError(null));
  }, [dispatch, validateFiles]);

  const handleDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
  }, []);

  const handleDrop = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    const files = Array.from(event.dataTransfer.files);
    handleFileSelect(files);
  }, [handleFileSelect]);

  const uploadFiles = useCallback(async (forceOverwrite = false) => {
    const validationError = validateFiles(state.upload.selectedFiles);
    if (validationError) {
      dispatch(setError(validationError));
      return;
    }

    dispatch(setUploading(true));
    dispatch(setError(null));
    dispatch(setUploadResult(null));
    dispatch(setUploadProgress(0));

    try {
      // 進捗シミュレーション
      let currentProgress = 0;
      const progressInterval = setInterval(() => {
        currentProgress = Math.min(currentProgress + 10, 90);
        dispatch(setUploadProgress(currentProgress));
      }, 500);

      const result = await journalDataAPI.uploadJournalData(
        state.upload.selectedFiles,
        state.upload.fiscalYear,
        state.upload.fiscalMonth,
        forceOverwrite
      );

      clearInterval(progressInterval);
      dispatch(setUploadProgress(100));

      // 既存データがある場合は上書き確認を表示
      if (result.data_exists && !forceOverwrite) {
        const formData = new FormData();
        formData.append("fiscal_year", state.upload.fiscalYear.toString());
        formData.append("fiscal_month", state.upload.fiscalMonth.toString());
        formData.append("overwrite", "true");
        state.upload.selectedFiles.forEach((file) => {
          formData.append("files", file);
        });

        dispatch(setShowOverwriteDialog(true));
        dispatch(setPendingOverwriteData(formData));
        dispatch(setUploading(false));
        dispatch(setUploadProgress(0));
        return;
      }

      dispatch(setUploadResult(result));
      dispatch(setSelectedFiles([]));

    } catch (error) {
      dispatch(setError(
        error instanceof Error ? error.message : "アップロード中にエラーが発生しました"
      ));
    } finally {
      dispatch(setUploading(false));
      setTimeout(() => dispatch(setUploadProgress(0)), 2000);
    }
  }, [state.upload, dispatch]);

  const handleOverwriteConfirm = useCallback(async () => {
    dispatch(setShowOverwriteDialog(false));
    if (state.upload.pendingOverwriteData) {
      await uploadFiles(true);
      dispatch(setPendingOverwriteData(null));
    }
  }, [state.upload.pendingOverwriteData, dispatch, uploadFiles]);

  const handleOverwriteCancel = useCallback(() => {
    dispatch(setShowOverwriteDialog(false));
    dispatch(setPendingOverwriteData(null));
    dispatch(setUploadProgress(0));
  }, [dispatch]);

  return {
    // State
    selectedFiles: state.upload.selectedFiles,
    fiscalYear: state.upload.fiscalYear,
    fiscalMonth: state.upload.fiscalMonth,
    isUploading: state.upload.isUploading,
    uploadProgress: state.upload.uploadProgress,
    uploadResult: state.upload.uploadResult,
    showOverwriteDialog: state.upload.showOverwriteDialog,
    error: state.error,

    // Actions
    handleFileSelect,
    handleDragOver,
    handleDrop,
    uploadFiles,
    handleOverwriteConfirm,
    handleOverwriteCancel,
  };
};