import React from "react";
import { clsx } from "clsx";

export function Card(props: React.HTMLAttributes<HTMLDivElement>) {
  const { className, ...rest } = props;
  return (
    <div
      className={clsx(
        "rounded-lg border border-slate-800 bg-slate-900/60 backdrop-blur p-6 shadow",
        className
      )}
      {...rest}
    />
  );
}

export function Button(
  props: React.ButtonHTMLAttributes<HTMLButtonElement>
) {
  const { className, ...rest } = props;
  return (
    <button
      className={clsx(
        "inline-flex items-center justify-center rounded-md border border-slate-700 bg-slate-800 px-4 py-2 text-sm font-medium text-slate-100 hover:bg-slate-700 focus:outline-none focus:ring-2 focus:ring-slate-400 disabled:opacity-50",
        className
      )}
      {...rest}
    />
  );
}

export function Pill(props: React.HTMLAttributes<HTMLSpanElement>) {
  const { className, ...rest } = props;
  return (
    <span
      className={clsx(
        "inline-block rounded-full border border-slate-700 bg-slate-800 px-3 py-1 text-xs text-slate-200",
        className
      )}
      {...rest}
    />
  );
}

