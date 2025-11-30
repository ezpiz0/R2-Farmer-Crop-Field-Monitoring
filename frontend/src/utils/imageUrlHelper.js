/**
 * Helper utility for constructing correct image URLs
 * Handles both dev (localhost:3000) and production (nginx on 8080) environments
 */

/**
 * Get the correct base URL for image requests
 * Works in both dev and production environments
 */
export function getImageBaseUrl() {
  // In production (Docker), we're served through nginx on port 8080
  // which proxies /results/ to backend:8000/results/
  // In dev, vite.config.js proxies /results/ to localhost:8000/results/
  
  // Always use relative URL - it will work through proxy in both cases
  return '';
}

/**
 * Construct full image URL from API response
 * @param {string} imageUrl - Relative URL from API (e.g., "/results/uuid/file.png")
 * @returns {string} - Full URL ready for use in img src or ImageOverlay
 */
export function buildImageUrl(imageUrl) {
  if (!imageUrl) {
    console.error('buildImageUrl: imageUrl is empty');
    return null;
  }

  // Ensure URL starts with /
  let url = imageUrl.startsWith('/') ? imageUrl : `/${imageUrl}`;
  
  // Add cache busting timestamp to prevent browser caching issues
  const separator = url.includes('?') ? '&' : '?';
  url = `${url}${separator}t=${Date.now()}`;
  
  return url;
}

/**
 * Verify image URL is accessible
 * @param {string} url - Image URL to check
 * @returns {Promise<boolean>} - True if image is accessible
 */
export async function verifyImageUrl(url) {
  try {
    const response = await fetch(url, { method: 'HEAD', cache: 'no-cache' });
    return response.ok;
  } catch (error) {
    console.error('Image URL verification failed:', error);
    return false;
  }
}

