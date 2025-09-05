import { useRouter } from 'next/router';
import { useAuth } from "@/hooks/useAuth";
import { useServers } from "@/hooks/useServers";
import { Layout } from "@/components/Layout";
import { tweakcn } from "@/lib/tweakcn";
import { HeaderImage } from "@/components/HeaderImage";
import { MetadataDisplay } from "@/components/MetadataDisplay";
import { InstallSteps } from "@/components/InstallSteps";

export default function ServerDetailPage() {
  const { user } = useAuth();
  const { servers } = useServers();
  const router = useRouter();
  const { id } = router.query;

  if (!user) {
    router.replace('/login');
    return null;
  }

  const server = servers.find(s => s.id === id);
  if (!server) return <Layout><div>Server not found.</div></Layout>;

  return (
    <Layout>
      <section className={tweakcn('card', 'p-8 rounded-2xl shadow-2xl mt-10 flex flex-col items-center relative') + ' before:absolute before:inset-0 before:bg-[radial-gradient(ellipse_at_top_left,_var(--tw-gradient-stops))] before:from-cyan-500/20 before:via-fuchsia-500/10 before:to-transparent before:blur-2xl before:z-0'}>
        <HeaderImage src={server.image} alt={server.name} />
        <h2 className={tweakcn('header', 'mt-4 mb-2 text-center z-10')}>{server.name}</h2>
        <div className="z-10 w-full">
          <MetadataDisplay data={{
            Status: server.status,
            Region: server.region,
            Version: server.version
          }} />
          <h3 className={tweakcn('subheader', 'mt-6 mb-2 text-center')}>Installation Steps</h3>
          <InstallSteps steps={server.installSteps} />
        </div>
      </section>
    </Layout>
  );
}
