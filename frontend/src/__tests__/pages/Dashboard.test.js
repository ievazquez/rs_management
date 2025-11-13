/**
 * Tests para página de Dashboard
 */
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Dashboard from '../../pages/Dashboard';
import { socialService, postService } from '../../services/api';

jest.mock('../../services/api');

const renderDashboard = () => {
  return render(
    <BrowserRouter>
      <Dashboard />
    </BrowserRouter>
  );
};

describe('Dashboard Page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should display loading state initially', () => {
    socialService.getConnectedAccounts.mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );
    postService.getPosts.mockImplementation(() => new Promise(() => {}));

    renderDashboard();

    expect(screen.getByText(/cargando/i)).toBeInTheDocument();
  });

  it('should display connected accounts', async () => {
    const mockAccounts = [
      {
        id: 1,
        platform: 'facebook',
        platform_username: 'testfb',
        is_active: true
      },
      {
        id: 2,
        platform: 'twitter',
        platform_username: 'testtw',
        is_active: true
      }
    ];

    socialService.getConnectedAccounts.mockResolvedValue(mockAccounts);
    postService.getPosts.mockResolvedValue([]);

    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText('testfb')).toBeInTheDocument();
      expect(screen.getByText('testtw')).toBeInTheDocument();
    });
  });

  it('should display empty state when no accounts connected', async () => {
    socialService.getConnectedAccounts.mockResolvedValue([]);
    postService.getPosts.mockResolvedValue([]);

    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText(/no tienes cuentas conectadas/i)).toBeInTheDocument();
    });
  });

  it('should display recent posts', async () => {
    const mockPosts = [
      {
        id: 1,
        content: 'First post content',
        status: 'published',
        platforms: []
      },
      {
        id: 2,
        content: 'Second post content',
        status: 'draft',
        platforms: []
      }
    ];

    socialService.getConnectedAccounts.mockResolvedValue([]);
    postService.getPosts.mockResolvedValue(mockPosts);

    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText(/first post content/i)).toBeInTheDocument();
      expect(screen.getByText(/second post content/i)).toBeInTheDocument();
    });
  });

  it('should display empty state when no posts', async () => {
    socialService.getConnectedAccounts.mockResolvedValue([]);
    postService.getPosts.mockResolvedValue([]);

    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText(/no tienes publicaciones/i)).toBeInTheDocument();
    });
  });

  it('should display quick actions', async () => {
    socialService.getConnectedAccounts.mockResolvedValue([]);
    postService.getPosts.mockResolvedValue([]);

    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText(/nueva publicación/i)).toBeInTheDocument();
      expect(screen.getByText(/conectar cuenta/i)).toBeInTheDocument();
      expect(screen.getByText(/ver estadísticas/i)).toBeInTheDocument();
    });
  });

  it('should handle API errors gracefully', async () => {
    const consoleError = jest.spyOn(console, 'error').mockImplementation(() => {});

    socialService.getConnectedAccounts.mockRejectedValue(
      new Error('API Error')
    );
    postService.getPosts.mockRejectedValue(new Error('API Error'));

    renderDashboard();

    await waitFor(() => {
      expect(consoleError).toHaveBeenCalled();
    });

    consoleError.mockRestore();
  });

  it('should display post status badges correctly', async () => {
    const mockPosts = [
      { id: 1, content: 'Published post', status: 'published', platforms: [] },
      { id: 2, content: 'Draft post', status: 'draft', platforms: [] },
      { id: 3, content: 'Failed post', status: 'failed', platforms: [] }
    ];

    socialService.getConnectedAccounts.mockResolvedValue([]);
    postService.getPosts.mockResolvedValue(mockPosts);

    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText('Publicada')).toBeInTheDocument();
      expect(screen.getByText('Borrador')).toBeInTheDocument();
      expect(screen.getByText('Fallida')).toBeInTheDocument();
    });
  });
});
