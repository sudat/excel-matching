/**
 * 通貨フォーマット
 */
export const formatCurrency = (amount: number): string => {
  return new Intl.NumberFormat("ja-JP", {
    style: "currency",
    currency: "JPY",
  }).format(amount);
};

/**
 * 日付フォーマット（日本語形式）
 */
export const formatDate = (dateString: string): string => {
  return new Date(dateString).toLocaleDateString("ja-JP");
};

/**
 * 日時フォーマット（日本語形式）
 */
export const formatDateTime = (dateString: string): string => {
  return new Date(dateString).toLocaleString("ja-JP");
};

/**
 * ファイルサイズフォーマット
 */
export const formatFileSize = (bytes: number): string => {
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  if (bytes === 0) return '0 Bytes';
  
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
};

/**
 * アクション表示名の取得
 */
export const getActionDisplayName = (action: string): string => {
  switch (action) {
    case "JOURNAL_DATA_UPLOAD":
      return "データ登録";
    case "JOURNAL_DATA_DELETE":
      return "データ削除";
    case "JOURNAL_DATA_UPDATE":
      return "データ更新";
    default:
      return action;
  }
};

/**
 * アクションバッジカラーの取得
 */
export const getActionBadgeColor = (action: string): string => {
  switch (action) {
    case "JOURNAL_DATA_UPLOAD":
      return "bg-green-100 text-green-800";
    case "JOURNAL_DATA_DELETE":
      return "bg-red-100 text-red-800";
    case "JOURNAL_DATA_UPDATE":
      return "bg-blue-100 text-blue-800";
    default:
      return "bg-gray-100 text-gray-800";
  }
};

/**
 * ファイル拡張子の検証
 */
export const isValidFileType = (file: File): boolean => {
  const validTypes = [
    'text/csv',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
  ];
  const validExtensions = ['.csv', '.xls', '.xlsx'];
  
  return validTypes.includes(file.type) || 
         validExtensions.some(ext => file.name.toLowerCase().endsWith(ext));
};

/**
 * ファイルサイズの検証
 */
export const isValidFileSize = (file: File, maxSizeMB = 10): boolean => {
  const maxSizeBytes = maxSizeMB * 1024 * 1024;
  return file.size <= maxSizeBytes;
};