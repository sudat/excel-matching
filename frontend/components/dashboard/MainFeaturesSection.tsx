import { FEATURE_CARDS } from "@/lib/dashboard/constants";
import { FeatureCard } from "./FeatureCard";

export function MainFeaturesSection() {
  return (
    <section className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
      {FEATURE_CARDS.map((feature) => (
        <FeatureCard key={feature.id} feature={feature} />
      ))}
    </section>
  );
}