(() => {
  'use strict';
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const menuButton = document.getElementById('navToggle');
  const menu = document.getElementById('navLinks');
  const setMenu = open => {
    menu?.classList.toggle('open', open);
    menuButton?.setAttribute('aria-expanded', String(open));
    menuButton?.setAttribute('aria-label', open ? 'Close navigation' : 'Open navigation');
  };
  menuButton?.addEventListener('click', () => setMenu(menuButton.getAttribute('aria-expanded') !== 'true'));
  menu?.addEventListener('click', event => { if (event.target.closest('a')) setMenu(false); });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && menuButton?.getAttribute('aria-expanded') === 'true') {
      setMenu(false); menuButton.focus();
    }
  });
  window.matchMedia('(min-width: 1121px)').addEventListener('change', () => setMenu(false));

  // Open an anchored technical section when it sits inside closed details.
  const revealTarget = hash => {
    let id;
    try { id = decodeURIComponent(hash.slice(1)); } catch { return null; }
    const target = document.getElementById(id);
    if (!target) return null;
    let node = target;
    while (node) { if (node.tagName === 'DETAILS') node.open = true; node = node.parentElement; }
    return target;
  };
  document.addEventListener('click', event => {
    const link = event.target.closest('a[href^="#"]');
    if (link) revealTarget(link.getAttribute('href'));
  });
  window.addEventListener('hashchange', () => revealTarget(location.hash));
  if (location.hash) {
    const target = revealTarget(location.hash);
    if (target) requestAnimationFrame(() => target.scrollIntoView());
  }
  const progress = document.getElementById('scrollProgress');
  const header = document.getElementById('nav');
  const hero = document.getElementById('top');
  let navVisible = null;
  const links = [...document.querySelectorAll('.nav-links a')];
  const targets = links.map(link => ({link, target: document.getElementById(link.hash.slice(1))})).filter(item => item.target);
  const toc = document.getElementById('toc');
  const tocGroups = [...(toc?.querySelectorAll('.toc-group') || [])];
  const tocTargets = [...(toc?.querySelectorAll('a[href^="#"]') || [])]
    .map(link => ({link, target:document.getElementById(link.hash.slice(1)), group:link.closest('.toc-group')}))
    .filter(item => item.target);
  let queued = false;
  const updateScroll = () => {
    queued = false;
    // Reveal the fixed menu as the content below the full-screen video reaches it.
    const headerHeight = header?.getBoundingClientRect().height || 66;
    const showNav = !hero || hero.getBoundingClientRect().bottom <= headerHeight + 17;
    if (header && showNav !== navVisible) {
      navVisible = showNav;
      if (!showNav) {
        setMenu(false);
        if (header.contains(document.activeElement)) {
          hero?.querySelector('.hero-scroll')?.focus({preventScroll: true});
        }
      }
      header.classList.toggle('nav-hidden', !showNav);
      header.inert = !showNav;
      header.setAttribute('aria-hidden', String(!showNav));
    }
    const height = document.documentElement.scrollHeight - window.innerHeight;
    if (progress) progress.style.width = `${height > 0 ? Math.min(100, Math.max(0, window.scrollY / height * 100)) : 0}%`;
    let current = null;
    for (const item of targets) if (item.target.getBoundingClientRect().top <= 150) current = item;
    for (const item of targets) {
      item.link.classList.toggle('active',item === current);
      if (item === current) item.link.setAttribute('aria-current', 'location');
      else item.link.removeAttribute('aria-current');
    }
    if (toc) {
      toc.classList.toggle('toc-hidden', !showNav);
      let active = tocTargets[0];
      for (const item of tocTargets) if (item.target.getBoundingClientRect().top <= 160) active = item;
      tocGroups.forEach(group => group.classList.toggle('open',group === active?.group));
      tocTargets.forEach(item => {
        item.link.classList.toggle('active', item === active || (item.group === active?.group && item.link.parentElement === item.group));
        if (item === active) item.link.setAttribute('aria-current','location');
        else item.link.removeAttribute('aria-current');
      });
    }
  };
  const queueScroll = () => { if (!queued) { queued = true; requestAnimationFrame(updateScroll); } };
  window.addEventListener('scroll', queueScroll, {passive:true});
  window.addEventListener('resize', queueScroll, {passive:true});
  window.addEventListener('pageshow', queueScroll);
  window.addEventListener('load', queueScroll);
  document.addEventListener('toggle', queueScroll, true);
  updateScroll();
  if ('ResizeObserver' in window) {
    new ResizeObserver(entries => {
      const headerHeight = Math.ceil(entries[0].target.getBoundingClientRect().height);
      document.documentElement.style.setProperty('--nav-height', `${headerHeight}px`);
      queueScroll();
    }).observe(document.getElementById('nav'));
  }

  // Works on hosted pages and documents opened directly from disk.
  document.getElementById('copyBib')?.addEventListener('click', async () => {
    const code = document.querySelector('.bibtex code');
    const status = document.getElementById('copyStatus');
    if (!code || !status) return;
    let success = false;
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(code.textContent); success = true;
      }
    } catch { /* Local files use the text-selection fallback. */ }
    if (!success) {
      const area = document.createElement('textarea');
      area.value = code.textContent;
      area.style.cssText = 'position:fixed;left:-9999px;top:0;';
      document.body.appendChild(area); area.select();
      try { success = document.execCommand('copy'); } catch { success = false; }
      area.remove();
      document.getElementById('copyBib').focus();
    }
    if (success) status.textContent = 'BibTeX copied.';
    else {
      const range = document.createRange(); range.selectNodeContents(code);
      const selection = window.getSelection(); selection.removeAllRanges(); selection.addRange(range);
      status.textContent = 'Citation selected. Press Ctrl+C or ⌘C to copy.';
    }
  });

  const featured = document.getElementById('featuredRollout');
  const buttons = [...document.querySelectorAll('[data-rollout]')];
  const rollouts = [
    {slug:'tongs', title:'Tongs', description:'Tool-mediated force control'},
    {slug:'bowl_destack', title:'Bowl unstacking', description:'Friction-dependent separation'},
    {slug:'bottle_cap', title:'Bottle cap unscrewing', description:'Friction and rotational contact'},
    {slug:'wipe_whiteboard', title:'Two-hand wipe', description:'Sustained surface contact'}
  ];
  let rolloutIndex = 0;
  const safePlay = video => { const promise = video.play(); if (promise?.catch) promise.catch(() => {}); };
  const showRollout = (index, shouldPlay = true) => {
    rolloutIndex = (index + rollouts.length) % rollouts.length;
    const rollout = rollouts[rolloutIndex];
    featured.src = `static/videos/web/tasks/${rollout.slug}.mp4`;
    featured.poster = `static/videos/web/tasks/${rollout.slug}_poster.jpg?v=20260916-2`;
    featured.setAttribute('aria-label', `Featured autonomous ${rollout.title.toLowerCase()} rollout`);
    document.getElementById('featuredRolloutTitle').textContent = rollout.title;
    document.getElementById('featuredRolloutDescription').textContent = rollout.description;
    buttons.forEach((button,i) => {button.classList.toggle('active', i === rolloutIndex);button.setAttribute('aria-pressed',String(i === rolloutIndex));});
    featured.load(); featured.playbackRate = 2;
    if (shouldPlay) safePlay(featured);
  };
  if (featured) {
    const playbackButton = document.getElementById('heroPlayback');
    const refreshPlaybackButton = () => {
      if (!playbackButton) return;
      playbackButton.querySelector('.playback-icon').textContent = featured.paused ? '▶' : 'Ⅱ';
      playbackButton.querySelector('.playback-text').textContent = featured.paused ? 'Play video' : 'Pause video';
      playbackButton.setAttribute('aria-label', featured.paused ? 'Play background video' : 'Pause background video');
    };
    playbackButton?.addEventListener('click', () => { if (featured.paused) safePlay(featured); else featured.pause(); });
    featured.addEventListener('play', refreshPlaybackButton);
    featured.addEventListener('pause', refreshPlaybackButton);
    featured.addEventListener('ended', refreshPlaybackButton);
    refreshPlaybackButton();
    featured.playbackRate = 2;
    featured.addEventListener('loadedmetadata', () => { featured.playbackRate = 2; });
    featured.addEventListener('ended', () => { if (!reducedMotion.matches) showRollout(rolloutIndex + 1); });
    buttons.forEach(button => button.addEventListener('click', () => showRollout(Number(button.dataset.rollout), true)));
  }

  // Play only visible videos, while respecting explicit pauses and reduced motion.
  const videos = [...document.querySelectorAll('video')];
  const state = new WeakMap(videos.map(video => [video, {visible:false, pausedByViewer:false, internalPause:false, resumeOnVisible:false}]));
  const pauseInternally = video => {
    const s = state.get(video);
    if (!video.paused) { s.resumeOnVisible = true; s.internalPause = true; video.pause(); }
  };
  videos.forEach(video => {
    video.addEventListener('pause', () => {
      const s = state.get(video);
      if (s.internalPause) s.internalPause = false;
      else if (!video.ended && video.readyState >= 2 && s.visible && !document.hidden) s.pausedByViewer = true;
    });
    video.addEventListener('play', () => {
      const s = state.get(video); s.pausedByViewer = false; s.resumeOnVisible = false;
    });
  });
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        const video = entry.target, s = state.get(video);
        s.visible = entry.isIntersecting && entry.intersectionRatio >= 0.25;
        if (s.visible && !document.hidden && !s.pausedByViewer && !reducedMotion.matches) safePlay(video);
        else if (!s.visible) pauseInternally(video);
      });
    }, {threshold:[0,0.25]});
    videos.forEach(video => observer.observe(video));
  }
  document.addEventListener('visibilitychange', () => videos.forEach(video => {
    const s = state.get(video);
    if (document.hidden) pauseInternally(video);
    else if (s.visible && s.resumeOnVisible && !s.pausedByViewer && !reducedMotion.matches) safePlay(video);
  }));
  reducedMotion.addEventListener('change', () => { if (reducedMotion.matches) videos.forEach(pauseInternally); });

  // Retain the scroll-triggered bar animation without comparison or hover text.
  const chart = document.getElementById('averageScoreChart');
  if (chart) {
    const bars = [...chart.querySelectorAll('.bar-fill')];
    let frame = 0;
    let animated = false;
    const finish = () => {
      cancelAnimationFrame(frame);
      bars.forEach(bar => { bar.style.transform = 'scaleX(1)'; });
    };
    const animate = () => {
      if (animated) return;
      animated = true;
      if (reducedMotion.matches) { finish(); return; }
      cancelAnimationFrame(frame);
      const start = performance.now();
      bars.forEach(bar => { bar.style.transform = 'scaleX(0)'; });
      const tick = now => {
        let complete = true;
        bars.forEach((bar, index) => {
          const t = Math.min(1, Math.max(0, (now - start - index * 90) / 950));
          bar.style.transform = `scaleX(${1 - Math.pow(1 - t, 3)})`;
          if (t < 1) complete = false;
        });
        if (complete) finish();
        else frame = requestAnimationFrame(tick);
      };
      frame = requestAnimationFrame(tick);
    };
    if ('IntersectionObserver' in window) {
      // Replay on every pass, but only re-arm once the chart has fully left the
      // viewport so that scrolling near the trigger point cannot restart it.
      const observer = new IntersectionObserver(entries => {
        entries.forEach(entry => {
          if (entry.intersectionRatio >= 0.45) animate();
          else if (entry.intersectionRatio === 0) animated = false;
        });
      }, {threshold: [0, 0.45]});
      observer.observe(chart);
    } else animate();
    reducedMotion.addEventListener('change', () => { if (reducedMotion.matches) finish(); });
  }
})();
