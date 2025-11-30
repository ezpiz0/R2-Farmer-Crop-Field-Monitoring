import React from 'react'
import './ErrorPage.css'

function ErrorPage({ errorCode = '404', errorMessage = 'Страница не найдена' }) {
  const getErrorDetails = () => {
    switch (errorCode) {
      case '404':
        return {
          title: 'Урожай не найден! 😢',
          description: 'Кажется, вы забрели не на то поле...',
          tip: 'Проверьте адрес или вернитесь на главную страницу'
        }
      case '500':
        return {
          title: 'Неурожай на сервере! 😭',
          description: 'Что-то пошло не так с нашими полями...',
          tip: 'Попробуйте обновить страницу или вернуться позже'
        }
      case '403':
        return {
          title: 'Доступ запрещен! 🚜',
          description: 'Это частное поле, вход запрещен!',
          tip: 'У вас нет прав для доступа к этому ресурсу'
        }
      default:
        return {
          title: 'Что-то пошло не так! 🌾',
          description: errorMessage || 'Произошла непредвиденная ошибка',
          tip: 'Попробуйте вернуться на главную страницу'
        }
    }
  }

  const details = getErrorDetails()

  const handleGoHome = () => {
    window.location.href = '/'
  }

  return (
    <div className="error-page">
      <div className="error-clouds">
        <div className="cloud cloud-1"></div>
        <div className="cloud cloud-2"></div>
        <div className="cloud cloud-3"></div>
      </div>

      <div className="error-content">
        {/* Плачущий фермер */}
        <div className="farmer-container">
          <div className="farmer">
            {/* Шляпа */}
            <div className="hat">
              <div className="hat-top"></div>
              <div className="hat-brim"></div>
            </div>
            
            {/* Голова */}
            <div className="farmer-head">
              {/* Слезы */}
              <div className="tear tear-left"></div>
              <div className="tear tear-right"></div>
              
              {/* Глаза */}
              <div className="eyes">
                <div className="eye eye-left">
                  <div className="pupil"></div>
                </div>
                <div className="eye eye-right">
                  <div className="pupil"></div>
                </div>
              </div>
              
              {/* Рот */}
              <div className="mouth"></div>
              
              {/* Усы */}
              <div className="mustache"></div>
            </div>
            
            {/* Тело */}
            <div className="farmer-body">
              <div className="overalls">
                <div className="strap strap-left"></div>
                <div className="strap strap-right"></div>
                <div className="pocket"></div>
              </div>
            </div>

            {/* Руки */}
            <div className="arm arm-left"></div>
            <div className="arm arm-right"></div>
          </div>

          {/* Увядшее растение */}
          <div className="dead-plant">
            <div className="plant-stem"></div>
            <div className="plant-leaf plant-leaf-1"></div>
            <div className="plant-leaf plant-leaf-2"></div>
          </div>
        </div>

        {/* Код ошибки */}
        <div className="error-code-display">
          <span className="error-number">{errorCode}</span>
        </div>

        {/* Текст ошибки */}
        <div className="error-text">
          <h1>{details.title}</h1>
          <p className="error-description">{details.description}</p>
          <p className="error-tip">💡 {details.tip}</p>
        </div>

        {/* Кнопки действий */}
        <div className="error-actions">
          <button className="btn btn-primary btn-large" onClick={handleGoHome}>
            🏠 Вернуться на главную
          </button>
          <button className="btn btn-secondary btn-large" onClick={() => window.location.reload()}>
            🔄 Обновить страницу
          </button>
        </div>

        {/* Декоративные элементы */}
        <div className="field-decoration">
          <div className="wheat wheat-1">🌾</div>
          <div className="wheat wheat-2">🌾</div>
          <div className="wheat wheat-3">🌾</div>
          <div className="tractor">🚜</div>
        </div>
      </div>
    </div>
  )
}

export default ErrorPage

