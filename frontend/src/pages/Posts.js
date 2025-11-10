/**
 * Página de listado de publicaciones
 */
import React, { useState, useEffect } from 'react';
import { postService } from '../services/api';
import { format } from 'date-fns';
import '../styles/Posts.css';

const Posts = () => {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState({ text: '', type: '' });

  useEffect(() => {
    loadPosts();
  }, []);

  const loadPosts = async () => {
    try {
      const data = await postService.getPosts();
      setPosts(data);
    } catch (error) {
      console.error('Error cargando publicaciones:', error);
      setMessage({ text: 'Error al cargar las publicaciones', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (postId) => {
    if (!window.confirm('¿Estás seguro de que deseas eliminar esta publicación?')) {
      return;
    }

    try {
      await postService.deletePost(postId);
      setMessage({ text: 'Publicación eliminada', type: 'success' });
      loadPosts();
    } catch (error) {
      console.error('Error eliminando publicación:', error);
      setMessage({ text: 'Error al eliminar la publicación', type: 'error' });
    }
  };

  const handlePublish = async (postId) => {
    if (!window.confirm('¿Deseas publicar esta publicación ahora?')) {
      return;
    }

    try {
      await postService.publishPost(postId);
      setMessage({
        text: 'Publicación en proceso de publicación',
        type: 'success'
      });
      loadPosts();
    } catch (error) {
      console.error('Error publicando:', error);
      setMessage({ text: 'Error al publicar', type: 'error' });
    }
  };

  const getStatusBadge = (status) => {
    const badges = {
      draft: { text: 'Borrador', class: 'badge-draft' },
      scheduled: { text: 'Programada', class: 'badge-scheduled' },
      publishing: { text: 'Publicando', class: 'badge-publishing' },
      published: { text: 'Publicada', class: 'badge-published' },
      failed: { text: 'Fallida', class: 'badge-failed' },
      partial: { text: 'Parcial', class: 'badge-partial' }
    };
    return badges[status] || { text: status, class: 'badge-default' };
  };

  const getPlatformIcon = (platformId) => {
    // Este es un placeholder, idealmente obtendrías la plataforma real
    return '📱';
  };

  if (loading) {
    return <div className="loading">Cargando...</div>;
  }

  return (
    <div className="posts-page">
      <div className="posts-header">
        <h1>Publicaciones</h1>
      </div>

      {message.text && (
        <div className={`message ${message.type}`}>
          {message.text}
          <button onClick={() => setMessage({ text: '', type: '' })}>×</button>
        </div>
      )}

      {posts.length === 0 ? (
        <div className="empty-state">
          <p>No tienes publicaciones</p>
          <a href="/create-post" className="btn btn-primary">
            Crear tu primera publicación
          </a>
        </div>
      ) : (
        <div className="posts-list">
          {posts.map((post) => {
            const badge = getStatusBadge(post.status);
            return (
              <div key={post.id} className="post-card">
                <div className="post-card-header">
                  <span className={`badge ${badge.class}`}>{badge.text}</span>
                  {post.scheduled_at && (
                    <span className="scheduled-time">
                      📅 {format(new Date(post.scheduled_at), 'dd/MM/yyyy HH:mm')}
                    </span>
                  )}
                </div>

                <div className="post-card-content">
                  <p>{post.content}</p>
                  {post.image_url && (
                    <div className="post-image">
                      <img src={post.image_url} alt="Post" />
                    </div>
                  )}
                </div>

                <div className="post-card-platforms">
                  <strong>Plataformas:</strong>
                  <div className="platforms-badges">
                    {post.platforms.map((platform) => (
                      <div key={platform.id} className="platform-status">
                        <span className="platform-icon">
                          {getPlatformIcon(platform.social_account_id)}
                        </span>
                        <span className={`status-indicator ${platform.status}`}>
                          {platform.status === 'published' && '✓'}
                          {platform.status === 'failed' && '✗'}
                          {platform.status === 'pending' && '⋯'}
                        </span>
                        {platform.error_message && (
                          <span className="error-tooltip" title={platform.error_message}>
                            ⚠
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                <div className="post-card-footer">
                  <div className="post-meta">
                    <span>Creada: {format(new Date(post.created_at), 'dd/MM/yyyy')}</span>
                    {post.published_at && (
                      <span>
                        Publicada: {format(new Date(post.published_at), 'dd/MM/yyyy HH:mm')}
                      </span>
                    )}
                  </div>

                  <div className="post-actions">
                    {post.status === 'draft' && (
                      <button
                        onClick={() => handlePublish(post.id)}
                        className="btn btn-sm btn-primary"
                      >
                        Publicar
                      </button>
                    )}
                    {(post.status === 'draft' || post.status === 'scheduled') && (
                      <button
                        onClick={() => handleDelete(post.id)}
                        className="btn btn-sm btn-danger"
                      >
                        Eliminar
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default Posts;
