import {
  ArrowRight,
  BarChart3,
  Clock,
  Database,
  FileText,
  Search,
  Upload,
} from "lucide-react";
import { FeatureCardData, StatusCardData } from "./types";

export const FEATURE_CARDS: FeatureCardData[] = [
  {
    id: "journal-data",
    title: "1. 仕訳データ管理",
    description: "事前準備：仕訳データの登録・管理",
    content: "会計システムからの仕訳データをアップロード・管理。一覧表示、検索、履歴確認機能を提供します。",
    href: "/journal-data",
    icon: Database,
    iconBgColor: "bg-blue-100",
    iconColor: "text-blue-600",
    buttonText: "管理画面を開く",
    buttonIcon: ArrowRight,
  },
  {
    id: "excel-upload",
    title: "2. Excelアップロード",
    description: "各部門のExcelファイルをアップロード",
    content: "照合対象となるExcel/CSVファイルをアップロード。AIが自動でファイル構造を解析します。",
    href: "/upload",
    icon: Upload,
    iconBgColor: "bg-green-100",
    iconColor: "text-green-600",
    buttonText: "ファイルアップロード",
    buttonIcon: Upload,
  },
  {
    id: "matching",
    title: "3. 突合・照合実行",
    description: "AI自動突合処理の実行・結果確認",
    content: "登録済み仕訳データとExcelファイルの突合処理。高精度なAI照合で業務効率を向上させます。",
    href: "/matching/new",
    icon: Search,
    iconBgColor: "bg-purple-100",
    iconColor: "text-purple-600",
    buttonText: "突合処理開始",
    buttonIcon: ArrowRight,
  },
];

export const STATUS_CARDS: StatusCardData[] = [
  {
    id: "journal-data-summary",
    title: "登録済み仕訳データ",
    icon: BarChart3,
    stats: [
      { label: "総件数", value: "-" },
      { label: "最新登録日", value: "-" },
    ],
    href: "/journal-data",
    buttonText: "詳細を見る",
  },
  {
    id: "active-sessions",
    title: "進行中セッション",
    icon: Clock,
    stats: [
      { label: "アクティブ", value: "0" },
      { label: "待機中", value: "0" },
    ],
    buttonText: "詳細を見る",
  },
  {
    id: "matching-history",
    title: "突合履歴",
    icon: FileText,
    stats: [
      { label: "今月実行", value: "-" },
      { label: "成功率", value: "-" },
    ],
    buttonText: "履歴を見る",
  },
];