import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Client from '../api/client';
import { Loader2, Shield } from 'lucide-react';
import { useTheme } from '../components/ThemeContext';

export default function Login() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const navigate = useNavigate();
    const { theme } = useTheme();

    // Default to true dark
    if (theme !== 'dark') {
        const root = window.document.documentElement;
        root.classList.add('dark');
    }

    const handleLogin = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            const response = await Client.auth.login(email, password);
            console.log("Login Success:", response);
            localStorage.setItem('alethian_token', response.access_token);
            localStorage.setItem('alethian_user', JSON.stringify({
                name: email.split('@')[0],
                email: email,
                role: response.role,
                user_id: response.user_id
            }));

            if (response.role === 'admin') {
                navigate('/admin');
            } else {
                navigate('/dashboard');
            }
        } catch (err) {
            setError('Invalid credentials');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex items-center justify-center min-h-screen bg-background text-on-background">
            <div className="w-full max-w-md p-10 space-y-8 bg-surface-container shadow-ambient border border-ghost relative overflow-hidden">
                <div className="absolute top-0 left-0 w-full h-1 bg-primary"></div>
                <div className="text-center flex flex-col items-center">
                    <Shield className="w-12 h-12 text-primary mb-4" />
                    <h1 className="text-3xl font-bold tracking-tight text-on-surface uppercase">Alethian</h1>
                    <p className="mt-2 text-xs font-mono tracking-widest text-on-surface-variant uppercase">Forensic Intelligence Network</p>
                </div>

                <form className="space-y-6" onSubmit={handleLogin}>
                    <div className="space-y-2">
                        <label className="text-xs font-bold text-on-surface-variant uppercase tracking-wider">Investigator ID</label>
                        <input
                            type="email"
                            required
                            className="w-full px-4 py-3 bg-surface-container-highest border border-ghost text-sm text-on-surface focus:outline-none focus:border-outline transition-colors placeholder:text-on-surface-variant/50"
                            placeholder="faculty@institution.edu"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                        />
                    </div>

                    <div className="space-y-2">
                        <label className="text-xs font-bold text-on-surface-variant uppercase tracking-wider">Passcode</label>
                        <input
                            type="password"
                            required
                            className="w-full px-4 py-3 bg-surface-container-highest border border-ghost text-sm text-on-surface focus:outline-none focus:border-outline transition-colors placeholder:text-on-surface-variant/50"
                            placeholder="••••••••"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                        />
                    </div>

                    {error && (
                        <div className="p-3 text-xs font-bold text-error bg-error-container border border-error/20 flex items-center">
                            {error}
                        </div>
                    )}

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full flex justify-center items-center py-3 px-4 border shadow-ambient text-sm font-bold uppercase tracking-wider text-on-primary bg-primary border-transparent hover:bg-primary-container disabled:opacity-50 transition-colors"
                    >
                        {loading ? (
                            <Loader2 className="w-5 h-5 animate-spin" />
                        ) : (
                            "Authenticate"
                        )}
                    </button>
                </form>

                <div className="pt-2">
                    <button
                        type="button"
                        onClick={() => alert("SSO Integration Pending Document Mesh Approval")}
                        className="w-full flex justify-center py-3 px-4 border border-ghost text-sm font-bold uppercase tracking-wider text-on-surface bg-surface hover:bg-surface-container-highest transition-colors"
                    >
                        SSO Handshake
                    </button>
                </div>
            </div>
        </div>
    );
}
