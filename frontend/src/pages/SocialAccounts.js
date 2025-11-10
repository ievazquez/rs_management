/**
 * Página de gestión de cuentas sociales
 * Permite conectar y desconectar cuentas de redes sociales
 */
import React, { useState, useEffect } from 'react';
import { socialService } from '../services/api';
import '../styles/SocialAccounts.css';

const SocialAccounts = () => {
  const [accounts, setAccounts] = useState([]);
  const [platforms, setPlatforms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState({ text: '', type: '' });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [accountsData, platformsData] = await Promise.all([
        socialService.getConnectedAccounts(),
        socialService.getPlatforms()
      ]);

      setAccounts(accountsData);
      setPlatforms(platformsData.platforms || []);
    } catch (error) {
      console.error('Error cargando datos:', error);
      setMessage({ text: 'Error al cargar las cuentas', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const handleConnect = async (platformValue) => {
    try {
      const response = await socialService.getAuthUrl(platformValue);
      // Redirigir a la URL de autorización OAuth
      window.location.href = response.authorization_url;
    } catch (error) {
      console.error('Error conectando cuenta:', error);
      setMessage({
        text: 'Error al conectar la cuenta. Intenta nuevamente.',
        type: 'error'
      });
    }
  };

  const handleDisconnect = async (accountId) => {
    if (!window.confirm('¿Estás seguro de que deseas desconectar esta cuenta?')) {
      return;
    }

    try {
      await socialService.disconnectAccount(accountId);
      setMessage({ text: 'Cuenta desconectada exitosamente', type: 'success' });
      loadData(); // Recargar datos
    } catch (error) {
      console.error('Error desconectando cuenta:', error);
      setMessage({ text: 'Error al desconectar la cuenta', type: 'error' });
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

  const isConnected = (platformValue) => {
    return accounts.some(account => account.platform === platformValue);
  };

  if (loading) {
    return <div className="loading">Cargando...</div>;
  }

  return (
    <div className="social-accounts">
      <h1>Cuentas de Redes Sociales</h1>
      <p className="subtitle">Conecta tus cuentas para publicar contenido</p>

      {message.text && (
        <div className={`message ${message.type}`}>
          {message.text}
          <button onClick={() => setMessage({ text: '', type: '' })}>×</button>
        </div>
      )}

      {/* Cuentas conectadas */}
      {accounts.length > 0 && (
        <div className="section">
          <h2>Cuentas Conectadas</h2>
          <div className="accounts-grid">
            {accounts.map((account) => (
              <div key={account.id} className="account-card connected">
                <div className="account-header">
                  <span className="platform-icon">
                    {getPlatformIcon(account.platform)}
                  </span>
                  <div className="account-details">
                    <h3>{account.platform}</h3>
                    <p>{account.platform_username || 'Usuario'}</p>
                  </div>
                  <span className="status-badge connected">Conectada</span>
                </div>
                <div className="account-footer">
                  <button
                    onClick={() => handleDisconnect(account.id)}
                    className="btn btn-danger"
                  >
                    Desconectar
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Plataformas disponibles */}
      <div className="section">
        <h2>Conectar Nueva Cuenta</h2>
        <div className="platforms-grid">
          {platforms.map((platform) => {
            const connected = isConnected(platform.value);
            return (
              <div
                key={platform.value}
                className={`platform-card ${connected ? 'disabled' : ''}`}
              >
                <div className="platform-header">
                  <span className="platform-icon">
                    {getPlatformIcon(platform.value)}
                  </span>
                  <h3>{platform.name}</h3>
                </div>
                <p className="platform-description">{platform.description}</p>
                <button
                  onClick={() => handleConnect(platform.value)}
                  className="btn btn-primary"
                  disabled={connected}
                >
                  {connected ? 'Ya conectada' : 'Conectar'}
                </button>
              </div>
            );
          })}
        </div>
      </div>

      {/* Información adicional */}
      <div className="info-box">
        <h3>ℹ️ Información importante</h3>
        <ul>
          <li>Para Instagram, necesitas tener una cuenta de Instagram Business</li>
          <li>Para Facebook, puedes publicar en tu perfil o en las páginas que administras</li>
          <li>Para Twitter/X, necesitas tener una cuenta verificada con API access</li>
          <li>Tus tokens de acceso se almacenan de forma segura y encriptada</li>
        </ul>
      </div>
    </div>
  );
};

export default SocialAccounts;
