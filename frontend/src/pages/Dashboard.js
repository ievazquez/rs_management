/**
 * Dashboard principal
 * Muestra resumen de cuentas conectadas y publicaciones recientes
 */
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { socialService, postService } from '../services/api';
import '../styles/Dashboard.css';

const Dashboard = () => {
  const [accounts, setAccounts] = useState([]);
  const [recentPosts, setRecentPosts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      const [accountsData, postsData] = await Promise.all([
        socialService.getConnectedAccounts(),
        postService.getPosts(0, 5)
      ]);

      setAccounts(accountsData);
      setRecentPosts(postsData);
    } catch (error) {
      console.error('Error cargando datos del dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const getPlatformIcon = (platform) => {
    const icons = {
      facebook: '📘',
      instagram: '📷',
      twitter: '🐦'
    };
    return icons[platform] || '📱';
  };

  const getStatusBadge = (status) => {
    const badges = {
      draft: { text: 'Borrador', class: 'badge-draft' },
      scheduled: { text: 'Programada', class: 'badge-scheduled' },
      published: { text: 'Publicada', class: 'badge-published' },
      failed: { text: 'Fallida', class: 'badge-failed' },
      partial: { text: 'Parcial', class: 'badge-partial' }
    };
    return badges[status] || { text: status, class: 'badge-default' };
  };

  if (loading) {
    return <div className="loading">Cargando...</div>;
  }

  return (
    <div className="dashboard">
      <h1>Dashboard</h1>

      <div className="dashboard-grid">
        {/* Cuentas conectadas */}
        <div className="dashboard-card">
          <div className="card-header">
            <h2>Cuentas Conectadas</h2>
            <Link to="/social-accounts" className="btn-link">Ver todas</Link>
          </div>

          {accounts.length === 0 ? (
            <div className="empty-state">
              <p>No tienes cuentas conectadas</p>
              <Link to="/social-accounts" className="btn btn-primary">
                Conectar cuenta
              </Link>
            </div>
          ) : (
            <div className="accounts-list">
              {accounts.map((account) => (
                <div key={account.id} className="account-item">
                  <span className="platform-icon">
                    {getPlatformIcon(account.platform)}
                  </span>
                  <div className="account-info">
                    <div className="account-platform">{account.platform}</div>
                    <div className="account-username">
                      {account.platform_username || 'Usuario'}
                    </div>
                  </div>
                  <span className="status-dot active"></span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Publicaciones recientes */}
        <div className="dashboard-card">
          <div className="card-header">
            <h2>Publicaciones Recientes</h2>
            <Link to="/posts" className="btn-link">Ver todas</Link>
          </div>

          {recentPosts.length === 0 ? (
            <div className="empty-state">
              <p>No tienes publicaciones</p>
              <Link to="/create-post" className="btn btn-primary">
                Crear publicación
              </Link>
            </div>
          ) : (
            <div className="posts-list">
              {recentPosts.map((post) => {
                const badge = getStatusBadge(post.status);
                return (
                  <div key={post.id} className="post-item">
                    <div className="post-content">
                      <p>{post.content.substring(0, 100)}...</p>
                      <span className={`badge ${badge.class}`}>
                        {badge.text}
                      </span>
                    </div>
                    <div className="post-platforms">
                      {post.platforms.map((p) => (
                        <span key={p.id} className="platform-badge">
                          {getPlatformIcon(p.social_account_id)}
                        </span>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Acciones rápidas */}
        <div className="dashboard-card quick-actions">
          <h2>Acciones Rápidas</h2>
          <div className="actions-grid">
            <Link to="/create-post" className="action-button">
              <span className="action-icon">✏️</span>
              <span className="action-text">Nueva Publicación</span>
            </Link>
            <Link to="/social-accounts" className="action-button">
              <span className="action-icon">🔗</span>
              <span className="action-text">Conectar Cuenta</span>
            </Link>
            <Link to="/posts" className="action-button">
              <span className="action-icon">📊</span>
              <span className="action-text">Ver Estadísticas</span>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
