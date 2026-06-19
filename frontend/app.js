const ideas = [
  {
    id: "I-042",
    title: "Neuro-Symbolic Workspace",
    crest: "兆",
    description:
      "A persistent, differentiable workspace binding symbolic graph structure to neural representations for reasoning and learning.",
    tags: ["reasoning", "neuro-symbolic", "workspace", "memory"],
    verdict: "PROMISING",
    verdictText:
      "Strong cross-domain provenance; feasible prototype if rollout protocol and metric stay fixed.",
    confidence: "0.78",
  },
  {
    id: "I-031",
    title: "Latent Memory Compression",
    crest: "記",
    description:
      "Compress long-horizon world-model memory with spectral regularization and cache-aware scheduling.",
    tags: ["world-model", "compression", "spectral", "cache"],
    verdict: "REVISE",
    verdictText:
      "Good mechanism match, but reviewer requests clearer dataset split and compute budget constraints.",
    confidence: "0.64",
  },
  {
    id: "I-028",
    title: "Generative Proof Hints",
    crest: "証",
    description:
      "Transfer theorem-proving hint search into multimodal branch generation as a constrained proposal prior.",
    tags: ["math", "proof", "proposal", "search"],
    verdict: "PROMISING",
    verdictText:
      "Novel enough for a branch candidate; keep proof analogy separate from validated benchmark evidence.",
    confidence: "0.74",
  },
  {
    id: "I-017",
    title: "Spiking Diffusion Models",
    crest: "脳",
    description:
      "Use spike-timing and replay-inspired schedules to regularize diffusion world-model training.",
    tags: ["neuroscience", "diffusion", "schedule"],
    verdict: "WATCH",
    verdictText:
      "Interesting but high analogy risk; needs an ablation plan before entering execution.",
    confidence: "0.53",
  },
];

const branches = [
  { rank: 1, name: "Neuro-Symbolic Workspace", idea: "I-042", score: 0.87, traction: "High", last: "18m" },
  { rank: 2, name: "Latent Memory Compression", idea: "I-031", score: 0.81, traction: "High", last: "1h" },
  { rank: 3, name: "Generative Proof Hints", idea: "I-028", score: 0.76, traction: "Medium", last: "3h" },
  { rank: 4, name: "Causal World Models for RL", idea: "I-015", score: 0.71, traction: "Medium", last: "5h" },
  { rank: 5, name: "Adaptive Attention Routing", idea: "I-009", score: 0.64, traction: "Medium", last: "1d" },
  { rank: 6, name: "Neural Theorem Prover", idea: "I-023", score: 0.58, traction: "Low", last: "1d" },
  { rank: 7, name: "Spiking Diffusion Models", idea: "I-017", score: 0.53, traction: "Low", last: "2d" },
];

const sessions = [
  { id: "CL-2026-06-19-A", focus: "Memory + Reasoning + Compression", ideas: 12, status: "Active", progress: 67, last: "22m" },
  { id: "CL-2026-06-19-B", focus: "Neuro-Symbolic Learning", ideas: 9, status: "Active", progress: 45, last: "1h" },
  { id: "CL-2026-06-18-C", focus: "Causal World Models", ideas: 11, status: "Active", progress: 80, last: "3h" },
  { id: "CL-2026-06-17-D", focus: "Attention + Dynamics", ideas: 8, status: "Completed", progress: 100, last: "2d" },
];

const selectedIdea = document.querySelector("#selectedIdea");
const verdictLabel = document.querySelector("#verdictLabel");
const verdictText = document.querySelector("#verdictText");
const branchRows = document.querySelector("#branchRows");
const sessionList = document.querySelector("#sessionList");
const searchInput = document.querySelector("#searchInput");

let activeIdea = ideas[0];
let branchSort = "score";

function renderSelectedIdea() {
  selectedIdea.innerHTML = `
    <h1 class="idea-title"><span class="crest">${activeIdea.crest}</span>${activeIdea.title}</h1>
    <p>${activeIdea.description}</p>
    <div class="tag-list">${activeIdea.tags.map((tag) => `<span>${tag}</span>`).join("")}</div>
  `;
  verdictLabel.textContent = activeIdea.verdict;
  verdictText.textContent = activeIdea.verdictText;
  document.querySelector(".confidence span").textContent = activeIdea.confidence;
}

function renderBranches() {
  const query = searchInput.value.trim().toLowerCase();
  const filtered = branches
    .filter((branch) => branch.name.toLowerCase().includes(query) || branch.idea.toLowerCase().includes(query))
    .sort((a, b) => {
      if (branchSort === "recent") return a.last.localeCompare(b.last);
      if (branchSort === "traction") return a.traction.localeCompare(b.traction);
      return b.score - a.score;
    });

  branchRows.innerHTML = filtered
    .map((branch) => {
      const tractionClass = branch.traction.toLowerCase();
      return `
        <tr data-idea="${branch.idea}">
          <td><span class="rank-badge">${branch.rank}</span></td>
          <td><strong>${branch.name}</strong></td>
          <td>${branch.idea}</td>
          <td>${branch.score.toFixed(2)} <span class="score-bar"><span style="width:${branch.score * 100}%"></span></span></td>
          <td><span class="traction ${tractionClass}">${branch.traction}</span></td>
          <td>${branch.last}</td>
        </tr>
      `;
    })
    .join("");
}

function renderSessions() {
  sessionList.innerHTML = sessions
    .map(
      (session) => `
      <div class="session-row">
        <strong>${session.id}</strong>
        <span>${session.focus}</span>
        <span>${session.ideas} ideas</span>
        <span class="progress"><span style="width:${session.progress}%"></span></span>
        <span class="status ${session.status.toLowerCase()}">${session.status}</span>
      </div>
    `,
    )
    .join("");
}

function selectIdeaByIndex(index) {
  activeIdea = ideas[index % ideas.length];
  renderSelectedIdea();
}

document.querySelectorAll(".idea-graph circle").forEach((node) => {
  node.addEventListener("click", () => selectIdeaByIndex(Number(node.dataset.idea || 0)));
});

branchRows.addEventListener("click", (event) => {
  const row = event.target.closest("tr");
  if (!row) return;
  const ideaIndex = Math.max(0, ideas.findIndex((idea) => idea.id === row.dataset.idea));
  selectIdeaByIndex(ideaIndex);
});

document.querySelector("#sortSelect").addEventListener("change", (event) => {
  branchSort = event.target.value;
  renderBranches();
});

searchInput.addEventListener("input", renderBranches);

document.querySelector("#toggleDensity").addEventListener("click", () => {
  document.body.classList.toggle("compact");
});

document.querySelector("#toggleTheme").addEventListener("click", () => {
  document.body.classList.toggle("night");
});

document.querySelector("#runPipeline").addEventListener("click", () => {
  const firstStage = document.querySelector(".stage.accent");
  firstStage.animate(
    [
      { boxShadow: "inset 0 3px 0 var(--vermilion), 0 0 0 rgba(211,77,56,0)" },
      { boxShadow: "inset 0 3px 0 var(--vermilion), 0 0 0 10px rgba(211,77,56,.14)" },
      { boxShadow: "inset 0 3px 0 var(--vermilion), 0 0 0 rgba(211,77,56,0)" },
    ],
    { duration: 900, easing: "ease-out" },
  );
});

document.querySelector("#newIntake").addEventListener("click", () => {
  searchInput.value = "world model spectral replay";
  searchInput.focus();
  renderBranches();
});

document.querySelectorAll(".nav-item").forEach((item) => {
  item.addEventListener("click", () => {
    document.querySelectorAll(".nav-item").forEach((nav) => nav.classList.remove("active"));
    item.classList.add("active");
  });
});

renderSelectedIdea();
renderBranches();
renderSessions();
