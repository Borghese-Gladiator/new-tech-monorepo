import * as React from 'react';

export function Collapsible({ title, children }: { title: string; children: React.ReactNode }) {
  const [open, setOpen] = React.useState(false);
  return (
    <div className="mb-2 border rounded">
      <button
        className="w-full text-left px-4 py-2 bg-gray-100 hover:bg-gray-200 font-medium rounded-t focus:outline-none"
        onClick={() => setOpen(o => !o)}
      >
        {title}
      </button>
      {open && <div className="border-t px-4 py-2 bg-white">{children}</div>}
    </div>
  );
}
