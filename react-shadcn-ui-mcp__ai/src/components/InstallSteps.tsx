import { Collapsible } from "@/components/ui/collapsible";

export function InstallSteps({ steps }: { steps: string[] }) {
  return (
    <div className="my-6">
      {steps.map((step, idx) => (
        <Collapsible key={idx} title={`Step ${idx + 1}`}>
          <div className="p-4">{step}</div>
        </Collapsible>
      ))}
    </div>
  );
}
