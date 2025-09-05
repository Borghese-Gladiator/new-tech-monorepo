import { useRouter } from 'next/router';
import { useAuth } from "@/hooks/useAuth";
import { useServers } from "@/hooks/useServers";
import { ServerGrid } from "@/components/ServerGrid";
import { Layout } from "@/components/Layout";
import { tweakcn } from "@/lib/tweakcn";

export default function DashboardPage() {
  const { user } = useAuth();
  const { servers } = useServers();
  const router = useRouter();

  if (!user) {
    router.replace('/login');
    return null;
  }

  return (
    <Layout>
      <section className={tweakcn('card', 'p-8 rounded-2xl shadow-2xl mt-10 relative') + ' before:absolute before:inset-0 before:bg-[radial-gradient(ellipse_at_top_left,_var(--tw-gradient-stops))] before:from-cyan-500/20 before:via-fuchsia-500/10 before:to-transparent before:blur-2xl before:z-0'}>
        <h2 className={tweakcn('header', 'mb-6 text-center z-10')}>MCP Servers</h2>
        <div className="z-10">
          <ServerGrid servers={servers} onCardClick={id => router.push(`/server/${id}`)} />
        </div>
      </section>
    </Layout>
  );
}
