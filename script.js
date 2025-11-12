const API_BASE = "http://127.0.0.1:5000";

const evaluateBtn = document.getElementById("evaluateBtn");
const clearBtn = document.getElementById("clearBtn");
const loading = document.getElementById("loading");

const tabs = document.querySelectorAll(".tab");
const tabContents = document.querySelectorAll(".tab-content");

tabs.forEach(tab => {
    tab.addEventListener("click", () => {
        tabs.forEach(t => t.classList.remove("active"));
        tab.classList.add("active");

        tabContents.forEach(tc => tc.classList.remove("active"));
        document.getElementById(tab.dataset.tab).classList.add("active");
    });
});

evaluateBtn.onclick = async () => {
    const prompt = document.getElementById("prompt").value.trim();
    const model = document.getElementById("modelSelect").value;
    const files = document.getElementById("fileInput").files;

    if (!prompt) return alert("Please enter a prompt!");

    const fd = new FormData();
    fd.append("prompt", prompt);
    fd.append("model", model);
    for (const f of files) fd.append("files", f);

    loading.classList.remove("hidden");

    try {
        const res = await fetch(`${API_BASE}/analyze`, { method: "POST", body: fd });
        const data = await res.json();

        loading.classList.add("hidden");

        if (data.error) {
            document.getElementById("explanation").innerText = data.error;
            return;
        }

        const sections = data.content.split(/### /g);
        document.getElementById("explanation").innerHTML =
            marked.parse(sections.find(s => s.startsWith("Explanation")) || "No explanation provided.");
        document.getElementById("code").innerHTML =
            marked.parse(sections.find(s => s.startsWith("Code")) || "No code found.");
        document.getElementById("complexity").innerHTML =
            marked.parse(sections.find(s => s.startsWith("Time & Space Complexity")) || "No analysis found.");

        updateHistory(prompt);

    } catch (err) {
        loading.classList.add("hidden");
        alert("Error: " + err.message);
    }
};

clearBtn.onclick = () => {
    document.getElementById("prompt").value = "";
    document.querySelectorAll(".tab-content").forEach(c => c.innerHTML = "");
};

/* History persistence */
function updateHistory(entry) {
    const historyList = document.getElementById("historyList");
    const item = document.createElement("div");
    item.textContent = entry.slice(0, 60) + (entry.length > 60 ? "..." : "");
    historyList.prepend(item);
}
