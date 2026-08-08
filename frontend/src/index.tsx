/* @refresh reload */
import { render } from 'solid-js/web'
import { Route, Router, useLocation } from "@solidjs/router";
import { createEffect, createSignal } from 'solid-js';
import { SolidQueryDevtools } from '@tanstack/solid-query-devtools'
import { QueryClient, QueryClientProvider } from '@tanstack/solid-query';

import Home from './pages/home.tsx';
import NovelsPage from './pages/novels.tsx';

// import '@knadh/oat/oat.min.css';
// import '@knadh/oat/oat.min.js';
import NovelsFetchingPage from './pages/novels-fetching.tsx';
import NovelsUpdatingPage from './pages/novels-updating.tsx';


const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 mins
    },
  },
})

const toggleTheme = () => {
  const colorScheme = document.documentElement.style.colorScheme;
  const isDark = colorScheme === 'dark' || (!colorScheme && matchMedia('(prefers-color-scheme: dark)').matches);
  let theme = isDark ? 'light' : 'dark';
  document.documentElement.style.colorScheme = theme;
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('theme', theme);
}

const getStoredTheme = () => {
  let theme = localStorage.getItem('theme')
  if (!theme) {
    const colorScheme = document.documentElement.style.colorScheme;
    const isDark = colorScheme === 'dark' || (!colorScheme && matchMedia('(prefers-color-scheme: dark)').matches);
    theme = isDark ? 'light' : 'dark';
  }
  document.documentElement.style.colorScheme = theme;
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('theme', theme);
}

// Assumes backend is running on the same host as the frontend via docker-compose or similar
export const BACKEND_IP =  window.location.protocol + "//" + window.location.hostname + ":13912"


function Layout(props: { children?: any }) {
  const [location, setLocation] = createSignal(useLocation().pathname)
  getStoredTheme()

  createEffect(() => {
    setLocation(useLocation().pathname);
  });

  return (
    <>
      <nav data-topnav>
        <button data-sidebar-toggle aria-label="Toggle menu" class="outline" style="width: 40px; height: 40px;">
          ☰
        </button>
        <button aria-labbel="Toggle theme" class="outline" style="width: 40px; height: 40px;" onClick={() => toggleTheme()}>
          🌙
        </button>
        <span>Syosetu-Epubifier</span>
      </nav>

      <aside data-sidebar>
        <nav>
          <ul style="list-style-type: none; list-style: none; padding-inline-start: 0; padding-left: 0;">
            <li><a style="text-decoration: none" href="/" aria-current={location() === "/" ? "page" : undefined}>Home</a></li>
            <li>
              <details open>
                <summary>小説</summary>
                <ul style="list-style-type: none;">
                  <li><a style="text-decoration: none" href="/novels" aria-current={location() === "/novels" ? "page" : undefined}>小説リスト</a></li>
                  <li><a style="text-decoration: none" href="/novels/updating" aria-current={location() === "/novels/updating" ? "page" : undefined}>更新中</a></li>
                  <li><a style="text-decoration: none" href="/novels/fetching" aria-current={location() === "/novels/fetching" ? "page" : undefined}>追加中</a></li>
                </ul>
              </details>
            </li>
          </ul>
        </nav>
        {/* <footer>
          <button class="outline small" style="width: 100%">Logout</button>
        </footer> */}
      </aside>

      <main>
        <QueryClientProvider client={queryClient}>
          <SolidQueryDevtools initialIsOpen={false} />
          <div style="padding: var(--space-3)">
            {props.children}
          </div>
        </QueryClientProvider>
      </main>

    </>
  )

}

// render(() => <App />, root!)
render(() => (
  <Router root={Layout}>
    <Route path="/" component={Home} />
    <Route path="/novels" component={NovelsPage} />
    <Route path="/novels/fetching" component={NovelsFetchingPage} />
    <Route path="/novels/updating" component={NovelsUpdatingPage} />
  </Router>
), document.body);
