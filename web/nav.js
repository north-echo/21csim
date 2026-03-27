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

  nav.setAttribute('role', 'navigation');
  nav.setAttribute('aria-label', 'Main navigation');

  const currentPath = window.location.pathname;

  nav.innerHTML = `
    <div class="nav-inner">
      <a href="/index.html" class="nav-logo" aria-label="21csim home">21csim</a>
      <button class="nav-hamburger" id="nav-hamburger" aria-label="Toggle navigation menu" aria-expanded="false" aria-controls="nav-links">
        <span class="hamburger-line"></span>
        <span class="hamburger-line"></span>
        <span class="hamburger-line"></span>
      </button>
      <div class="nav-links" id="nav-links" role="menubar">
        ${NAV_LINKS.map(link => {
          const isActive = link.id === activeId ||
            currentPath.endsWith(link.href) ||
            (link.id === 'viewer' && (currentPath === '/' || currentPath.includes('/century/')));
          return `<a href="${link.href}" class="nav-link ${isActive ? 'active' : ''}" role="menuitem" ${isActive ? 'aria-current="page"' : ''}>${link.label}</a>`;
        }).join('')}
      </div>
    </div>
  `;

  // Hamburger toggle
  const hamburger = document.getElementById('nav-hamburger');
  const navLinks = document.getElementById('nav-links');
  if (hamburger && navLinks) {
    hamburger.addEventListener('click', () => {
      const isOpen = navLinks.classList.toggle('nav-open');
      hamburger.classList.toggle('open', isOpen);
      hamburger.setAttribute('aria-expanded', String(isOpen));
    });

    // Close menu on Escape key
    navLinks.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        navLinks.classList.remove('nav-open');
        hamburger.classList.remove('open');
        hamburger.setAttribute('aria-expanded', 'false');
        hamburger.focus();
      }
    });
  }
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
  .nav-link:focus-visible {
    outline: 2px solid #6080ff;
    outline-offset: 2px;
  }

  /* Hamburger button */
  .nav-hamburger {
    display: none;
    flex-direction: column;
    justify-content: center;
    gap: 4px;
    background: none;
    border: 1px solid #2a2a3a;
    border-radius: 4px;
    cursor: pointer;
    padding: 6px 8px;
    margin-left: auto;
    width: 36px;
    height: 32px;
  }
  .nav-hamburger:hover { border-color: #6080ff; }
  .nav-hamburger:focus-visible {
    outline: 2px solid #6080ff;
    outline-offset: 2px;
  }
  .hamburger-line {
    display: block;
    width: 18px;
    height: 2px;
    background: #d0d0d8;
    border-radius: 1px;
    transition: transform 0.2s, opacity 0.2s;
  }
  .nav-hamburger.open .hamburger-line:nth-child(1) {
    transform: translateY(6px) rotate(45deg);
  }
  .nav-hamburger.open .hamburger-line:nth-child(2) {
    opacity: 0;
  }
  .nav-hamburger.open .hamburger-line:nth-child(3) {
    transform: translateY(-6px) rotate(-45deg);
  }

  /* Mobile nav: hamburger menu below 600px */
  @media (max-width: 600px) {
    .nav-hamburger {
      display: flex;
    }
    .nav-links {
      display: none;
      position: absolute;
      top: 44px;
      left: 0;
      right: 0;
      background: #08080c;
      border-bottom: 1px solid #1a1a2a;
      flex-direction: column;
      padding: 8px 16px;
      gap: 2px;
      z-index: 99;
    }
    .nav-links.nav-open {
      display: flex;
    }
    .nav-link {
      padding: 10px 12px;
      font-size: 14px;
    }
    .nav-inner {
      position: relative;
    }
  }
`;
document.head.appendChild(style);
