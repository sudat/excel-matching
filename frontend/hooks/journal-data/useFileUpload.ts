import { useCallback, useRef } from "react";
import { useJournalDataContext } from "@/lib/journal-data/store";
import {
  setSelectedFiles,
  setError,
  setUploading,
  setUploadProgress,
  setUploadResult,
  setShowOverwriteDialog,
  setPendingOverwriteData,
} from "@/lib/journal-data/store";
import { journalDataAPI } from "@/lib/journal-data/api";
import {
  isValidFileType,
  isValidFileSize,
} from "@/lib/journal-data/formatters";

export const useFileUpload = () => {
  const { state, dispatch } = useJournalDataContext();
  const fileInputRef = useRef<HTMLInputElement>(null);

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

  const clearPreviousResults = useCallback(() => {
    // 新しいファイル選択時に前回の結果をクリア
    if (state.upload.uploadResult) {
      dispatch(setUploadResult(null));
    }
    if (state.error) {
      dispatch(setError(null));
    }
  }, [state.upload.uploadResult, state.error, dispatch]);

  const resetFileInput = useCallback(() => {
    // input要素の値をリセット（同じファイルの再選択を可能にする）
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }, []);

  const handleFileSelect = useCallback(
    (files: File[]) => {
      const validationError = validateFiles(files);
      if (validationError) {
        dispatch(setError(validationError));
        return;
      }

      // 新しいファイル選択時に前回の結果をクリア
      clearPreviousResults();

      dispatch(setSelectedFiles(files));
      dispatch(setError(null));
    },
    [dispatch, validateFiles, clearPreviousResults]
  );

  const handleDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
  }, []);

  const handleDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();
      const files = Array.from(event.dataTransfer.files);
      handleFileSelect(files);
    },
    [handleFileSelect]
  );

  const uploadFiles = useCallback(
    async (forceOverwrite = false) => {
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

        // アップロード成功時のクリーンアップ
        dispatch(setUploadResult(result));
        dispatch(setSelectedFiles([]));
        resetFileInput(); // input要素をリセット
      } catch (error) {
        dispatch(
          setError(
            error instanceof Error
              ? error.message
              : "アップロード中にエラーが発生しました"
          )
        );
      } finally {
        dispatch(setUploading(false));
        setTimeout(() => dispatch(setUploadProgress(0)), 2000);
      }
    },
    [state.upload, dispatch, resetFileInput]
  );

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

    // Refs
    fileInputRef,
  };
};
