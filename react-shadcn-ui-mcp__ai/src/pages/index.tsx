import Link from "next/link";
import { tweakcn } from "@/lib/tweakcn";
import { Layout } from "@/components/Layout";

export default function Home() {
  return (
    <Layout>
  <section className={tweakcn('card', 'flex flex-col items-center justify-center py-20 w-full min-h-[70vh] relative') + ' before:absolute before:inset-0 before:bg-[radial-gradient(ellipse_at_top_left,_var(--tw-gradient-stops))] before:from-cyan-500/20 before:via-fuchsia-500/10 before:to-transparent before:blur-2xl before:z-0'}>
  <h2 className={tweakcn('header', 'mb-10 text-center tracking-tight z-10')}>Welcome to the Future</h2>
        <nav className="flex justify-center z-10">
          <div className="flex flex-row gap-10">
            <Link
              href="/login"
              className={tweakcn('button', 'neon-glow text-lg uppercase tracking-widest')}
            >
              Login
            </Link>
            <Link
              href="/dashboard"
              className={tweakcn('button', 'neon-glow text-lg uppercase tracking-widest')}
            >
              Dashboard
            </Link>
            <Link
              href="/server/1"
              className={tweakcn('button', 'neon-glow text-lg uppercase tracking-widest')}
            >
              Server Details
            </Link>
          </div>
        </nav>
      </section>
    </Layout>
  );
}
