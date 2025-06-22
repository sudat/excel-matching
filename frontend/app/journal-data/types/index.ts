export interface JournalEntry {
  id: string;
  entry_date: string;
  amount: number;
  person: string;
  category: string;
  description: string;
  account_code?: string;
  department?: string;
  sub_account?: string;
  partner?: string;
  detail_description?: string;
  source_file: string;
  registered_at: string;
}

export interface JournalDataUploadResponse {
  status: string;
  message: string;
  processed_count: number;
  failed_count: number;
  pinecone_index_name: string;
  details?: any;
  data_exists?: boolean;
  existing_count?: number;
}

export interface JournalDataListResponse {
  total_count: number;
  data: JournalEntry[];
  date_range: {
    from: string;
    to: string;
  };
}

export interface HistoryItem {
  id: string;
  timestamp: string;
  action: string;
  user_id: string;
  details: any;
  result: string;
  description: string;
}

export interface HistoryResponse {
  status: string;
  total_count: number;
  history: HistoryItem[];
  pagination: {
    limit: number;
    offset: number;
    has_more: boolean;
  };
}

export interface MonthlyStats {
  period: string;
  year: number;
  month: number;
  count: number;
  total_amount: number;
}

export interface CategoryStats {
  category: string;
  count: number;
  total_amount: number;
}

export interface PersonStats {
  person: string;
  count: number;
  total_amount: number;
}

export interface AmountStats {
  total: number;
  average: number;
  max: number;
  min: number;
  count: number;
}

export interface StatsSummary {
  total_amount: number;
  total_entries: number;
  unique_categories: number;
  unique_persons: number;
  active_months: number;
}

export interface JournalDataStats {
  total_entries: number;
  last_updated: string;
  date_range: {
    from: string | null;
    to: string | null;
  };
  amount_stats: AmountStats;
  monthly_breakdown: MonthlyStats[];
  category_breakdown: CategoryStats[];
  person_breakdown: PersonStats[];
  summary: StatsSummary;
}

export interface StatsResponse {
  status: string;
  stats: JournalDataStats;
}
