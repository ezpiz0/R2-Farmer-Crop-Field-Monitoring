import React from 'react'
import './ThemeToggle.css'

function ThemeToggle({ isDark, onToggle }) {
  return (
    <button 
      className="theme-toggle" 
      onClick={onToggle}
      aria-label={isDark ? 'Переключить на светлую тему' : 'Переключить на темную тему'}
      title={isDark ? 'Светлая тема' : 'Темная тема'}
    >
      <span className="theme-label">
        {isDark ? '🌙 Темная тема' : '☀️ Светлая тема'}
      </span>
      <div className="toggle-track">
        <div className={`toggle-thumb ${isDark ? 'dark' : 'light'}`}>
          {isDark ? '🌙' : '☀️'}
        </div>
      </div>
    </button>
  )
}

export default ThemeToggle

