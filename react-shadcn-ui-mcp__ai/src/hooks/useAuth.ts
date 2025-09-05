import { useState } from 'react';

export function useAuth() {
  const [user, setUser] = useState<{ email: string } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const login = async (email: string, password: string) => {
    setLoading(true);
    setError(null);
    // TODO: Replace with real authentication logic
    await new Promise(res => setTimeout(res, 1000));
    if (email === 'admin@example.com' && password === 'password') {
      setUser({ email });
    } else {
      setError('Invalid credentials');
    }
    setLoading(false);
  };

  const logout = () => setUser(null);

  return { user, loading, error, login, logout };
}
