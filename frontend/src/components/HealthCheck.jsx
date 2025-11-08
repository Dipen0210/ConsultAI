import React, { useEffect, useState } from "react";
import API from "../utils/api";

export default function HealthCheck() {
  const [message, setMessage] = useState("Checking backend...");

  useEffect(() => {
    let isMounted = true;
    API.get("/health")
      .then((res) => {
        if (isMounted) {
          setMessage(res.data?.message ?? "Backend response received");
        }
      })
      .catch(() => {
        if (isMounted) {
          setMessage("Backend not reachable");
        }
      });
    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <h3 className="text-sm font-semibold text-slate-600">Backend Status</h3>
      <p className="mt-1 text-slate-900">{message}</p>
    </div>
  );
}
