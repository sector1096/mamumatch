import React from "react";

export function Badge({ ok, label }) {
  return <span className={`badge ${ok ? "ok" : "ko"}`}>{label} {ok ? "OK" : "NO"}</span>;
}
