import AppLayout from "@/components/layout/AppLayout";
import {
  WelcomeSection,
  MainFeaturesSection,
  StatusOverviewSection,
} from "@/components/dashboard";

export default function DashboardPage() {
  return (
    <AppLayout title="経費精算突合システム" subtitle="ダッシュボード">
      <WelcomeSection />
      <MainFeaturesSection />
      <StatusOverviewSection />
    </AppLayout>
  );
}
