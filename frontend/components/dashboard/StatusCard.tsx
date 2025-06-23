import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { StatusCardData } from "@/lib/dashboard/types";
import { ArrowRight } from "lucide-react";
import Link from "next/link";

interface StatusCardProps {
  status: StatusCardData;
}

export function StatusCard({ status }: StatusCardProps) {
  const { title, icon: Icon, stats, href, buttonText } = status;

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base flex items-center space-x-2">
          <Icon className="h-4 w-4" />
          <span>{title}</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {stats.map((stat, index) => (
            <div key={index} className="flex justify-between items-center">
              <span className="text-sm text-gray-600">{stat.label}</span>
              <span className="font-semibold text-sm">{stat.value}</span>
            </div>
          ))}
          {buttonText && (
            <div className="pt-2">
              {href ? (
                <Link href={href}>
                  <Button variant="ghost" size="sm" className="text-xs">
                    {buttonText}
                    <ArrowRight className="h-3 w-3 ml-1" />
                  </Button>
                </Link>
              ) : (
                <Button variant="ghost" size="sm" className="text-xs">
                  {buttonText}
                  <ArrowRight className="h-3 w-3 ml-1" />
                </Button>
              )}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}