import { STATUS_CARDS } from "@/lib/dashboard/constants";
import { StatusCard } from "./StatusCard";

export function StatusOverviewSection() {
  return (
    <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {STATUS_CARDS.map((status) => (
        <StatusCard key={status.id} status={status} />
      ))}
    </section>
  );
}