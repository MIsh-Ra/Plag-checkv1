import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Login from '../pages/Login';
import Client from '../api/client';

// Mock Client
vi.mock('../api/client', () => ({
  default: {
    auth: {
      login: vi.fn(),
    }
  }
}));

describe('Login Component', () => {
    it('calls API and redirects on success', async () => {
        Client.auth.login.mockResolvedValue({ access_token: 'valid_token', user_id: '1', role: 'faculty' });
        render(<BrowserRouter><Login /></BrowserRouter>);

        // Actual placeholders from Login.jsx: "faculty@university.edu" and "••••••••"
        fireEvent.change(screen.getByPlaceholderText('faculty@university.edu'), { target: { value: 'test@edu' } });
        fireEvent.change(screen.getByPlaceholderText('••••••••'), { target: { value: 'password' } });
        fireEvent.click(screen.getByText('Sign In'));

        await waitFor(() => {
            expect(Client.auth.login).toHaveBeenCalledWith('test@edu', 'password');
        });
    });

    it('shows error message on failure', async () => {
        Client.auth.login.mockRejectedValue(new Error('Bad request'));
        render(<BrowserRouter><Login /></BrowserRouter>);

        // Fill in required fields so the form actually submits
        fireEvent.change(screen.getByPlaceholderText('faculty@university.edu'), { target: { value: 'test@edu' } });
        fireEvent.change(screen.getByPlaceholderText('••••••••'), { target: { value: 'password' } });
        fireEvent.click(screen.getByText('Sign In'));

        await waitFor(() => {
            expect(screen.getByText('Invalid credentials')).toBeInTheDocument();
        });
    });
});
