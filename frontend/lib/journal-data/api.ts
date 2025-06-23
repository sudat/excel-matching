import type {
  JournalDataUploadResponse,
  JournalDataListResponse,
  HistoryResponse,
  StatsResponse,
} from "../types";

const API_BASE_URL =
  process.env.NODE_ENV === "development"
    ? "http://localhost:8000"
    : "http://localhost:8000";

export class JournalDataAPIError extends Error {
  constructor(message: string, public statusCode?: number) {
    super(message);
    this.name = "JournalDataAPIError";
  }
}

class JournalDataAPI {
  private async fetchWithErrorHandling<T>(
    url: string,
    options: RequestInit = {}
  ): Promise<T> {
    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          ...options.headers,
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new JournalDataAPIError(
          errorData.detail || `HTTP Error: ${response.status}`,
          response.status
        );
      }

      return await response.json();
    } catch (error) {
      if (error instanceof JournalDataAPIError) {
        throw error;
      }
      throw new JournalDataAPIError(
        `Network error: ${
          error instanceof Error ? error.message : "Unknown error"
        }`
      );
    }
  }

  async uploadJournalData(
    files: File[],
    fiscalYear: number,
    fiscalMonth: number,
    overwrite = false
  ): Promise<JournalDataUploadResponse> {
    const formData = new FormData();
    formData.append("fiscal_year", fiscalYear.toString());
    formData.append("fiscal_month", fiscalMonth.toString());
    if (overwrite) {
      formData.append("overwrite", "true");
    }

    files.forEach((file) => {
      formData.append("files", file);
    });

    return this.fetchWithErrorHandling<JournalDataUploadResponse>(
      `${API_BASE_URL}/api/register-journal-data`,
      {
        method: "POST",
        body: formData,
      }
    );
  }

  async getJournalData(
    searchTerm?: string,
    dateFilter?: string
  ): Promise<JournalDataListResponse> {
    const params = new URLSearchParams();
    if (searchTerm) params.append("search", searchTerm);
    if (dateFilter) params.append("date_filter", dateFilter);

    const url = `${API_BASE_URL}/api/journal-data${
      params.toString() ? `?${params}` : ""
    }`;
    return this.fetchWithErrorHandling<JournalDataListResponse>(url);
  }

  async deleteJournalEntry(entryId: string): Promise<void> {
    await this.fetchWithErrorHandling<void>(
      `${API_BASE_URL}/api/journal-data/${entryId}`,
      {
        method: "DELETE",
      }
    );
  }

  async getOperationHistory(limit = 50, offset = 0): Promise<HistoryResponse> {
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString(),
    });

    return this.fetchWithErrorHandling<HistoryResponse>(
      `${API_BASE_URL}/api/journal-data/history?${params}`
    );
  }

  async getStats(): Promise<StatsResponse> {
    return this.fetchWithErrorHandling<StatsResponse>(
      `${API_BASE_URL}/api/journal-data/stats`
    );
  }
}

// シングルトンインスタンス
export const journalDataAPI = new JournalDataAPI();
