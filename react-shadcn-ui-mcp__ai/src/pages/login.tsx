import { useRouter } from 'next/router';
import { AuthForm } from "@/components/AuthForm";
import { useAuth } from "@/hooks/useAuth";
import { Layout } from "@/components/Layout";
import { tweakcn } from "@/lib/tweakcn";

export default function LoginPage() {
  const { user, loading, error, login } = useAuth();
  const router = useRouter();

  if (user) {
    router.replace('/dashboard');
    return null;
  }

  return (
    <Layout>
      <section className={tweakcn('card', 'max-w-sm mx-auto mt-24 p-8 rounded-2xl shadow-2xl relative') + ' before:absolute before:inset-0 before:bg-[radial-gradient(ellipse_at_top_left,_var(--tw-gradient-stops))] before:from-cyan-500/20 before:via-fuchsia-500/10 before:to-transparent before:blur-2xl before:z-0'}>
        <h2 className={tweakcn('header', 'mb-6 text-center z-10')}>Login</h2>
        <div className="z-10">
          <AuthForm onSubmit={login} loading={loading} error={error || undefined} />
        </div>
      </section>
    </Layout>
  );
}
