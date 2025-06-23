import { Badge } from "@/components/ui/badge";
import { FileSpreadsheet } from "lucide-react";
import { formatFileSize } from "@/lib/upload/utils";
import type { UploadResponse } from "@/lib/upload/types";

interface FileDetailsProps {
  uploadResult: UploadResponse;
}

export default function FileDetails({ uploadResult }: FileDetailsProps) {
  return (
    <div className="mt-4">
      <h4 className="font-medium text-gray-800 mb-3">
        アップロードされたファイル:
      </h4>
      <div className="space-y-2">
        {uploadResult.uploaded_files.map((file) => (
          <div
            key={file.file_id}
            className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border"
          >
            <div className="flex items-center space-x-3">
              <FileSpreadsheet className="h-5 w-5 text-green-600" />
              <div>
                <p className="font-medium text-gray-800 text-sm">
                  {file.filename}
                </p>
                <p className="text-xs text-gray-500">
                  {formatFileSize(file.file_size)}
                </p>
              </div>
            </div>
            <Badge variant="secondary" className="text-xs">
              完了
            </Badge>
          </div>
        ))}
      </div>
    </div>
  );
}