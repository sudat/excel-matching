"use client";

import React from "react";
import { Button } from "@/components/ui/button";
import {
  AlertTriangle,
  CheckCircle2,
  X,
} from "lucide-react";

interface OverwriteDialogProps {
  isOpen: boolean;
  fiscalYear: number;
  fiscalMonth: number;
  onConfirm: () => void;
  onCancel: () => void;
}

export default function OverwriteDialog({
  isOpen,
  fiscalYear,
  fiscalMonth,
  onConfirm,
  onCancel,
}: OverwriteDialogProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md mx-4 shadow-xl">
        <div className="flex items-center mb-4">
          <AlertTriangle className="h-6 w-6 text-orange-500 mr-3" />
          <h3 className="text-lg font-semibold text-gray-900">
            既存データの上書き確認
          </h3>
        </div>
        
        <div className="mb-6">
          <p className="text-gray-700 mb-3">
            指定された期間（{fiscalYear}年{fiscalMonth}月）には既に仕訳データが登録されています。
          </p>
          <div className="bg-orange-50 border border-orange-200 rounded-md p-3">
            <p className="text-sm text-orange-800">
              <strong>注意:</strong> 上書きすると既存のデータは完全に削除され、復元できません。
            </p>
          </div>
        </div>

        <div className="flex space-x-3">
          <Button
            onClick={onCancel}
            variant="outline"
            className="flex-1"
          >
            <X className="h-4 w-4 mr-2" />
            キャンセル
          </Button>
          <Button
            onClick={onConfirm}
            variant="destructive"
            className="flex-1"
          >
            <CheckCircle2 className="h-4 w-4 mr-2" />
            上書き実行
          </Button>
        </div>
      </div>
    </div>
  );
}