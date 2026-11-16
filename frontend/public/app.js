// Shared helpers. All backend calls go through /api/*, which nginx forwards
// to the backend configured by API_URL.

export async function api(path, options = {}) {
  const response = await fetch(`/api${path}`, options);
  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`;
    try {
      const body = await response.json();
      if (typeof body.detail === "string") detail = body.detail;
      else if (Array.isArray(body.detail)) detail = body.detail.map((e) => e.msg).join("; ");
    } catch {
      // Non-JSON error body (e.g. a proxy 502): keep the status line.
    }
    throw new Error(detail);
  }
  return response.status === 204 ? null : response.json();
}

// Shows a message in a `.status` element; kind is "ok" or "error".
export function setStatus(element, message, kind = "") {
  element.textContent = message;
  element.className = `status ${kind}`;
}

const PAGES = [
  ["index.html", "Browse"],
  ["add.html", "Add"],
  ["search.html", "Search"],
];

// Fills the <nav> element and marks the current page.
export function renderNav(nav, current) {
  nav.innerHTML = "<strong>Links Tracker</strong>";
  for (const [href, label] of PAGES) {
    const link = document.createElement("a");
    link.href = href;
    link.textContent = label;
    if (href === current) link.setAttribute("aria-current", "page");
    nav.append(link);
  }
}

const PAGE_SIZE = 10;

// Renders a paginated table of URLs into `root`.
//   searchable: show a search box (filters via the API's `q` parameter)
//   deletable:  show a delete button on each row
//   editable:   allow editing the name and tags on each row
export function mountList(
  root,
  { searchable = false, deletable = false, editable = false } = {},
) {
  root.innerHTML = `
    ${searchable ? `<form class="inline" data-search>
      <input name="q" type="search" placeholder="Search by key, name or tag" aria-label="Search">
      <button class="primary">Search</button>
    </form>` : ""}
    <p class="status" role="status"></p>
    <table>
      <thead><tr><th>ID</th><th>Source key</th><th>Name</th><th>Tags</th>${editable || deletable ? "<th></th>" : ""}</tr></thead>
      <tbody></tbody>
    </table>
    <div class="pager">
      <button data-prev>Previous</button>
      <span data-position></span>
      <button data-next>Next</button>
    </div>`;

  const status = root.querySelector(".status");
  const tbody = root.querySelector("tbody");
  const prev = root.querySelector("[data-prev]");
  const next = root.querySelector("[data-next]");
  const position = root.querySelector("[data-position]");
  const searchForm = root.querySelector("[data-search]");

  let query = "";
  let offset = 0;
  let loadVersion = 0;

  async function load() {
    const version = ++loadVersion;
    const params = new URLSearchParams({ limit: PAGE_SIZE, offset });
    if (query) params.set("q", query);
    try {
      const page = await api(`/urls?${params}`);
      if (version !== loadVersion) return false;
      // The last row of the last page may have just been deleted.
      if (page.items.length === 0 && offset > 0) {
        offset = Math.max(0, offset - PAGE_SIZE);
        return load();
      }
      setStatus(status, page.total === 0 ? "No URLs found." : "");
      render(page);
      return true;
    } catch (error) {
      if (version !== loadVersion) return false;
      setStatus(status, error.message, "error");
      return false;
    }
  }

  function render({ items, total }) {
    tbody.replaceChildren(...items.map(renderRow));
    const end = offset + items.length;
    position.textContent = total === 0 ? "" : `${offset + 1}–${end} of ${total}`;
    prev.disabled = offset === 0;
    next.disabled = end >= total;
  }

  function renderRow(item) {
    const row = document.createElement("tr");
    for (const value of [item.id, item.source_key]) {
      row.insertCell().textContent = value;
    }

    const nameCell = row.insertCell();
    const tagsCell = row.insertCell();
    const actions = editable || deletable ? row.insertCell() : null;
    let editing = false;
    let saving = false;
    let nameInput;
    let tagsInput;

    function renderFields() {
      nameCell.replaceChildren();
      tagsCell.replaceChildren();
      if (editing) {
        nameInput = document.createElement("input");
        nameInput.className = "row-edit-input";
        nameInput.setAttribute("aria-label", "Name");
        nameInput.value = item.name;
        nameInput.disabled = saving;
        nameCell.append(nameInput);

        tagsInput = document.createElement("input");
        tagsInput.className = "row-edit-input";
        tagsInput.setAttribute("aria-label", "Tags, comma-separated");
        tagsInput.value = (item.tags ?? []).join(", ");
        tagsInput.disabled = saving;
        tagsCell.append(tagsInput);
        return;
      }

      nameCell.textContent = item.name;
      for (const tag of item.tags ?? []) {
        const chip = document.createElement("span");
        chip.className = "tag";
        chip.textContent = tag;
        tagsCell.append(chip);
      }
    }

    function renderActions() {
      if (!actions) return;
      actions.className = "row-actions";
      actions.replaceChildren();

      if (editable) {
        const button = document.createElement("button");
        button.type = "button";
        if (editing) {
          button.className = "primary";
          button.textContent = "Save";
          button.disabled = saving;
          button.addEventListener("click", save);
        } else {
          button.className = "edit";
          button.textContent = "✎";
          button.setAttribute("aria-label", "Edit name and tags");
          button.title = "Edit name and tags";
          button.addEventListener("click", () => {
            editing = true;
            renderFields();
            renderActions();
          });
        }
        actions.append(button);
      }

      if (deletable) {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "danger";
        button.textContent = "Delete";
        button.disabled = saving;
        button.addEventListener("click", () => remove(item));
        actions.append(button);
      }
    }

    async function save() {
      const name = nameInput.value.trim();
      const tags = tagsInput.value.split(",").map((tag) => tag.trim()).filter(Boolean);
      saving = true;
      nameInput.disabled = true;
      tagsInput.disabled = true;
      renderActions();
      try {
        const updated = await api(`/urls/${item.id}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name, tags }),
        });
        item.name = updated.name;
        item.tags = updated.tags;
        editing = false;
        saving = false;
        renderFields();
        renderActions();
        if (await load()) setStatus(status, `Saved "${item.name}".`, "ok");
      } catch (error) {
        saving = false;
        nameInput.disabled = false;
        tagsInput.disabled = false;
        renderActions();
        setStatus(status, error.message, "error");
      }
    }

    renderFields();
    renderActions();
    return row;
  }

  async function remove(item) {
    if (!confirm(`Delete "${item.name}" (${item.source_key})?`)) return;
    try {
      await api(`/urls/${item.id}`, { method: "DELETE" });
    } catch (error) {
      // 404 means it is already gone; reloading shows the true state.
      setStatus(status, error.message, "error");
      return;
    }
    await load();
    setStatus(status, `Deleted "${item.name}".`, "ok");
  }

  prev.addEventListener("click", () => {
    offset = Math.max(0, offset - PAGE_SIZE);
    load();
  });
  next.addEventListener("click", () => {
    offset += PAGE_SIZE;
    load();
  });
  searchForm?.addEventListener("submit", (event) => {
    event.preventDefault();
    query = new FormData(searchForm).get("q").trim();
    offset = 0;
    load();
  });

  load();
}
