import { LucideIcon } from "lucide-react";

export interface FeatureCardData {
  id: string;
  title: string;
  description: string;
  content: string;
  href: string;
  icon: LucideIcon;
  iconBgColor: string;
  iconColor: string;
  buttonText: string;
  buttonIcon: LucideIcon;
}

export interface StatusCardData {
  id: string;
  title: string;
  icon: LucideIcon;
  stats: {
    label: string;
    value: string;
  }[];
  href?: string;
  buttonText?: string;
}