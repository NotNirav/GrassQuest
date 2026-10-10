import { useState } from "react";
import { BookOpen } from "lucide-react";
import FieldCard from "../components/FieldCard.jsx";

const FILTERS = ["all", "bird", "tree", "plant", "insect", "sky"];

export default function FieldGuide({ player }) {
  const [f, setF] = useState("all");
  const cards = player.field_guide.filter((c) => f === "all" || c.kind === f);
  return (
    <div className="wrap page">
      <div className="page-head">
        <div><div className="kicker">Everything you've found{player.area ? ` around ${player.area}` : ""}</div><h1>Field Guide</h1></div>
        <div className="seg" role="group" aria-label="Filter cards">
          {FILTERS.map((k) => <button key={k} aria-pressed={f === k} onClick={() => setF(k)}>{k === "all" ? `All · ${player.field_guide.length}` : k}</button>)}
        </div>
      </div>
      {cards.length ? (
        <div className="cards">{cards.map((c) => <FieldCard key={c.key} card={c} />)}</div>
      ) : (
        <div className="card empty">
          <BookOpen size={36} />
          <h2 style={{ fontSize: "1.8rem", margin: "10px 0 6px" }}>No cards yet</h2>
          <p className="muted">When Gemma spots a bird, tree, flower or bug in your proof photo, it lands here with a fun fact. Collect your whole neighbourhood.</p>
        </div>
      )}
    </div>
  );
}
