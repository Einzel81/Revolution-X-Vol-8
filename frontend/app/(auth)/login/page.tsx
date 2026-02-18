// frontend/app/(auth)/login/page.tsx
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Eye, EyeOff, Lock, Mail, AlertCircle } from 'lucide-react';
import { authService } from '@/lib/auth';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [twoFactorCode, setTwoFactorCode] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [requires2FA, setRequires2FA] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await authService.login({
        email,
        password,
        two_factor_code: requires2FA ? twoFactorCode : undefined,
      });
      router.push('/dashboard');
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Login failed';
      if (message.includes('2FA')) {
        setRequires2FA(true);
      } else {
        setError(message);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-revolution-dark p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-gradient-to-br from-gold-400 to-gold-600 rounded-xl flex items-center justify-center mx-auto mb-4">
            <span className="text-2xl font-bold text-white">X</span>
          </div>
          <h1 className="text-2xl font-bold text-white">Revolution X</h1>
          <p className="text-slate-400">AI-Powered Gold Trading</p>
        </div>

        {/* Login Form */}
        <div className="bg-revolution-card border border-revolution-border rounded-xl p-6">
          <h2 className="text-xl font-semibold text-white mb-6">
            {requires2FA ? 'Two-Factor Authentication' : 'Sign In'}
          </h2>

          {error && (
            <div className="flex items-center space-x-2 p-3 bg-rose-500/20 border border-rose-500/30 rounded-lg mb-4">
              <AlertCircle className="w-5 h-5 text-rose-400" />
              <span className="text-rose-400 text-sm">{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {!requires2FA ? (
              <>
                <div>
                  <label className="block text-slate-400 text-sm mb-2">Email</label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="w-full bg-revolution-dark border border-revolution-border rounded-lg pl-10 pr-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-gold-500"
                      placeholder="Enter your email"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-slate-400 text-sm mb-2">Password</label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
                    <input
                      type={showPassword ? 'text' : 'password'}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="w-full bg-revolution-dark border border-revolution-border rounded-lg pl-10 pr-12 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-gold-500"
                      placeholder="Enter your password"
                      required
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
                    >
                      {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                    </button>
                  </div>
                </div>
              </>
            ) : (
              <div>
                <label className="block text-slate-400 text-sm mb-2">2FA Code</label>
                <input
                  type="text"
                  value={twoFactorCode}
                  onChange={(e) => setTwoFactorCode(e.target.value)}
                  className="w-full bg-revolution-dark border border-revolution-border rounded-lg px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-gold-500 text-center text-2xl tracking-widest"
                  placeholder="000000"
                  maxLength={6}
                  required
                />
                <p className="text-slate-500 text-sm mt-2 text-center">
                  Enter the code from your authenticator app
                </p>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-gold-500 to-gold-600 text-white font-semibold py-3 rounded-lg hover:from-gold-400 hover:to-gold-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Signing in...' : requires2FA ? 'Verify' : 'Sign In'}
            </button>
          </form>
        </div>

        <p className="text-center text-slate-500 text-sm mt-6">
          Protected by Revolution X Security
        </p>
      </div>
    </div>
  );
}
