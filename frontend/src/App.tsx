import { useCallback, useEffect, useMemo, useState } from "react";
import type { FormEvent, ReactNode } from "react";
import {
  ArrowDownLeft,
  ArrowLeftRight,
  ArrowUpRight,
  Check,
  ChevronDown,
  CircleHelp,
  CreditCard,
  LayoutDashboard,
  LoaderCircle,
  LogOut,
  MessageCircle,
  Plus,
  Send,
  Settings2,
  Sparkles,
  Wallet,
  X,
} from "lucide-react";
import LandingPage from "./LandingPage";
import {
  Budget,
  Profile,
  Summary,
  Transaction,
  clearSession,
  hasSession,
  request,
  signIn,
  signOut,
  signUp,
} from "./api";

type Page = "overview" | "transactions" | "budgets" | "assistant";
type ChatMessage = { role: "user" | "assistant"; content: string };

const money = (amount: number, currency = "KES") =>
  new Intl.NumberFormat("en-KE", { style: "currency", currency, maximumFractionDigits: 0 }).format(amount);
const localDate = (date: Date) => `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;

function ErrorBanner({ message, onClose, dismissible = true }: { message: string; onClose: () => void; dismissible?: boolean }) {
  if (!message) return null;
  return (
    <div className="notice" role="alert">
      <span>{message}</span>
      {dismissible && <button className="icon-button" onClick={onClose} aria-label="Dismiss error"><X size={16} /></button>}
    </div>
  );
}

function AuthScreen({ onAuthenticated, initialMode }: { onAuthenticated: () => void; initialMode: "login" | "register" }) {
  const [mode, setMode] = useState<"login" | "register">(initialMode);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      if (mode === "register") await signUp(name, email, password);
      else await signIn(email, password);
      onAuthenticated();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to sign in.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="auth-layout">
      <section className="auth-art">
        <a className="brand brand-light" href="#home"><span className="brand-mark">m</span> mula</a>
        <div className="auth-quote">
          <span className="eyebrow light-eyebrow">A little more clarity</span>
          <h1>Your money has a story. Let’s make sense of it.</h1>
          <p>See what’s coming in, where it’s going, and what you can do next.</p>
        </div>
        <div className="art-orbit orbit-one" />
        <div className="art-orbit orbit-two" />
        <div className="art-note"><Sparkles size={17} /><span>Small steps add up.</span></div>
      </section>
      <section className="auth-panel">
        <div className="mobile-brand brand"><span className="brand-mark">m</span> mula</div>
        <div className="auth-box">
          <span className="eyebrow">YOUR MONEY, IN ONE PLACE</span>
          <h2>{mode === "login" ? "Welcome back" : "Start with Mula"}</h2>
          <p className="muted">{mode === "login" ? "Sign in to pick up where you left off." : "Create an account to get your finances organized."}</p>
          <ErrorBanner message={error} onClose={() => setError("")} />
          <form onSubmit={submit} className="form-stack">
            {mode === "register" && <label>Your name<input value={name} onChange={(e) => setName(e.target.value)} autoComplete="name" required /></label>}
            <label>Email address<input value={email} onChange={(e) => setEmail(e.target.value)} type="email" autoComplete="email" required /></label>
            <label>Password<input value={password} onChange={(e) => setPassword(e.target.value)} type="password" autoComplete={mode === "login" ? "current-password" : "new-password"} minLength={8} required />
              {mode === "register" && <small>Use at least 8 characters and include a number.</small>}
            </label>
            <button className="button button-primary button-wide" disabled={busy}>
              {busy ? <LoaderCircle className="spin" size={18} /> : null}
              {mode === "login" ? "Sign in" : "Create account"}
            </button>
          </form>
          <p className="auth-switch">
            {mode === "login" ? "New to Mula?" : "Already have an account?"}{" "}
            <button className="link-button" onClick={() => { setMode(mode === "login" ? "register" : "login"); setError(""); }}>
              {mode === "login" ? "Create an account" : "Sign in"}
            </button>
          </p>
          <p className="auth-legal">Your financial data belongs to you. Keep your sign-in details private.</p>
        </div>
      </section>
    </main>
  );
}

export default function App() {
  const [isAppRoute, setIsAppRoute] = useState(() => window.location.pathname.startsWith("/app"));
  const [authMode, setAuthMode] = useState<"login" | "register">(() => window.location.search.includes("mode=register") ? "register" : "login");
  const [authenticated, setAuthenticated] = useState(hasSession());
  const [page, setPage] = useState<Page>("overview");
  const [profile, setProfile] = useState<Profile | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [budgets, setBudgets] = useState<Budget[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [modalError, setModalError] = useState("");
  const [modal, setModal] = useState<"transaction" | "budget" | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [chat, setChat] = useState<ChatMessage[]>([
    { role: "assistant", content: "Hi! I’m Mula. Tell me what you’re working toward, and we can make a simple plan together." },
  ]);
  const [chatBusy, setChatBusy] = useState(false);

  useEffect(() => {
    const syncRoute = () => {
      setIsAppRoute(window.location.pathname.startsWith("/app"));
      setAuthMode(window.location.search.includes("mode=register") ? "register" : "login");
    };
    window.addEventListener("popstate", syncRoute);
    return () => window.removeEventListener("popstate", syncRoute);
  }, []);

  function openApp(mode: "login" | "register" = "login") {
    setAuthMode(mode);
    setIsAppRoute(true);
    window.history.pushState({}, "", mode === "register" ? "/app?mode=register" : "/app");
  }

  const loadDashboard = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const now = new Date();
      const fromDate = localDate(new Date(now.getFullYear(), now.getMonth(), 1));
      const toDate = localDate(now);
      const [user, txs, totals, plans] = await Promise.all([
        request<Profile>("/auth/profile"),
        request<Transaction[]>("/transactions?limit=50"),
        request<Summary>(`/transactions/summary?from_date=${fromDate}&to_date=${toDate}`),
        request<Budget[]>("/financial/budgets"),
      ]);
      setProfile(user);
      setTransactions(txs);
      setSummary(totals);
      setBudgets(plans);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not load your Mula data.");
      if (!hasSession()) {
        clearSession();
        setAuthenticated(false);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (authenticated) void loadDashboard();
  }, [authenticated, loadDashboard]);

  const displayName = profile?.full_name?.trim().split(/\s+/)[0] || "there";
  const debitCategories = useMemo(() => {
    const month = localDate(new Date()).slice(0, 7);
    const totals = new Map<string, number>();
    for (const transaction of transactions) {
      if (transaction.transaction_type !== "debit" || transaction.transaction_date.slice(0, 7) !== month || !transaction.category) continue;
      totals.set(transaction.category, (totals.get(transaction.category) || 0) + transaction.amount);
    }
    return [...totals.entries()].sort((a, b) => b[1] - a[1]).slice(0, 5);
  }, [transactions]);

  async function logout() {
    await signOut();
    setProfile(null);
    setAuthenticated(false);
  }

  async function createTransaction(form: FormData) {
    await request<Transaction>("/transactions", {
      method: "POST",
      body: JSON.stringify({
        amount: Number(form.get("amount")),
        currency: profile?.currency || "KES",
        transaction_type: form.get("transaction_type"),
        category: form.get("category"),
        description: form.get("description") || null,
        source: "manual",
        transaction_date: form.get("transaction_date"),
      }),
    });
    setModal(null);
    await loadDashboard();
  }

  async function createBudget(form: FormData) {
    const allocation = Number(form.get("allocation"));
    await request<Budget>("/financial/budgets/create", {
      method: "POST",
      body: JSON.stringify({
        name: form.get("name"),
        period: "monthly",
        start_date: form.get("start_date"),
        total_income: Number(form.get("total_income")),
        currency: profile?.currency || "KES",
        categories: allocation > 0 ? [{ name: "Monthly spending", category_type: "needs", allocated_amount: allocation }] : [],
      }),
    });
    setModal(null);
    await loadDashboard();
    setPage("budgets");
  }

  async function sendChat(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const message = String(form.get("message") || "").trim();
    if (!message || chatBusy) return;
    const nextChat = [...chat, { role: "user" as const, content: message }];
    setChat(nextChat);
    event.currentTarget.reset();
    setChatBusy(true);
    setError("");
    try {
      const response = await request<{ conversation_id: string; message: string; model_used: string }>("/assistant/chat", {
        method: "POST",
        body: JSON.stringify({ message, conversation_id: conversationId, task_type: "chat" }),
      });
      setConversationId(response.conversation_id);
      setChat([...nextChat, { role: "assistant", content: response.message }]);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Mula could not reply just now.");
    } finally {
      setChatBusy(false);
    }
  }

  if (!isAppRoute) return <LandingPage onOpenApp={openApp} />;
  if (!authenticated) return <AuthScreen initialMode={authMode} onAuthenticated={() => setAuthenticated(true)} />;

  const navItems: { key: Page; label: string; icon: typeof LayoutDashboard }[] = [
    { key: "overview", label: "Overview", icon: LayoutDashboard },
    { key: "transactions", label: "Transactions", icon: ArrowLeftRight },
    { key: "budgets", label: "Budgets", icon: Wallet },
    { key: "assistant", label: "Mula assistant", icon: MessageCircle },
  ];

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="#overview" onClick={(e) => { e.preventDefault(); setPage("overview"); }}><span className="brand-mark">m</span> mula</a>
        <div className="workspace-label">YOUR MONEY</div>
        <nav className="side-nav" aria-label="Main navigation">
          {navItems.map(({ key, label, icon: Icon }) => (
            <button key={key} className={`nav-link ${page === key ? "active" : ""}`} onClick={() => setPage(key)}>
              <Icon size={18} strokeWidth={1.8} /><span>{label}</span>{key === "assistant" && <span className="nav-spark"><Sparkles size={13} /></span>}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <button className="nav-link"><CircleHelp size={18} strokeWidth={1.8} /><span>Help & support</span></button>
          <div className="profile-card">
            <div className="avatar">{(profile?.full_name || profile?.email || "M").slice(0, 1).toUpperCase()}</div>
            <div className="profile-meta"><strong>{profile?.full_name || "My account"}</strong><span>{profile?.email}</span></div>
            <button className="icon-button logout-button" onClick={logout} title="Sign out" aria-label="Sign out"><LogOut size={16} /></button>
          </div>
        </div>
      </aside>

      <main className="main-area">
        <header className="topbar">
          <div className="breadcrumb"><span>My finances</span><span className="crumb-divider">/</span><strong>{navItems.find((item) => item.key === page)?.label}</strong></div>
          <div className="topbar-actions"><span className="secure-chip"><span className="status-dot" />Your account is up to date</span><button className="icon-button settings-button" title="Settings"><Settings2 size={18} /></button></div>
        </header>

        <div className="page-content">
          <ErrorBanner message={error} onClose={() => setError("")} />
          {page === "overview" && <>
            <section className="welcome-row">
              <div><span className="eyebrow">{new Intl.DateTimeFormat("en-KE", { weekday: "long", month: "long", day: "numeric" }).format(new Date()).toUpperCase()}</span><h1>Good day, {displayName}<span className="wave"> ✳</span></h1><p className="muted">Here’s the shape of your money right now.</p></div>
              <button className="button button-primary" onClick={() => setModal("transaction")}><Plus size={17} />Add transaction</button>
            </section>
            <section className="summary-grid">
              <article className="summary-card balance-card"><div className="card-label">NET THIS MONTH <span className="card-icon"><Wallet size={18} /></span></div><strong className="big-number">{money(summary?.net ?? 0, profile?.currency)}</strong><div className="card-foot"><span className="tiny-status"><span className="status-dot" />Updated from your transactions</span></div><div className="balance-decoration" /></article>
              <article className="summary-card"><div className="card-label">MONEY IN <span className="card-icon incoming"><ArrowDownLeft size={17} /></span></div><strong className="metric-number">{money(summary?.total_credits ?? 0, profile?.currency)}</strong><span className="metric-note">{summary?.count ?? 0} recorded transactions</span><div className="mini-bars bars-green"><i /><i /><i /><i /><i /><i /><i /><i /><i /><i /><i /><i /></div></article>
              <article className="summary-card"><div className="card-label">MONEY OUT <span className="card-icon outgoing"><ArrowUpRight size={17} /></span></div><strong className="metric-number">{money(summary?.total_debits ?? 0, profile?.currency)}</strong><span className="metric-note">Across your spending categories</span><div className="mini-bars bars-sand"><i /><i /><i /><i /><i /><i /><i /><i /><i /><i /><i /><i /></div></article>
            </section>
            <section className="content-grid">
              <article className="panel transaction-panel">
                <div className="panel-heading"><div><span className="eyebrow">YOUR ACTIVITY</span><h2>Recent transactions</h2></div><button className="text-action" onClick={() => setPage("transactions")}>See all <span>↗</span></button></div>
                <Transactions rows={transactions.slice(0, 6)} currency={profile?.currency || "KES"} loading={loading} />
              </article>
              <div className="right-column">
                <article className="panel category-panel"><div className="panel-heading compact"><div><span className="eyebrow">SPENDING SNAPSHOT</span><h2>Where it goes</h2></div><CreditCard size={18} className="quiet-icon" /></div>
                  {debitCategories.length ? <div className="category-list">{debitCategories.map(([category, amount], index) => {
                    const total = summary?.total_debits || 1;
                    return <div className="category-row" key={category}><div className="category-label"><span className={`category-dot dot-${index + 1}`} />{category}<span className="category-value">{money(amount, profile?.currency)}</span></div><div className="progress-track"><span className={`progress-fill fill-${index + 1}`} style={{ width: `${Math.max(4, Math.min(100, amount / total * 100))}%` }} /></div></div>;
                  })}</div> : <EmptyState title="Your categories will show here" text="Record a transaction to see your spending breakdown." />}
                </article>
                <article className="assistant-promo"><div className="promo-icon"><Sparkles size={18} /></div><span className="eyebrow light-eyebrow">A THOUGHTFUL MONEY BUDDY</span><h3>A better plan starts with a conversation.</h3><p>Ask Mula about budgets, saving, or a money decision on your mind.</p><button className="promo-link" onClick={() => setPage("assistant")}>Talk to Mula <span>→</span></button><div className="promo-art" /></article>
              </div>
            </section>
          </>}

          {page === "transactions" && <>
            <PageTitle eyebrow="YOUR ACTIVITY" title="Transactions" subtitle="A clear view of money moving in and out." action={<button className="button button-primary" onClick={() => setModal("transaction")}><Plus size={17} />Add transaction</button>} />
            <section className="panel full-panel"><div className="panel-heading"><div><span className="eyebrow">ALL ACTIVITY</span><h2>{summary?.count ?? 0} transactions</h2></div><span className="period-tag">Latest first <ChevronDown size={14} /></span></div><Transactions rows={transactions} currency={profile?.currency || "KES"} loading={loading} /></section>
          </>}

          {page === "budgets" && <>
            <PageTitle eyebrow="A PLAN FOR WHAT MATTERS" title="Budgets" subtitle="Give your priorities a place in the plan." action={<button className="button button-primary" onClick={() => setModal("budget")}><Plus size={17} />Create a budget</button>} />
            {budgets.length ? <div className="budget-grid">{budgets.map((budget) => <BudgetCard key={budget.id} budget={budget} />)}</div> : <section className="panel empty-budget"><div className="empty-illustration"><Wallet size={28} /></div><span className="eyebrow">YOUR FIRST PLAN</span><h2>Start with a budget that feels like you.</h2><p className="muted">Set a monthly income and decide how much to put toward your day-to-day spending.</p><button className="button button-primary" onClick={() => setModal("budget")}><Plus size={17} />Create a budget</button></section>}
          </>}

          {page === "assistant" && <>
            <PageTitle eyebrow="HERE WHEN YOU NEED A HAND" title="Mula assistant" subtitle="A calm place to think through your next money move." />
            <section className="chat-shell panel"><div className="chat-top"><div className="bot-avatar"><Sparkles size={18} /></div><div><strong>Mula</strong><span><span className="status-dot" /> Ready to help</span></div><span className="chat-context">Your conversations stay private</span></div>
              <div className="chat-messages">{chat.map((message, index) => <div className={`chat-line ${message.role}`} key={`${index}-${message.role}`}><div className="chat-bubble">{message.content}</div></div>)}{chatBusy && <div className="chat-line assistant"><div className="chat-bubble typing"><i /><i /><i /></div></div>}</div>
              <form className="chat-form" onSubmit={sendChat}><input name="message" placeholder="Ask about your money…" maxLength={8000} autoComplete="off" disabled={chatBusy} /><button className="send-button" aria-label="Send message" disabled={chatBusy}><Send size={17} /></button></form>
              <div className="chat-disclaimer">Mula can help you plan, but it isn’t a financial adviser.</div>
            </section>
          </>}
          <footer className="page-footer"><span>mula <span className="footer-dot">·</span> money, made clearer</span><span>Built for your next good decision.</span></footer>
        </div>
      </main>

      {modal && <Modal title={modal === "transaction" ? "Add a transaction" : "Create a monthly budget"} error={modalError} onClose={() => { setModal(null); setModalError(""); }}>
        <form className="form-stack modal-form" onSubmit={async (event) => {
          event.preventDefault();
          const form = new FormData(event.currentTarget);
          try { setError(""); if (modal === "transaction") await createTransaction(form); else await createBudget(form); }
          catch (reason) { setModalError(reason instanceof Error ? reason.message : "Could not save your changes."); }
        }}>
          {modal === "transaction" ? <>
            <label>Amount<input name="amount" type="number" min="1" step="0.01" placeholder="0.00" required /></label>
            <label>Type<select name="transaction_type"><option value="debit">Money out</option><option value="credit">Money in</option></select></label>
            <label>Category<input name="category" placeholder="e.g. Food, transport, rent" required /></label>
            <label>Description <span className="optional">Optional</span><input name="description" placeholder="What was this for?" /></label>
            <label>Date<input name="transaction_date" type="date" defaultValue={new Date().toISOString().slice(0, 10)} required /></label>
          </> : <>
            <label>Give your budget a name<input name="name" placeholder="My monthly plan" required /></label>
            <label>Monthly take-home income<input name="total_income" type="number" min="0" step="0.01" placeholder="0.00" required /></label>
            <label>Spending allocation <span className="optional">Optional</span><input name="allocation" type="number" min="0" step="0.01" placeholder="e.g. 25000" /></label>
            <label>Start date<input name="start_date" type="date" defaultValue={new Date().toISOString().slice(0, 10)} required /></label>
          </>}
          <div className="modal-actions"><button type="button" className="button button-secondary" onClick={() => setModal(null)}>Cancel</button><button className="button button-primary">Save</button></div>
        </form>
      </Modal>}
    </div>
  );
}

function PageTitle({ eyebrow, title, subtitle, action }: { eyebrow: string; title: string; subtitle: string; action?: ReactNode }) {
  return <section className="welcome-row"><div><span className="eyebrow">{eyebrow}</span><h1>{title}</h1><p className="muted">{subtitle}</p></div>{action}</section>;
}

function Transactions({ rows, currency, loading }: { rows: Transaction[]; currency: string; loading: boolean }) {
  if (loading && !rows.length) return <div className="loading-state"><LoaderCircle size={19} className="spin" />Loading your activity…</div>;
  if (!rows.length) return <EmptyState title="No transactions yet" text="Add one to get a better picture of your money." />;
  return <div className="transaction-list">{rows.map((tx) => {
    const credit = tx.transaction_type === "credit";
    return <div className="transaction-row" key={tx.id}><div className={`tx-icon ${credit ? "tx-in" : "tx-out"}`}>{credit ? <ArrowDownLeft size={18} /> : <ArrowUpRight size={18} />}</div><div className="tx-description"><strong>{tx.description || tx.category || (credit ? "Money in" : "Money out")}</strong><span>{tx.category || (credit ? "Income" : "Spending")} <span className="tx-separator">·</span> {new Date(`${tx.transaction_date}T12:00:00`).toLocaleDateString("en-KE", { day: "numeric", month: "short" })}</span></div><strong className={`tx-amount ${credit ? "positive" : ""}`}>{credit ? "+" : "−"}{money(tx.amount, tx.currency || currency)}</strong></div>;
  })}</div>;
}

function BudgetCard({ budget }: { budget: Budget }) {
  return <article className="panel budget-card"><div className="budget-card-top"><span className="budget-icon"><Wallet size={18} /></span><span className="period-tag">{budget.period}</span></div><span className="eyebrow">MONTHLY PLAN</span><h2>{budget.name}</h2><div className="budget-total">{money(budget.total_income, budget.currency)}<span>planned income</span></div>
    {budget.categories.length ? <div className="budget-categories">{budget.categories.map((category) => {
      const percent = Math.min(100, category.spent_amount / Math.max(category.allocated_amount, 1) * 100);
      return <div key={category.id} className="budget-category"><div><span>{category.name}</span><small>{money(category.spent_amount, budget.currency)} / {money(category.allocated_amount, budget.currency)}</small></div><div className="progress-track"><span className="progress-fill fill-1" style={{ width: `${percent}%` }} /></div></div>;
    })}</div> : <p className="muted budget-note">Add categories to give this plan more detail.</p>}
  </article>;
}

function EmptyState({ title, text }: { title: string; text: string }) {
  return <div className="empty-state"><span className="empty-check"><Check size={17} /></span><strong>{title}</strong><p>{text}</p></div>;
}

function Modal({ title, children, error, onClose }: { title: string; children: ReactNode; error: string; onClose: () => void }) {
  return <div className="modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}><section className="modal" role="dialog" aria-modal="true" aria-label={title}><div className="modal-heading"><div><span className="eyebrow">MAKE IT COUNT</span><h2>{title}</h2></div><button className="icon-button" onClick={onClose} aria-label="Close dialog"><X size={19} /></button></div><ErrorBanner message={error} onClose={() => {}} dismissible={false} />{children}</section></div>;
}
