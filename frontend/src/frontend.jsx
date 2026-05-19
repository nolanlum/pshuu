import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { createRoot } from "react-dom/client";

// `list_url` and `api_key` are emitted by manage.html.
const LIST_URL = list_url;
const API_KEY = api_key;
const PAGE_SIZE = 25;

const POOP = [
  "well poop.",
  "well poop. that did not work.",
  "well poop. something went sideways.",
];
const poop = () => POOP[Math.floor(Math.random() * POOP.length)];

function timeAgo(value) {
  const then = new Date(value);
  if (Number.isNaN(then.getTime())) return "";
  const secs = Math.round((Date.now() - then.getTime()) / 1000);
  const steps = [
    ["year", 31536000],
    ["month", 2592000],
    ["day", 86400],
    ["hour", 3600],
    ["minute", 60],
  ];
  for (const [label, size] of steps) {
    const n = Math.floor(secs / size);
    if (n >= 1) return `${n} ${label}${n > 1 ? "s" : ""} ago`;
  }
  return "just now";
}

function useInfiniteScroll(onHit, enabled) {
  const ref = useRef(null);
  useEffect(() => {
    const node = ref.current;
    if (!node || !enabled) return undefined;
    const io = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) onHit();
      },
      { rootMargin: "400px 0px" },
    );
    io.observe(node);
    return () => io.disconnect();
  }, [onHit, enabled]);
  return ref;
}

function Toast({ message, onClose }) {
  useEffect(() => {
    if (!message) return undefined;
    const t = setTimeout(onClose, 6000);
    return () => clearTimeout(t);
  }, [message, onClose]);
  if (!message) return null;
  return (
    <div className="toast" role="alert" onClick={onClose}>
      <span className="toast-bang">{poop()}</span>
      <span className="toast-msg">{message}</span>
      <span className="toast-x" aria-hidden="true">
        ×
      </span>
    </div>
  );
}

function UploadRow({ file, onDeleted, onError }) {
  const [busy, setBusy] = useState(false);
  const [copied, setCopied] = useState(false);

  const copy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(file.url);
    } catch (e) {
      const ta = document.createElement("textarea");
      ta.value = file.url;
      document.body.appendChild(ta);
      ta.select();
      try {
        document.execCommand("copy");
      } catch (_) {
        /* noop */
      }
      document.body.removeChild(ta);
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 1600);
  }, [file.url]);

  const del = useCallback(async () => {
    if (
      !window.confirm(
        `Delete "${file.original_filename}"? This cannot be undone.`,
      )
    ) {
      return;
    }
    setBusy(true);
    try {
      const body = new FormData();
      body.append("k", API_KEY);
      const res = await fetch("/delete/" + encodeURIComponent(file.id), {
        method: "POST",
        body,
      });
      const json = await res.json().catch(() => ({}));
      if (res.ok && json.status === "pshuu~") {
        onDeleted(file.id);
      } else {
        onError("could not delete that one.");
        setBusy(false);
      }
    } catch (e) {
      onError("could not reach the server to delete that.");
      setBusy(false);
    }
  }, [file, onDeleted, onError]);

  return (
    <li className={"upload" + (busy ? " upload--busy" : "")}>
      <a
        className="upload-thumb"
        href={file.url}
        target="_blank"
        rel="noreferrer"
      >
        <img src={file.url + "?thumb"} alt="" loading="lazy" />
      </a>
      <div className="upload-meta">
        <a
          className="upload-name"
          href={file.url}
          target="_blank"
          rel="noreferrer"
        >
          {file.original_filename}
        </a>
        <span className="upload-time">{timeAgo(file.upload_time)}</span>
      </div>
      <div className="upload-actions">
        <button className="btn btn--ghost" type="button" onClick={copy}>
          {copied ? "copied!" : "copy link"}
        </button>
        <button
          className="btn btn--danger"
          type="button"
          onClick={del}
          disabled={busy}
        >
          {busy ? "…" : "delete"}
        </button>
      </div>
    </li>
  );
}

function Dropzone({ onUploaded, onError }) {
  const [over, setOver] = useState(false);
  const [jobs, setJobs] = useState([]);
  const inputRef = useRef(null);

  const uploadOne = useCallback(
    (fileObj) => {
      const jobId = `${Date.now()}-${Math.random()}`;
      setJobs((j) => [...j, { id: jobId, name: fileObj.name, pct: 0 }]);

      const xhr = new XMLHttpRequest();
      xhr.open("POST", "/upload");
      xhr.upload.onprogress = (e) => {
        if (!e.lengthComputable) return;
        const pct = Math.round((e.loaded / e.total) * 100);
        setJobs((j) => j.map((x) => (x.id === jobId ? { ...x, pct } : x)));
      };
      const finish = () => setJobs((j) => j.filter((x) => x.id !== jobId));
      xhr.onload = () => {
        let json = {};
        try {
          json = JSON.parse(xhr.responseText);
        } catch (_) {
          /* noop */
        }
        if (xhr.status === 200 && json.status === "pshuu~") {
          // share_url = http://host/<b62 id>/<key>.ext
          const parts = json.share_url.split("/").filter(Boolean);
          onUploaded({
            id: parts[parts.length - 2],
            original_filename: fileObj.name,
            upload_time: new Date().toISOString(),
            url: json.share_url,
          });
        } else if (xhr.status === 403) {
          onError("that api key is not allowed to upload.");
        } else {
          onError(`upload of "${fileObj.name}" flopped.`);
        }
        finish();
      };
      xhr.onerror = () => {
        onError(`couldn't reach the server to upload "${fileObj.name}".`);
        finish();
      };

      const body = new FormData();
      body.append("k", API_KEY);
      body.append("f", fileObj);
      xhr.send(body);
    },
    [onUploaded, onError],
  );

  const take = useCallback(
    (fileList) => {
      for (const f of Array.from(fileList || [])) uploadOne(f);
    },
    [uploadOne],
  );

  const openPicker = () => inputRef.current && inputRef.current.click();

  return (
    <div
      className={"dropzone" + (over ? " dropzone--over" : "")}
      onClick={openPicker}
      onDragOver={(e) => {
        e.preventDefault();
        setOver(true);
      }}
      onDragLeave={() => setOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setOver(false);
        take(e.dataTransfer.files);
      }}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          openPicker();
        }
      }}
    >
      <input
        ref={inputRef}
        type="file"
        multiple
        hidden
        onChange={(e) => {
          take(e.target.files);
          e.target.value = "";
        }}
      />
      <div className="dropzone-art" aria-hidden="true">
        ⤓
      </div>
      <div className="dropzone-headline">drop files here</div>
      <div className="dropzone-sub">or tap to choose</div>

      {jobs.length > 0 && (
        <ul className="joblist" onClick={(e) => e.stopPropagation()}>
          {jobs.map((j) => (
            <li key={j.id} className="job">
              <span className="job-name">{j.name}</span>
              <span className="progress">
                <span className="progress-bar" style={{ width: `${j.pct}%` }} />
              </span>
              <span className="job-pct">{j.pct}%</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function Manage() {
  const startPage = (() => {
    const p = Number.parseInt(
      new URLSearchParams(window.location.search).get("page"),
      10,
    );
    return !Number.isNaN(p) && p > 0 ? p : 0;
  })();

  const [files, setFiles] = useState([]);
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [loading, setLoading] = useState(false);
  const [ready, setReady] = useState(false);
  const [query, setQuery] = useState("");
  const [error, setError] = useState("");

  const loadPage = useCallback(async (pageNum) => {
    setLoading(true);
    try {
      const offset = pageNum * PAGE_SIZE;
      const url =
        LIST_URL + "&" + new URLSearchParams({ offset, limit: PAGE_SIZE });
      const res = await fetch(url);
      const json = await res.json();
      if (json.status !== "pshuu~") {
        setError("the server would not hand over your uploads.");
        setHasMore(false);
        return;
      }
      const batch = Object.values(json.files).sort(
        (a, b) => new Date(b.upload_time) - new Date(a.upload_time),
      );
      setFiles((prev) => {
        const seen = new Set(prev.map((f) => f.id));
        return [...prev, ...batch.filter((f) => !seen.has(f.id))];
      });
      setHasMore(Object.keys(json.files).length === PAGE_SIZE);
      setPage(pageNum);
      const qs = new URLSearchParams({ page: pageNum });
      window.history.replaceState({}, "", window.location.pathname + "?" + qs);
    } catch (e) {
      setError("could not reach the server for your uploads.");
      setHasMore(false);
    } finally {
      setLoading(false);
      setReady(true);
    }
  }, []);

  // Initial load (covers up to the page restored from the URL).
  useEffect(() => {
    (async () => {
      for (let p = 0; p <= startPage; p += 1) {
        // eslint-disable-next-line no-await-in-loop
        await loadPage(p);
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const onHit = useCallback(() => {
    if (!loading && hasMore) loadPage(page + 1);
  }, [loading, hasMore, page, loadPage]);

  const sentinelRef = useInfiniteScroll(onHit, ready && hasMore && !query);

  const onUploaded = useCallback((file) => {
    setFiles((prev) =>
      prev.some((f) => f.id === file.id) ? prev : [file, ...prev],
    );
  }, []);
  const onDeleted = useCallback((id) => {
    setFiles((prev) => prev.filter((f) => f.id !== id));
  }, []);

  const shown = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return files;
    return files.filter((f) =>
      (f.original_filename || "").toLowerCase().includes(q),
    );
  }, [files, query]);

  return (
    <div className="manage">
      <header className="manage-head">
        <h1 className="manage-title">
          pshuu<span className="tilde">~</span>
        </h1>
        <input
          className="search"
          type="search"
          placeholder="filter by filename…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </header>

      <Dropzone onUploaded={onUploaded} onError={setError} />

      <ul className="uploads">
        {shown.map((f) => (
          <UploadRow
            key={f.id}
            file={f}
            onDeleted={onDeleted}
            onError={setError}
          />
        ))}
      </ul>

      {ready && shown.length === 0 && (
        <div className="empty">
          {query
            ? "nothing matches that filter."
            : "no uploads yet — drop a file up there to start."}
        </div>
      )}

      {loading && <div className="loading">loading…</div>}
      <div ref={sentinelRef} className="sentinel" aria-hidden="true" />

      <Toast message={error} onClose={() => setError("")} />
    </div>
  );
}

createRoot(document.getElementById("content")).render(<Manage />);
