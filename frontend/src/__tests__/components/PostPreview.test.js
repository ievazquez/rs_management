/**
 * Tests para componente PostPreview
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import PostPreview from '../../components/Posts/PostPreview';

describe('PostPreview Component', () => {
  it('should render empty state when no platforms selected', () => {
    render(<PostPreview content="Test content" imageUrl="" platforms={[]} />);

    expect(screen.getByText(/selecciona una plataforma/i)).toBeInTheDocument();
  });

  it('should render Facebook preview', () => {
    render(
      <PostPreview
        content="Facebook post content"
        imageUrl=""
        platforms={['facebook']}
      />
    );

    expect(screen.getByText('Facebook post content')).toBeInTheDocument();
    expect(screen.getByText('Tu Perfil de Facebook')).toBeInTheDocument();
  });

  it('should render Instagram preview with image', () => {
    render(
      <PostPreview
        content="Instagram caption"
        imageUrl="https://example.com/image.jpg"
        platforms={['instagram']}
      />
    );

    expect(screen.getByText(/Instagram caption/i)).toBeInTheDocument();
    expect(screen.getByAltText('Preview')).toHaveAttribute(
      'src',
      'https://example.com/image.jpg'
    );
  });

  it('should render Instagram placeholder when no image', () => {
    render(
      <PostPreview content="Caption" imageUrl="" platforms={['instagram']} />
    );

    expect(screen.getByText(/instagram requiere una imagen/i)).toBeInTheDocument();
  });

  it('should render Twitter preview with truncation warning', () => {
    const longText = 'a'.repeat(300);

    render(<PostPreview content={longText} imageUrl="" platforms={['twitter']} />);

    expect(screen.getByText(/truncado a 280 caracteres/i)).toBeInTheDocument();
  });

  it('should render multiple platform previews', () => {
    render(
      <PostPreview
        content="Multi-platform post"
        imageUrl="https://example.com/image.jpg"
        platforms={['facebook', 'twitter', 'instagram']}
      />
    );

    expect(screen.getByText('Tu Perfil de Facebook')).toBeInTheDocument();
    expect(screen.getByText('@tuusuario')).toBeInTheDocument();
    expect(screen.getByText('tu_usuario')).toBeInTheDocument();
  });

  it('should display image when provided', () => {
    render(
      <PostPreview
        content="Post with image"
        imageUrl="https://example.com/test.jpg"
        platforms={['facebook']}
      />
    );

    const images = screen.getAllByAltText('Preview');
    expect(images[0]).toHaveAttribute('src', 'https://example.com/test.jpg');
  });

  it('should handle empty content gracefully', () => {
    render(<PostPreview content="" imageUrl="" platforms={['facebook']} />);

    expect(screen.getByText(/tu contenido aparecerá aquí/i)).toBeInTheDocument();
  });
});
