import { useState } from 'react'
import { ChevronUp, ChevronDown } from 'lucide-react'

const TICKER_ITEMS = [
  'Brand Identity',
  'App Development',
  'Visual Design',
  'Creative Video',
  'Iconography',
]

const COMPANIES = [
  { name: 'Airbnb', cls: 'airbnb' },
  { name: 'Shopify', cls: 'shopify' },
  { name: 'Notion', cls: 'notion' },
  { name: 'Linear', cls: 'linear' },
  { name: 'Webflow', cls: 'webflow' },
  { name: 'Figma', cls: 'figma' },
  { name: 'Slack', cls: 'slack' },
  { name: 'Stripe', cls: 'stripe' },
  { name: 'Vercel', cls: 'vercel' },
  { name: 'Framer', cls: 'framer' },
]

const DRAWER_LINKS = ['Projects', 'Plans', 'Team', 'FAQs', 'Get in Touch']

// 20 curved lines per side — staggered, widths grow by 10px each
const SIDE_LINES = Array.from({ length: 20 }, (_, i) => i)
// 10 top horizontal lines for mobile
const TOP_LINES = Array.from({ length: 10 }, (_, i) => i)

function CurvedLines() {
  return (
    <>
      <div className="curved-left" aria-hidden="true">
        {SIDE_LINES.map((i) => (
          <div
            key={`l-${i}`}
            className="curve-line left"
            style={{
              left: `${10 + i * 5}px`,
              top: `${130 + i * 22}px`,
              width: `${60 + i * 10}px`,
              height: `${340 - i * 7}px`,
              animationDelay: `${i * 0.25}s`,
            }}
          />
        ))}
      </div>
      <div className="curved-right" aria-hidden="true">
        {SIDE_LINES.map((i) => (
          <div
            key={`r-${i}`}
            className="curve-line right"
            style={{
              right: `${10 + i * 5}px`,
              top: `${130 + i * 22}px`,
              width: `${60 + i * 10}px`,
              height: `${340 - i * 7}px`,
              animationDelay: `${i * 0.25}s`,
            }}
          />
        ))}
      </div>
      <div className="top-lines" aria-hidden="true">
        {TOP_LINES.map((i) => (
          <div
            key={`t-${i}`}
            className="top-line"
            style={{
              left: `${i * 9}%`,
              top: `${i * 6}px`,
              width: `${120 + i * 10}px`,
              height: `${60 + i * 8}px`,
              animationDelay: `${i * 0.25}s`,
            }}
          />
        ))}
      </div>
    </>
  )
}

function Ticker() {
  // 4x duplicated for a seamless -50% loop
  const row = [...TICKER_ITEMS, ...TICKER_ITEMS, ...TICKER_ITEMS, ...TICKER_ITEMS]
  return (
    <div className="ticker-row">
      <div className="ticker-track">
        {row.map((item, idx) => (
          <span className="ticker-item" key={idx}>
            {item}
          </span>
        ))}
      </div>
    </div>
  )
}

function TrustedBy() {
  const row = [...COMPANIES, ...COMPANIES, ...COMPANIES, ...COMPANIES]
  return (
    <section className="trusted">
      <div className="trusted-label">
        Partnered with top-tier companies globally
      </div>
      <div className="trusted-marquee">
        <div className="trusted-track">
          {row.map((c, idx) => (
            <span className={`company ${c.cls}`} key={idx}>
              {c.name}
            </span>
          ))}
        </div>
      </div>
    </section>
  )
}

function Navbar({ open, setOpen }) {
  return (
    <>
      <nav className="navbar">
        <div className="navbar-inner">
          <div className="logo">
            Alwayzz<sup>®</sup>
          </div>
          <button className="menu-btn" onClick={() => setOpen(true)}>
            Menu
            <ChevronUp />
          </button>
        </div>
      </nav>

      <div className={`drawer ${open ? 'open' : ''}`}>
        <div className="drawer-top">
          <div className="logo">
            Alwayzz<sup>®</sup>
          </div>
          <button className="drawer-close" onClick={() => setOpen(false)}>
            Close
            <ChevronDown />
          </button>
        </div>
        <div className="drawer-links">
          {DRAWER_LINKS.map((l) => (
            <a href="#" key={l} onClick={() => setOpen(false)}>
              {l}
            </a>
          ))}
        </div>
        <div className="drawer-footer">
          © {new Date().getFullYear()} Alwayzz. All rights reserved.
        </div>
      </div>
    </>
  )
}

export default function App() {
  const [open, setOpen] = useState(false)

  return (
    <div className="app-root">
      <Navbar open={open} setOpen={setOpen} />

      <section className="hero">
        <CurvedLines />

        <Ticker />

        <h1 className="hero-title">
          Premium creative <span className="serif">alwayzz</span>
          <sup>®</sup> on demand.
        </h1>

        <p className="hero-subtitle">
          A flexible design partnership for founders, brands, and agencies who
          want top craft delivered on their timeline.
        </p>

        <div className="cta-row">
          <button className="btn-primary">View Plans</button>
          <button className="btn-book">
            <img
              className="avatar"
              src="https://framerusercontent.com/images/hfneFL6CHBi5BnNvCeOaqU9HqE4.png"
              alt="book avatar"
            />
            <span className="book-text">
              <span className="book-primary">
                Chat for 15 minutes
                <span className="green-dot" />
              </span>
              <span className="book-secondary">Pick a slot</span>
            </span>
          </button>
        </div>

        <div className="progressive-blur" />
      </section>

      <TrustedBy />
    </div>
  )
}
