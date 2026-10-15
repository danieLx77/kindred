export function BrandMark({ className }: { className?: string }) {
  return (
    <svg
      className={className ? `brand-mark ${className}` : "brand-mark"}
      viewBox="0 0 32 32"
      aria-hidden="true"
      focusable="false"
    >
      <circle className="brand-mark__a" cx="11" cy="16" r="9" />
      <circle className="brand-mark__b" cx="21" cy="16" r="9" />
      <path className="brand-mark__lens" d="M16 8.52A9 9 0 0 1 16 23.48A9 9 0 0 1 16 8.52Z" />
    </svg>
  );
}
