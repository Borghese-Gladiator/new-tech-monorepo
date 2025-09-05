import { useAuth } from "@/hooks/useAuth";
import { useRouter } from 'next/router';
import { ReactNode, useEffect } from 'react';

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!user) router.replace('/login');
  }, [user, router]);

  if (!user) return null;
  return <>{children}</>;
}
