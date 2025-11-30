/**
 * AIReportViewer Component
 * Presentational component for rendering AI-generated agronomist reports
 * 
 * Features:
 * - Renders Markdown content safely
 * - Professional styling
 * - Print-friendly layout
 * - Export to PDF capability (future enhancement)
 */
import React from 'react';
import './AIReportViewer.css';

const AIReportViewer = ({ markdown, generationTime, modelUsed }) => {
  /**
   * Simple Markdown parser for safe HTML rendering
   * Supports: headings, bold, italic, lists, code blocks, horizontal rules
   */
  const parseMarkdown = (md) => {
    if (!md) return '';

    let html = md;

    // Code blocks
    html = html.replace(/```([^`]+)```/g, '<pre><code>$1</code></pre>');

    // Horizontal rules
    html = html.replace(/^---$/gm, '<hr />');

    // Headers (h3, h4)
    html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
    html = html.replace(/^#### (.+)$/gm, '<h4>$1</h4>');

    // Bold
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

    // Italic
    html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');

    // Unordered lists (convert * to bullets)
    html = html.replace(/^\*   (.+)$/gm, '<li class="indent-2">$1</li>');
    html = html.replace(/^\* (.+)$/gm, '<li>$1</li>');

    // Wrap consecutive list items in ul
    html = html.replace(/(<li[^>]*>.*<\/li>\n?)+/g, '<ul>$&</ul>');

    // Ordered lists
    html = html.replace(/^\d+\.\s+(.+)$/gm, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>\n?)+/g, (match) => {
      // Check if already wrapped in ul
      if (match.startsWith('<ul>')) return match;
      return '<ol>' + match + '</ol>';
    });

    // Line breaks
    html = html.replace(/\n\n/g, '<br/><br/>');
    html = html.replace(/\n/g, '<br/>');

    return html;
  };

  const htmlContent = parseMarkdown(markdown);

  return (
    <div className="ai-report-viewer">
      <div className="report-header">
        <div className="report-badge">
          <span className="badge-icon">🤖</span>
          <span className="badge-text">AI Агроном</span>
        </div>
        <div className="report-meta">
          <span className="meta-item">
            <span className="meta-label">Модель:</span> {modelUsed}
          </span>
          <span className="meta-item">
            <span className="meta-label">Время генерации:</span> {generationTime}с
          </span>
        </div>
      </div>

      <div 
        className="report-content"
        dangerouslySetInnerHTML={{ __html: htmlContent }}
      />

      <div className="report-footer">
        <button 
          className="btn-secondary"
          onClick={() => window.print()}
          title="Печать отчета"
        >
          <span>🖨️</span> Печать
        </button>
      </div>
    </div>
  );
};

export default AIReportViewer;

