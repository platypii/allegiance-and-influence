import styles from "./system.module.css"

const colors = [
  ["Ink", "--ink"], ["Paper", "--paper"], ["Raised paper", "--paper-raised"],
  ["Brass", "--brass"], ["Red faction", "--red"], ["Blue faction", "--blue"],
]

export default function DesignSystem() {
  return <main className={styles.system}>
    <header><a href="/">← Back to the game</a><p className="eyebrow muted">Allegiance &amp; Influence · design reference</p><h1>A room for great minds.</h1><p>Warm paper, quiet surfaces, confident type. The characters bring the color; the interface gives them room.</p></header>
    <section aria-labelledby="palette"><h2 id="palette">01 / Palette</h2><div className={styles.colors}>{colors.map(([name, variable]) => <div key={variable}><div className={styles.swatch} style={{ background: `var(${variable})` }} /><strong>{name}</strong><p>{variable}</p></div>)}</div></section>
    <section aria-labelledby="type"><h2 id="type">02 / Typography</h2><div className={styles.type}><h1>Persuasion changes everything.</h1><h2>Choose your next ally.</h2><p>Body text stays at 16px or larger, with enough line spacing for an entire conversation.</p><p className="eyebrow">Secondary labels · 14px minimum</p></div></section>
    <section aria-labelledby="controls"><h2 id="controls">03 / Controls</h2><p>Clear labels, visible focus, and a minimum 44px touch target. Primary controls use dark ink; secondary controls sit on paper.</p><div className={styles.controls}><button className="primary" type="button">Primary example</button><button type="button">Secondary example</button><button type="button" disabled>Disabled example</button><label>Example input<input placeholder="A clear, readable field" /></label></div></section>
    <section aria-labelledby="principles"><h2 id="principles">04 / In play</h2><ul><li>Show faction names alongside color.</li><li>Keep text off detailed artwork and portraits.</li><li>Use a labeled grid on phones; let conversations fill the screen.</li><li>Make profiles, errors, pending replies, and recovery readable.</li><li>Respect reduced motion and keep all assets local.</li></ul></section>
  </main>
}
