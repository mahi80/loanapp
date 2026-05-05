"use client";

export function UserAvatar({ name, image }: { name?: string | null; image?: string | null }) {
  const initials = (name || "U").split(" ").map(w => w[0]).join("").slice(0, 2).toUpperCase();

  if (!image) {
    return (
      <div className="w-8 h-8 rounded-full bg-[#0F172A] flex items-center justify-center border-2 border-slate-200">
        <span className="text-white text-xs font-semibold">{initials}</span>
      </div>
    );
  }

  return (
    <div className="relative w-8 h-8">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={image}
        alt={name || ""}
        className="w-8 h-8 rounded-full border-2 border-slate-200 object-cover"
        referrerPolicy="no-referrer"
        onError={(e) => {
          (e.target as HTMLImageElement).style.display = "none";
        }}
      />
    </div>
  );
}
