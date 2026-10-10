import { ArrowRight } from "lucide-react";
import Logo from "../components/Logo.jsx";
import { photo } from "../lib/photos.js";
import Topo from "../components/Topo.jsx";
import Faq from "../components/Faq.jsx";

export default function Landing({ onStart }) {
  return (
    <div className="landing">
      <header className="hero">
        <img src={photo("hero", 2000)} alt="Friends laughing and playing outdoors" />
        <div className="hero-top"><div className="wrap nav-in"><Logo light /></div></div>
        <div className="wrap hero-in">
          <div className="kicker" style={{ color: "rgba(255,255,255,.8)" }}>Open-source AI · Touch Grass</div>
          <h1>Your street is a <em>quest map.</em></h1>
          <p>GrassQuest reads the weather and what's actually near you, then sends you outside on a quest made for that exact moment. Bring back a photo. An AI on your own computer judges it.</p>
          <div className="actions">
            <button className="btn primary big" onClick={onStart}>Start your first quest <ArrowRight size={18} /></button>
            <a className="btn big" href="#how">How it works</a>
          </div>
        </div>
        <span className="credit">Photo: Unsplash</span>
      </header>

      <section className="section topo-host" id="how">
        <Topo seed={7} />
        <div className="wrap" style={{ position: "relative" }}>
          <div className="kicker">How it works</div>
          <h2>Less screen. More world.</h2>
          <div className="steps3">
            <Step n="01" img="walk" title="It reads your world" text="Live weather, sunset time and the real parks, ponds, trails and trees within walking distance. Storm outside? You get a rain check, not a soggy quest." />
            <Step n="02" img="leaf" title="You go do it" text="Pick from three quests: an easy win, a sweet spot, or a stretch. The Ranger briefs you, then the screen goes dark. Phone in pocket." />
            <Step n="03" img="bird" title="Proof becomes progress" text="Snap a photo. Gemma judges it on your machine and names what you found: every bird and tree becomes a card in your Field Guide." />
          </div>
        </div>
      </section>

      <section className="section" style={{ background: "var(--paper-2)" }}>
        <div className="wrap split">
          <div>
            <div className="kicker">Built on open AI</div>
            <h2>Your photos never leave your computer.</h2>
            <p className="muted" style={{ fontSize: "1.1rem", maxWidth: "46ch" }}>
              The judge is Gemma 4, an open-weight model running locally through Ollama. No uploads, no cloud vision bill,
              and it works with whichever Gemma 4 size your machine can handle.
            </p>
          </div>
          <div className="partners" style={{ gridTemplateColumns: "1fr 1fr" }}>
            <div className="partner"><b>Gemma 4</b><span className="muted small">Writes your briefing, judges proof, identifies species</span></div>
            <div className="partner"><b>TabPFN</b><span className="muted small">Predicts your odds and minutes, picks your sweet spot</span></div>
            <div className="partner"><b>MongoDB Atlas</b><span className="muted small">Game data + vector search for fresh quests</span></div>
            <div className="partner"><b>ElevenLabs</b><span className="muted small">The Ranger's voice</span></div>
            <div className="partner"><b>Open-Meteo</b><span className="muted small">Live weather and sunset</span></div>
            <div className="partner"><b>OpenStreetMap</b><span className="muted small">The real places near you</span></div>
          </div>
        </div>
      </section>

      <section className="section">
        <div className="wrap" style={{ maxWidth: 820 }}>
          <div className="kicker">FAQ</div>
          <h2 style={{ marginBottom: 20 }}>Questions</h2>
          <Faq />
          <div style={{ marginTop: 36 }}><button className="btn primary big" onClick={onStart}>Let's go outside <ArrowRight size={18} /></button></div>
        </div>
      </section>
    </div>
  );
}

function Step({ n, img, title, text }) {
  return (
    <article className="step">
      <img src={photo(img, 900)} alt="" loading="lazy" />
      <div className="step-body">
        <div className="step-num">{n}</div>
        <h3>{title}</h3>
        <p className="muted" style={{ margin: 0 }}>{text}</p>
      </div>
    </article>
  );
}
