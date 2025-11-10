/**
 * Layout principal de la aplicación
 * Incluye navegación y estructura general
 */
import React from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import '../../styles/Layout.css';

const Layout = ({ children }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const isActive = (path) => {
    return location.pathname === path ? 'active' : '';
  };

  return (
    <div className="layout">
      <nav className="navbar">
        <div className="navbar-brand">
          <h1>Social Media Manager</h1>
        </div>

        <div className="navbar-menu">
          <Link to="/dashboard" className={`nav-item ${isActive('/dashboard')}`}>
            Dashboard
          </Link>
          <Link to="/posts" className={`nav-item ${isActive('/posts')}`}>
            Publicaciones
          </Link>
          <Link to="/create-post" className={`nav-item ${isActive('/create-post')}`}>
            Nueva Publicación
          </Link>
          <Link to="/social-accounts" className={`nav-item ${isActive('/social-accounts')}`}>
            Cuentas Sociales
          </Link>
        </div>

        <div className="navbar-user">
          <span className="user-name">{user?.username}</span>
          <button onClick={handleLogout} className="btn-logout">
            Cerrar Sesión
          </button>
        </div>
      </nav>

      <main className="main-content">
        {children}
      </main>
    </div>
  );
};

export default Layout;
