import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { StatusBadge } from "@/components/StatusBadge";
import { Server } from "@/types/server";

export function ServerCard({ server, onClick }: { server: Server, onClick: () => void }) {
  return (
    <Card className="cursor-pointer hover:shadow-lg transition" onClick={onClick}>
      <img src={server.image} alt={server.name} className="w-full h-32 object-cover rounded-t" />
      <div className="p-4">
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-semibold text-lg">{server.name}</h3>
          <StatusBadge status={server.status} />
        </div>
        <div className="text-sm text-gray-500">{server.region}</div>
        <Badge variant="secondary" className="mt-2">v{server.version}</Badge>
      </div>
    </Card>
  );
}
