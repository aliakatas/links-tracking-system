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
