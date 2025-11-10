/**
 * Página para crear y programar publicaciones
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { postService, socialService } from '../services/api';
import PostPreview from '../components/Posts/PostPreview';
import '../styles/CreatePost.css';

const CreatePost = () => {
  const [content, setContent] = useState('');
  const [imageUrl, setImageUrl] = useState('');
  const [scheduledDate, setScheduledDate] = useState('');
  const [scheduledTime, setScheduledTime] = useState('');
  const [selectedAccounts, setSelectedAccounts] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ text: '', type: '' });

  const navigate = useNavigate();

  useEffect(() => {
    loadAccounts();
  }, []);

  const loadAccounts = async () => {
    try {
      const data = await socialService.getConnectedAccounts();
      setAccounts(data);
    } catch (error) {
      console.error('Error cargando cuentas:', error);
      setMessage({ text: 'Error al cargar las cuentas', type: 'error' });
    }
  };

  const handleAccountToggle = (accountId) => {
    setSelectedAccounts(prev =>
      prev.includes(accountId)
        ? prev.filter(id => id !== accountId)
        : [...prev, accountId]
    );
  };

  const handleSubmit = async (e, publish = false) => {
    e.preventDefault();
    setMessage({ text: '', type: '' });

    if (!content.trim()) {
      setMessage({ text: 'El contenido es requerido', type: 'error' });
      return;
    }

    if (selectedAccounts.length === 0) {
      setMessage({
        text: 'Selecciona al menos una cuenta social',
        type: 'error'
      });
      return;
    }

    // Validar que Instagram tenga imagen
    const hasInstagram = selectedAccounts.some(id => {
      const account = accounts.find(a => a.id === id);
      return account && account.platform === 'instagram';
    });

    if (hasInstagram && !imageUrl.trim()) {
      setMessage({
        text: 'Instagram requiere una imagen',
        type: 'error'
      });
      return;
    }

    setLoading(true);

    try {
      const postData = {
        content,
        image_url: imageUrl || null,
        platform_account_ids: selectedAccounts
      };

      // Si hay fecha programada, agregarla
      if (scheduledDate && scheduledTime) {
        const scheduledAt = new Date(`${scheduledDate}T${scheduledTime}`);
        postData.scheduled_at = scheduledAt.toISOString();
      }

      const post = await postService.createPost(postData);

      // Si se quiere publicar inmediatamente
      if (publish && !postData.scheduled_at) {
        await postService.publishPost(post.id);
        setMessage({
          text: 'Publicación creada y en proceso de publicación',
          type: 'success'
        });
      } else if (postData.scheduled_at) {
        setMessage({
          text: 'Publicación programada exitosamente',
          type: 'success'
        });
      } else {
        setMessage({
          text: 'Borrador guardado exitosamente',
          type: 'success'
        });
      }

      // Limpiar formulario
      setTimeout(() => {
        navigate('/posts');
      }, 1500);

    } catch (error) {
      console.error('Error creando publicación:', error);
      setMessage({
        text: error.response?.data?.detail || 'Error al crear la publicación',
        type: 'error'
      });
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

  return (
    <div className="create-post">
      <h1>Nueva Publicación</h1>

      {message.text && (
        <div className={`message ${message.type}`}>
          {message.text}
          <button onClick={() => setMessage({ text: '', type: '' })}>×</button>
        </div>
      )}

      <div className="create-post-grid">
        {/* Formulario */}
        <div className="post-form">
          <form onSubmit={(e) => handleSubmit(e, false)}>
            <div className="form-group">
              <label htmlFor="content">Contenido *</label>
              <textarea
                id="content"
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="¿Qué quieres compartir?"
                rows="6"
                required
              />
              <div className="char-count">
                {content.length} caracteres
                {content.length > 280 && (
                  <span className="warning"> (Twitter truncará a 280)</span>
                )}
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="imageUrl">URL de Imagen</label>
              <input
                type="url"
                id="imageUrl"
                value={imageUrl}
                onChange={(e) => setImageUrl(e.target.value)}
                placeholder="https://ejemplo.com/imagen.jpg"
              />
              <small>Requerida para Instagram, opcional para otras plataformas</small>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="scheduledDate">Fecha de Programación</label>
                <input
                  type="date"
                  id="scheduledDate"
                  value={scheduledDate}
                  onChange={(e) => setScheduledDate(e.target.value)}
                  min={new Date().toISOString().split('T')[0]}
                />
              </div>

              <div className="form-group">
                <label htmlFor="scheduledTime">Hora</label>
                <input
                  type="time"
                  id="scheduledTime"
                  value={scheduledTime}
                  onChange={(e) => setScheduledTime(e.target.value)}
                />
              </div>
            </div>

            <div className="form-group">
              <label>Publicar en: *</label>
              {accounts.length === 0 ? (
                <div className="empty-state">
                  <p>No tienes cuentas conectadas</p>
                  <button
                    type="button"
                    onClick={() => navigate('/social-accounts')}
                    className="btn btn-secondary"
                  >
                    Conectar cuentas
                  </button>
                </div>
              ) : (
                <div className="accounts-selector">
                  {accounts.map((account) => (
                    <label key={account.id} className="account-checkbox">
                      <input
                        type="checkbox"
                        checked={selectedAccounts.includes(account.id)}
                        onChange={() => handleAccountToggle(account.id)}
                      />
                      <span className="platform-icon">
                        {getPlatformIcon(account.platform)}
                      </span>
                      <span className="account-name">
                        {account.platform} - {account.platform_username}
                      </span>
                    </label>
                  ))}
                </div>
              )}
            </div>

            <div className="form-actions">
              <button
                type="submit"
                className="btn btn-secondary"
                disabled={loading}
              >
                Guardar Borrador
              </button>
              <button
                type="button"
                onClick={(e) => handleSubmit(e, true)}
                className="btn btn-primary"
                disabled={loading}
              >
                {scheduledDate && scheduledTime
                  ? 'Programar Publicación'
                  : 'Publicar Ahora'}
              </button>
            </div>
          </form>
        </div>

        {/* Vista previa */}
        <div className="post-preview-section">
          <h2>Vista Previa</h2>
          <PostPreview
            content={content}
            imageUrl={imageUrl}
            platforms={selectedAccounts.map(id =>
              accounts.find(a => a.id === id)?.platform
            ).filter(Boolean)}
          />
        </div>
      </div>
    </div>
  );
};

export default CreatePost;
