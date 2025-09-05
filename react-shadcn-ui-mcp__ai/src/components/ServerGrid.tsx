import { Server } from "@/types/server";
import { ServerCard } from "@/components/ServerCard";

export function ServerGrid({ servers, onCardClick }: { servers: Server[], onCardClick: (id: string) => void }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
      {servers.map(server => (
        <ServerCard key={server.id} server={server} onClick={() => onCardClick(server.id)} />
      ))}
    </div>
  );
}
