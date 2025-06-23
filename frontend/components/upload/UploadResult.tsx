import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { ArrowRight, CheckCircle2 } from "lucide-react";
import FileDetails from "./FileDetails";
import type { UploadResponse } from "@/lib/upload/types";

interface UploadResultProps {
  uploadResult: UploadResponse;
}

export default function UploadResult({ uploadResult }: UploadResultProps) {
  return (
    <div className="mt-6 max-w-4xl mx-auto px-4">
      <Alert className="border-green-200 bg-green-50">
        <CheckCircle2 className="h-4 w-4 text-green-600" />
        <AlertDescription>
          <div className="space-y-3">
            <div>
              <h3 className="font-medium text-green-800">
                アップロード完了
              </h3>
              <p className="text-green-700 mt-1">
                {uploadResult.message}
              </p>
            </div>

            <div className="bg-white p-4 rounded-lg border border-green-200">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="font-medium text-gray-700">
                    業務依頼ID:
                  </span>
                  <code className="ml-2 font-mono text-xs bg-gray-100 px-2 py-1 rounded">
                    {uploadResult.business_request_id}
                  </code>
                </div>
                <div>
                  <span className="font-medium text-gray-700">
                    ファイル数:
                  </span>
                  <span className="ml-2">
                    {uploadResult.total_files}個
                  </span>
                </div>
              </div>

              <FileDetails uploadResult={uploadResult} />

              <div className="mt-4 pt-4 border-t border-green-200">
                <Button className="w-full sm:w-auto">
                  <ArrowRight className="h-4 w-4 mr-2" />
                  分析結果を確認
                </Button>
              </div>
            </div>
          </div>
        </AlertDescription>
      </Alert>
    </div>
  );
}