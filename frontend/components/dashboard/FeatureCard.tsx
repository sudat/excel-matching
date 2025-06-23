import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { FeatureCardData } from "@/lib/dashboard/types";
import Link from "next/link";

interface FeatureCardProps {
  feature: FeatureCardData;
}

export function FeatureCard({ feature }: FeatureCardProps) {
  const {
    title,
    description,
    content,
    href,
    icon: Icon,
    iconBgColor,
    iconColor,
    buttonText,
    buttonIcon: ButtonIcon,
  } = feature;

  return (
    <Card className="hover:shadow-lg transition-all duration-300">
      <CardHeader>
        <div className="flex items-center space-x-3">
          <div className={`h-12 w-12 ${iconBgColor} rounded-lg flex items-center justify-center`}>
            <Icon className={`h-6 w-6 ${iconColor}`} />
          </div>
          <div>
            <CardTitle className="text-lg">{title}</CardTitle>
            <CardDescription>{description}</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-gray-600 mb-4 text-sm">{content}</p>
        <Link href={href}>
          <Button className="w-full" size="sm">
            {buttonText}
            <ButtonIcon className="h-4 w-4 ml-2" />
          </Button>
        </Link>
      </CardContent>
    </Card>
  );
}