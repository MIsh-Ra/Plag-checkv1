import { useNavigate, useLocation } from 'react-router-dom';
import { Shield, LayoutDashboard, Settings, LogOut, Moon, Sun } from 'lucide-react';
import { useTheme } from '../ThemeContext';

export default function GlobalLayout({ children }) {
    const navigate = useNavigate();
    const location = useLocation();
    const { theme, toggleTheme } = useTheme();
    const user = JSON.parse(localStorage.getItem('alethian_user') || '{}');

    const handleLogout = () => {
        localStorage.removeItem('alethian_token');
        localStorage.removeItem('alethian_user');
        navigate('/login');
    };

    const navItems = [
        { path: '/dashboard', label: 'Faculty Dashboard', icon: LayoutDashboard },
        { path: '/admin', label: 'Admin Configuration', icon: Settings }
    ];

    return (
        <div className="flex h-screen w-full bg-background overflow-hidden text-on-background">
            {/* The Forensic Laboratory Sidebar: Heavy Sidebar using surface-container-low */}
            <aside className="w-72 bg-surface-container-low flex flex-col justify-between py-6 px-4">
                <div>
                    <div className="flex items-center space-x-3 mb-10 px-2">
                        <Shield className="w-8 h-8 text-primary font-bold" />
                        <span className="text-2xl font-bold tracking-tight text-on-surface">Alethian</span>
                    </div>

                    <nav className="space-y-2">
                        {navItems.map((item) => {
                            const Icon = item.icon;
                            const isActive = location.pathname.startsWith(item.path);
                            return (
                                <button
                                    key={item.path}
                                    onClick={() => navigate(item.path)}
                                    className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-sm transition-all text-sm font-medium ${
                                        isActive
                                            ? 'bg-surface text-primary font-semibold shadow-ambient'
                                            : 'text-on-surface-variant hover:bg-surface-container hover:text-on-surface'
                                    }`}
                                >
                                    <Icon className="w-5 h-5" />
                                    <span>{item.label}</span>
                                </button>
                            );
                        })}
                    </nav>
                </div>

                <div className="space-y-2 border-t border-ghost pt-4">
                     <button
                        onClick={toggleTheme}
                        className="w-full flex items-center justify-between px-3 py-2.5 rounded-sm hover:bg-surface-container transition-all text-sm font-medium text-on-surface-variant"
                    >
                        <span className="flex items-center space-x-3">
                            {theme === 'dark' ? <Moon className="w-5 h-5" /> : <Sun className="w-5 h-5" />}
                            <span>{theme === 'dark' ? 'True Dark' : 'Standard'}</span>
                        </span>
                    </button>
                    <div className="flex items-center justify-between px-3 py-2.5 rounded-sm mt-2">
                        <div className="flex items-center space-x-3 text-sm font-medium text-on-surface-variant">
                             <div className="w-8 h-8 rounded-full bg-primary-container text-on-primary flex items-center justify-center font-bold">
                                 {user.name ? user.name.charAt(0).toUpperCase() : 'F'}
                             </div>
                             <div className="flex flex-col text-left">
                                 <span className="text-on-surface font-semibold">{user.name || 'Faculty'}</span>
                                 <span className="text-xs">Investigator</span>
                             </div>
                        </div>
                    </div>
                     <button
                        onClick={handleLogout}
                        className="w-full flex items-center space-x-3 px-3 py-2 mt-2 rounded-sm hover:bg-error-container hover:text-on-error-container transition-all text-sm font-medium text-on-surface-variant"
                    >
                        <LogOut className="w-5 h-5" />
                        <span>Sign Out</span>
                    </button>
                </div>
            </aside>

            {/* Main fluid document stage */}
            <main className="flex-1 bg-surface overflow-auto relative">
                {children}
            </main>
        </div>
    );
}
