import React from 'react'
import ErrorPage from './ErrorPage'

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { 
      hasError: false,
      error: null,
      errorInfo: null
    }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true }
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error caught by boundary:', error, errorInfo)
    this.state = {
      hasError: true,
      error: error,
      errorInfo: errorInfo
    }
  }

  render() {
    if (this.state.hasError) {
      return (
        <ErrorPage 
          errorCode="500" 
          errorMessage="Произошла непредвиденная ошибка в приложении"
        />
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary

