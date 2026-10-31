const $ = (id) => document.getElementById(id);
let latestAnalysis = null;

$("description").addEventListener("input", (e) => {
  $("char-count").textContent = `${e.target.value.length} / 3000`;
});

$("analyze-btn").addEventListener("click", async () => {
  const description = $("description").value.trim();
  if (description.length < 15) return alert("Please enter at least 15 characters describing the issue.");
  const button = $("analyze-btn");
  button.disabled = true;
  button.innerHTML = "Analyzing report…";
  $("status").textContent = "ANALYZING";
  try {
    const response = await fetch("/api/analyze", {
      method: "POST", headers: {"Content-Type":"application/json"},
      body: JSON.stringify({description})
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Could not analyze this report.");
    latestAnalysis = {...data, description, title: data.category + " report"};
    $("category-tag").textContent = data.category;
    $("urgency-tag").textContent = data.urgency + " urgency";
    $("urgency-tag").className = data.urgency.toLowerCase();
    $("department").textContent = data.department;
    $("summary").textContent = data.summary;
    $("action").textContent = data.suggested_action;
    $("ai-mode").textContent = "Analysis method: " + data.ai_mode;
    $("empty-state").classList.add("hidden");
    $("result").classList.remove("hidden");
    $("status").textContent = "READY";
  } catch (error) {
    alert(error.message);
    $("status").textContent = "ERROR";
  } finally {
    button.disabled = false;
    button.innerHTML = 'Analyze report <span>→</span>';
  }
});

$("save-btn").addEventListener("click", async () => {
  if (!latestAnalysis) return;
  const button = $("save-btn");
  button.disabled = true;
  try {
    const response = await fetch("/api/complaints", {
      method: "POST", headers: {"Content-Type":"application/json"},
      body: JSON.stringify(latestAnalysis)
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Could not save report.");
    button.textContent = `Saved as report #${data.id}`;
    await loadReports();
  } catch (error) { alert(error.message); }
  finally { button.disabled = false; }
});

async function loadReports() {
  const [reportsRes, statsRes] = await Promise.all([fetch("/api/complaints"), fetch("/api/stats")]);
  const reports = await reportsRes.json();
  const stats = await statsRes.json();
  $("total-count").textContent = stats.total;
  $("critical-count").textContent = stats.critical;
  $("complaints").innerHTML = "";
  if (!reports.length) {
    $("complaints").innerHTML = '<p class="muted">No reports saved yet.</p>';
    return;
  }
  reports.forEach((r) => {
    const card = document.createElement("article");
    card.className = "complaint";
    const title = document.createElement("strong");
    title.textContent = r.title;
    const body = document.createElement("p");
    body.textContent = r.description;
    const meta = document.createElement("div");
    meta.className = "complaint-meta";
    meta.textContent = `#${r.id} · ${r.category} · ${r.urgency} urgency · ${r.department}`;
    card.append(title, body, meta);
    $("complaints").append(card);
  });
}
$("refresh-btn").addEventListener("click", loadReports);
loadReports();
