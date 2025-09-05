export function MetadataDisplay({ data }: { data: Record<string, string | number> }) {
  return (
    <div className="grid grid-cols-2 gap-4 my-4">
      {Object.entries(data).map(([key, value]) => (
        <div key={key} className="flex flex-col">
          <span className="text-xs text-gray-500 uppercase">{key}</span>
          <span className="font-medium">{value}</span>
        </div>
      ))}
    </div>
  );
}
