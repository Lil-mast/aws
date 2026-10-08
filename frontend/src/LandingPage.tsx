import {
  ArrowRight,
  Check,
  ChevronRight,
  Compass,
  MessageCircle,
  ShieldCheck,
  Sparkles,
  Wallet,
} from "lucide-react";

type Props = { onOpenApp: (mode?: "login" | "register") => void };

export default function LandingPage({ onOpenApp }: Props) {
  return (
    <main className="marketing-page">
      <header className="marketing-header">
        <a className="brand" href="#top"><span className="brand-mark">m</span> mula</a>
        <nav className="marketing-nav" aria-label="Main navigation">
          <a href="#what-mula-does">What Mula does</a>
          <a href="#how-it-works">How it works</a>
          <a href="#built-on-trust">Your money, your call</a>
        </nav>
        <div className="marketing-actions">
          <button className="marketing-signin" onClick={() => onOpenApp("login")}>Sign in</button>
          <button className="button button-primary" onClick={() => onOpenApp("register")}>Get started <ArrowRight size={15} /></button>
        </div>
      </header>

      <section id="top" className="marketing-hero">
        <div className="hero-copy">
          <span className="hero-kicker"><span /> FINANCIAL CLARITY FOR EVERYDAY LIFE</span>
          <h1>Make a little more sense of your <em>money.</em></h1>
          <p>Mula brings your spending, plans, and next steps into one calm place—so you can make decisions with more confidence.</p>
          <div className="hero-actions"><button className="button button-lime" onClick={() => onOpenApp("register")}>Start with Mula <ArrowRight size={16} /></button><a className="hero-learn" href="#how-it-works">See how it works <ChevronRight size={15} /></a></div>
          <div className="hero-points"><span><Check size={14} /> Built for real life in Kenya</span><span><Check size={14} /> You’re in control of what you add</span></div>
        </div>
        <div className="hero-visual" aria-label="Sample Mula finance dashboard">
          <div className="visual-glow" />
          <div className="visual-card">
            <div className="visual-top"><div className="visual-brand"><span className="visual-mark">m</span><span>your overview</span></div><span className="visual-period">THIS MONTH⌄</span></div>
            <div className="visual-greeting">A clearer view, one step at a time.</div>
            <div className="visual-balance-label">MONEY LEFT AFTER SPENDING</div>
            <div className="visual-balance">KES 18,450 <span>↗</span></div>
            <div className="visual-line"><i /><i /><i /><i /><i /><i /><i /><i /><i /><i /><i /><i /><i /><i /><i /><i /><i /><i /></div>
            <div className="visual-stats"><div><span className="visual-stat-title"><i className="green-dot" /> MONEY IN</span><strong>KES 76,000</strong></div><div><span className="visual-stat-title"><i className="sand-dot" /> MONEY OUT</span><strong>KES 57,550</strong></div></div>
            <div className="visual-transaction"><span className="visual-merchant">M</span><span><b>Market shopping</b><small>Food · Today</small></span><strong>− KES 2,400</strong></div>
            <span className="visual-sample">Illustrative example</span>
          </div>
          <div className="floating-tip"><span className="tip-icon"><Sparkles size={15} /></span><span><b>One step at a time</b><small>Small plans can make a difference.</small></span></div>
          <div className="visual-circle circle-a" /><div className="visual-circle circle-b" />
        </div>
        <div className="hero-bottom-line" />
      </section>

      <section id="what-mula-does" className="marketing-section what-section">
        <div className="section-intro"><span className="eyebrow">A FRIENDLIER WAY TO PLAN</span><h2>Money can feel complicated.<br /><span>Mula helps make it clearer.</span></h2><p>Start with what you know. Add your activity, shape a plan, and get practical help when you need it.</p></div>
        <div className="feature-grid">
          <article className="feature-card"><span className="feature-icon icon-sage"><Wallet size={20} /></span><span className="eyebrow">SEE THE PICTURE</span><h3>Know where your money goes</h3><p>Add transactions and see your money in, money out, and spending categories together.</p><span className="feature-number">01</span></article>
          <article className="feature-card feature-card-raised"><span className="feature-icon icon-lime"><Compass size={20} /></span><span className="eyebrow">MAKE A PLAN</span><h3>Give your priorities a place</h3><p>Create a monthly budget and choose what matters most—one simple plan you can adjust.</p><span className="feature-number">02</span></article>
          <article className="feature-card"><span className="feature-icon icon-peach"><MessageCircle size={20} /></span><span className="eyebrow">THINK IT THROUGH</span><h3>Get a helpful perspective</h3><p>Talk through a money question with Mula’s assistant and turn a big goal into a next step.</p><span className="feature-number">03</span></article>
        </div>
        <div className="manual-note"><span className="note-check"><Check size={14} /></span><span><b>You decide what goes in.</b> For now, add transactions yourself; automatic account connections are not enabled.</span></div>
      </section>

      <section id="how-it-works" className="how-section">
        <div className="how-inner"><div className="how-heading"><span className="eyebrow light-eyebrow">A GOOD PLACE TO BEGIN</span><h2>Start where you are.<br /><span>Build from there.</span></h2><p>No perfect spreadsheets or big financial plans needed. Just your next useful step.</p><button className="button button-lime" onClick={() => onOpenApp("register")}>Create your free account <ArrowRight size={15} /></button></div>
          <div className="steps-list"><div className="how-step"><span className="step-index">01</span><div><h3>Make your account</h3><p>Sign up with your email and keep your money workspace personal.</p></div><span className="step-symbol"><Check size={16} /></span></div><div className="how-step"><span className="step-index">02</span><div><h3>Add a little context</h3><p>Record a few transactions and set the income or budget you want to work with.</p></div><span className="step-symbol"><Wallet size={16} /></span></div><div className="how-step"><span className="step-index">03</span><div><h3>Choose your next step</h3><p>Review the picture, adjust your plan, or ask Mula to help you think it through.</p></div><span className="step-symbol"><ArrowRight size={16} /></span></div></div>
        </div>
      </section>

      <section id="built-on-trust" className="trust-section"><div className="trust-icon"><ShieldCheck size={22} /></div><div><span className="eyebrow">BUILT AROUND YOUR CHOICES</span><h2>Your finances should stay yours.</h2><p>Mula is a financial wellness tool for learning and planning. It is not a lender, a credit bureau, or a source of professional financial advice. You choose the activity you add, and can sign out at any time.</p></div><button className="trust-cta" onClick={() => onOpenApp("register")}>Take a look around <ArrowRight size={15} /></button></section>

      <footer className="marketing-footer"><a className="brand" href="#top"><span className="brand-mark">m</span> mula</a><span>Money, made clearer.</span><span>Made with care in Kenya <span className="footer-heart">♥</span></span></footer>
    </main>
  );
}
