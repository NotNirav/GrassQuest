import { Bird, Bug, Cloud, Leaf, PawPrint, Sprout, TreeDeciduous } from "lucide-react";

const KIND = {
  bird: { icon: Bird, color: "#2f5d8a", label: "Bird" },
  plant: { icon: Sprout, color: "#4e6b3a", label: "Plant" },
  tree: { icon: TreeDeciduous, color: "#3d5a2a", label: "Tree" },
  insect: { icon: Bug, color: "#a0522d", label: "Insect" },
  fungus: { icon: Leaf, color: "#8a5a2b", label: "Fungus" },
  sky: { icon: Cloud, color: "#5b7fa6", label: "Sky" },
  animal: { icon: PawPrint, color: "#b5651d", label: "Animal" },
};
const RARITY_COLOR = { common: "var(--common)", uncommon: "var(--rare)", rare: "var(--legendary)" };

export default function FieldCard({ card, flip = false }) {
  const k = KIND[card.kind] ?? KIND.plant;
  const Icon = k.icon;
  return (
    <article className={`fcard${flip ? " flip" : ""}`} style={{ "--k": k.color }}>
      <div className="kind">
        <span className="kicker">{k.label}</span>
        <span className="rarity" style={{ "--r-color": RARITY_COLOR[card.rarity] }}>{card.rarity}</span>
      </div>
      <div className="icon"><Icon size={30} /></div>
      <h3>{card.name}</h3>
      <p>{card.fact}</p>
      <div className="foot">First spotted {card.first_seen}{card.area ? ` · ${card.area}` : ""}</div>
    </article>
  );
}
