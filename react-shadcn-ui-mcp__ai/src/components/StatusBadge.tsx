import { Badge } from './ui/badge';

export function StatusBadge({ status }: { status: 'online' | 'offline' | 'unknown' }) {
  let color = 'bg-gray-400';
  if (status === 'online') color = 'bg-green-500';
  if (status === 'offline') color = 'bg-red-500';
  return (
    <Badge className={`${color} text-white`}>{status}</Badge>
  );
}
