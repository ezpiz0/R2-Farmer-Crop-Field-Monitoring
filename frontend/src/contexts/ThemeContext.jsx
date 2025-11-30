import React, { createContext, useState, useEffect, useContext } from 'react'

const ThemeContext = createContext()

export function ThemeProvider({ children }) {
  const [isDarkTheme, setIsDarkTheme] = useState(() => {
    const savedTheme = localStorage.getItem('theme')
    return savedTheme === 'dark'
  })

  useEffect(() => {
    const theme = isDarkTheme ? 'dark' : 'light'
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('theme', theme)
  }, [isDarkTheme])

  const toggleTheme = () => {
    setIsDarkTheme(prev => !prev)
  }

  return (
    <ThemeContext.Provider value={{ isDarkTheme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  const context = useContext(ThemeContext)
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider')
  }
  return context
}

