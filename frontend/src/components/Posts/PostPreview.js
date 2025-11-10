/**
 * Componente de vista previa de publicación
 * Muestra cómo se verá el contenido en cada plataforma
 */
import React from 'react';
import '../../styles/PostPreview.css';

const PostPreview = ({ content, imageUrl, platforms = [] }) => {
  const truncateText = (text, maxLength) => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  const renderPreview = (platform) => {
    switch (platform) {
      case 'facebook':
        return (
          <div className="preview-card facebook">
            <div className="preview-header">
              <div className="preview-icon">📘</div>
              <div>
                <div className="preview-name">Tu Perfil de Facebook</div>
                <div className="preview-time">Justo ahora</div>
              </div>
            </div>
            <div className="preview-content">
              <p>{content || 'Tu contenido aparecerá aquí...'}</p>
              {imageUrl && (
                <div className="preview-image">
                  <img src={imageUrl} alt="Preview" />
                </div>
              )}
            </div>
          </div>
        );

      case 'instagram':
        return (
          <div className="preview-card instagram">
            <div className="preview-header">
              <div className="preview-icon">📷</div>
              <div>
                <div className="preview-name">tu_usuario</div>
              </div>
            </div>
            {imageUrl ? (
              <>
                <div className="preview-image">
                  <img src={imageUrl} alt="Preview" />
                </div>
                <div className="preview-content">
                  <p>
                    <strong>tu_usuario</strong>{' '}
                    {content || 'Tu caption aparecerá aquí...'}
                  </p>
                </div>
              </>
            ) : (
              <div className="preview-placeholder">
                Instagram requiere una imagen
              </div>
            )}
          </div>
        );

      case 'twitter':
        return (
          <div className="preview-card twitter">
            <div className="preview-header">
              <div className="preview-icon">🐦</div>
              <div>
                <div className="preview-name">Tu Usuario</div>
                <div className="preview-handle">@tuusuario</div>
              </div>
            </div>
            <div className="preview-content">
              <p>{truncateText(content, 280) || 'Tu tweet aparecerá aquí...'}</p>
              {content.length > 280 && (
                <div className="preview-warning">
                  Truncado a 280 caracteres
                </div>
              )}
              {imageUrl && (
                <div className="preview-image">
                  <img src={imageUrl} alt="Preview" />
                </div>
              )}
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="post-preview">
      {platforms.length === 0 ? (
        <div className="preview-empty">
          Selecciona una plataforma para ver la vista previa
        </div>
      ) : (
        platforms.map((platform, index) => (
          <div key={index}>{renderPreview(platform)}</div>
        ))
      )}
    </div>
  );
};

export default PostPreview;
