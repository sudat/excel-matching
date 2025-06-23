export interface UploadResponse {
  status: string;
  message: string;
  business_request_id: string;
  uploaded_files: Array<{
    file_id: string;
    filename: string;
    file_size: number;
    file_type: string;
    storage_path: string;
  }>;
  total_files: number;
}

export interface SheetInfo {
  name: string;
  row_count: number;
  col_count: number;
  has_data: boolean;
  data_range: string | null;
  data_density: number;
  estimated_data_cells: number;
}

export interface ExcelSheetsData {
  sessionId: string;
  filename: string;
  sheets: SheetInfo[];
}