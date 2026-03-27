// nav.js -- Shared navigation header injected into all pages

const NAV_LINKS = [
  { href: '/index.html', label: 'Viewer', id: 'viewer' },
  { href: '/explore.html', label: 'Explorer', id: 'explore' },
  { href: '/findings.html', label: 'Findings', id: 'findings' },
  { href: '/about.html', label: 'About', id: 'about' },
];

export function initNav(activeId) {
  const nav = document.getElementById('site-nav');
  if (!nav) return;

  const currentPath = window.location.pathname;

  nav.innerHTML = `
    <div class="nav-inner">
      <a href="/index.html" class="nav-logo">21csim</a>
      <div class="nav-links">
        ${NAV_LINKS.map(link => {
          const isActive = link.id === activeId ||
            currentPath.endsWith(link.href) ||
            (link.id === 'viewer' && (currentPath === '/' || currentPath.includes('/century/')));
          return `<a href="${link.href}" class="nav-link ${isActive ? 'active' : ''}">${link.label}</a>`;
        }).join('')}
      </div>
    </div>
  `;
}

// Auto-inject nav styles
const style = document.createElement('style');
style.textContent = `
  #site-nav {
    background: #08080c;
    border-bottom: 1px solid #1a1a2a;
    padding: 0 16px;
    position: sticky;
    top: 0;
    z-index: 100;
  }
  .nav-inner {
    max-width: 1400px;
    margin: 0 auto;
    display: flex;
    align-items: center;
    height: 44px;
    gap: 24px;
  }
  .nav-logo {
    font-family: 'JetBrains Mono', 'Fira Code', 'SF Mono', monospace;
    font-size: 16px;
    font-weight: 700;
    color: #f0f0ff;
    text-decoration: none;
    letter-spacing: 1px;
  }
  .nav-logo:hover { color: #6080ff; }
  .nav-links {
    display: flex;
    gap: 4px;
  }
  .nav-link {
    font-family: -apple-system, system-ui, sans-serif;
    font-size: 13px;
    color: #808090;
    text-decoration: none;
    padding: 6px 12px;
    border-radius: 4px;
    transition: color 0.15s, background 0.15s;
  }
  .nav-link:hover {
    color: #d0d0d8;
    background: #1a1a26;
  }
  .nav-link.active {
    color: #f0f0ff;
    background: #1a1a26;
  }
`;
document.head.appendChild(style);
