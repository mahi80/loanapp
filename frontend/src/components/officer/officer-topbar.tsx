"use client";

import { useState, useEffect, useRef } from "react";
import { signOut, useSession } from "next-auth/react";
import {
  Landmark,
  LayoutDashboard,
  ClipboardCheck,
  SlidersHorizontal,
  BarChart3,
  Settings,
  Bell,
  LogOut,
  User,
  ChevronDown,
} from "lucide-react";

interface OfficerTopbarProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
  pendingCount: number;
  userName?: string | null;
}

function getInitials(name?: string | null): string {
  if (!name) return "?";
  const words = name.trim().split(/\s+/);
  if (words.length === 1) return words[0][0]?.toUpperCase() ?? "?";
  return (
    (words[0][0]?.toUpperCase() ?? "") +
    (words[words.length - 1][0]?.toUpperCase() ?? "")
  );
}

export function OfficerTopbar({
  activeTab,
  onTabChange,
  pendingCount,
  userName,
}: OfficerTopbarProps) {
  const { data: session } = useSession();
  const [clock, setClock] = useState("");
  const [profileOpen, setProfileOpen] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);
  const profileRef = useRef<HTMLDivElement>(null);
  const notifRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function tick() {
      const now = new Date();
      setClock(
        now.toLocaleTimeString("en-IN", {
          hour: "2-digit",
          minute: "2-digit",
          hour12: false,
        })
      );
    }
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);

  // Close dropdowns on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (profileRef.current && !profileRef.current.contains(e.target as Node)) {
        setProfileOpen(false);
      }
      if (notifRef.current && !notifRef.current.contains(e.target as Node)) {
        setNotifOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const initials = getInitials(userName);
  const userImage = session?.user?.image;
  const userEmail = session?.user?.email;

  const tabs = [
    { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
    { id: "review", label: "Review", icon: ClipboardCheck, badge: true },
    { id: "settings", label: "Settings", icon: SlidersHorizontal },
    { id: "analytics", label: "Analytics", icon: BarChart3 },
  ];

  return (
    <header className="officer-topbar">
      {/* Logo */}
      <div className="flex items-center gap-[10px]">
        <div
          className="flex items-center justify-center rounded-[10px]"
          style={{ width: 36, height: 36, background: "#0C1222", flexShrink: 0 }}
        >
          <Landmark size={18} color="#C8A24E" />
        </div>
        <span
          style={{
            fontFamily: "var(--font-dm-serif)",
            fontSize: 18,
            color: "#0C1222",
            lineHeight: 1,
          }}
        >
          LoanAI
        </span>
      </div>

      {/* Nav tabs */}
      <nav className="nav-pills ml-6">
        {tabs.map(({ id, label, icon: Icon, badge }) => (
          <button
            key={id}
            className={`nav-pill${activeTab === id ? " active" : ""}`}
            onClick={() => onTabChange(id)}
          >
            <Icon size={15} />
            {label}
            {badge && pendingCount > 0 && (
              <span
                className="badge-pulse"
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  justifyContent: "center",
                  width: 18,
                  height: 18,
                  borderRadius: "50%",
                  background: "#C0392B",
                  color: "#fff",
                  fontSize: 10,
                  fontWeight: 700,
                }}
              >
                {pendingCount}
              </span>
            )}
          </button>
        ))}
      </nav>

      {/* Right side */}
      <div className="ml-auto flex items-center gap-3">
        {/* Live clock */}
        <span
          style={{
            fontFamily: "var(--font-jetbrains-mono)",
            fontSize: 12,
            color: "#B0A999",
          }}
        >
          {clock}
        </span>

        {/* Settings button — navigates to settings tab */}
        <button
          onClick={() => onTabChange("settings")}
          title="Settings"
          style={{
            width: 38,
            height: 38,
            borderRadius: 12,
            background: activeTab === "settings" ? "#E8E2D6" : "#F5F2EA",
            border: "none",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            transition: "background 0.2s, transform 0.2s",
          }}
          onMouseEnter={(e) => {
            (e.currentTarget as HTMLButtonElement).style.background = "#E8E2D6";
            (e.currentTarget as HTMLButtonElement).style.transform = "scale(1.05)";
          }}
          onMouseLeave={(e) => {
            (e.currentTarget as HTMLButtonElement).style.background =
              activeTab === "settings" ? "#E8E2D6" : "#F5F2EA";
            (e.currentTarget as HTMLButtonElement).style.transform = "scale(1)";
          }}
        >
          <Settings size={16} color={activeTab === "settings" ? "#0C1222" : "#7A7568"} />
        </button>

        {/* Bell button with notification dropdown */}
        <div ref={notifRef} style={{ position: "relative" }}>
          <button
            onClick={() => {
              setNotifOpen(!notifOpen);
              setProfileOpen(false);
            }}
            title="Notifications"
            style={{
              width: 38,
              height: 38,
              borderRadius: 12,
              background: notifOpen ? "#E8E2D6" : "#F5F2EA",
              border: "none",
              cursor: "pointer",
              position: "relative",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              transition: "background 0.2s, transform 0.2s",
            }}
            onMouseEnter={(e) => {
              (e.currentTarget as HTMLButtonElement).style.background = "#E8E2D6";
              (e.currentTarget as HTMLButtonElement).style.transform = "scale(1.05)";
            }}
            onMouseLeave={(e) => {
              (e.currentTarget as HTMLButtonElement).style.background =
                notifOpen ? "#E8E2D6" : "#F5F2EA";
              (e.currentTarget as HTMLButtonElement).style.transform = "scale(1)";
            }}
          >
            <Bell size={16} color="#7A7568" />
            {pendingCount > 0 && (
              <span
                style={{
                  position: "absolute",
                  top: 4,
                  right: 4,
                  width: 7,
                  height: 7,
                  borderRadius: "50%",
                  background: "#C0392B",
                  border: "2px solid #FFFDF8",
                }}
              />
            )}
          </button>

          {/* Notification dropdown */}
          {notifOpen && (
            <div
              style={{
                position: "absolute",
                top: 46,
                right: 0,
                width: 280,
                background: "#FFFDF8",
                borderRadius: 14,
                boxShadow: "0 12px 40px rgba(12,18,34,0.12), 0 2px 8px rgba(12,18,34,0.06)",
                border: "1px solid rgba(12,18,34,0.06)",
                zIndex: 100,
                overflow: "hidden",
              }}
            >
              <div style={{ padding: "14px 16px 10px", borderBottom: "1px solid #F0EDE5" }}>
                <span style={{ fontSize: 13, fontWeight: 600, color: "#0C1222" }}>
                  Notifications
                </span>
              </div>
              {pendingCount > 0 ? (
                <button
                  onClick={() => {
                    onTabChange("review");
                    setNotifOpen(false);
                  }}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 10,
                    width: "100%",
                    padding: "12px 16px",
                    border: "none",
                    background: "none",
                    cursor: "pointer",
                    textAlign: "left",
                    transition: "background 0.15s",
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = "#F5F2EA";
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = "none";
                  }}
                >
                  <div
                    style={{
                      width: 32,
                      height: 32,
                      borderRadius: 8,
                      background: "#FFF3E0",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      flexShrink: 0,
                    }}
                  >
                    <ClipboardCheck size={14} color="#E67E22" />
                  </div>
                  <div>
                    <div style={{ fontSize: 13, color: "#0C1222", fontWeight: 500 }}>
                      {pendingCount} application{pendingCount > 1 ? "s" : ""} awaiting review
                    </div>
                    <div style={{ fontSize: 11, color: "#B0A999", marginTop: 2 }}>
                      Click to open review queue
                    </div>
                  </div>
                </button>
              ) : (
                <div style={{ padding: "20px 16px", textAlign: "center" }}>
                  <span style={{ fontSize: 12, color: "#B0A999" }}>No new notifications</span>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Profile avatar with dropdown */}
        <div ref={profileRef} style={{ position: "relative" }}>
          <button
            onClick={() => {
              setProfileOpen(!profileOpen);
              setNotifOpen(false);
            }}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              background: "none",
              border: "none",
              cursor: "pointer",
              padding: 0,
              borderRadius: 12,
            }}
          >
            {userImage ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={userImage}
                alt={userName || ""}
                referrerPolicy="no-referrer"
                style={{
                  width: 38,
                  height: 38,
                  borderRadius: 12,
                  objectFit: "cover",
                  border: "2px solid #E8E2D6",
                }}
                onError={(e) => {
                  (e.target as HTMLImageElement).style.display = "none";
                  const fallback = e.currentTarget.nextElementSibling as HTMLElement;
                  if (fallback) fallback.style.display = "flex";
                }}
              />
            ) : null}
            <div
              style={{
                width: 38,
                height: 38,
                borderRadius: 12,
                background: "linear-gradient(135deg, #C8A24E 0%, #A07828 100%)",
                display: userImage ? "none" : "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "#fff",
                fontSize: 13,
                fontWeight: 700,
                flexShrink: 0,
              }}
            >
              {initials}
            </div>
            <ChevronDown
              size={14}
              color="#B0A999"
              style={{
                transition: "transform 0.2s",
                transform: profileOpen ? "rotate(180deg)" : "rotate(0deg)",
              }}
            />
          </button>

          {/* Profile dropdown */}
          {profileOpen && (
            <div
              style={{
                position: "absolute",
                top: 46,
                right: 0,
                width: 240,
                background: "#FFFDF8",
                borderRadius: 14,
                boxShadow: "0 12px 40px rgba(12,18,34,0.12), 0 2px 8px rgba(12,18,34,0.06)",
                border: "1px solid rgba(12,18,34,0.06)",
                zIndex: 100,
                overflow: "hidden",
              }}
            >
              {/* User info */}
              <div style={{ padding: "14px 16px", borderBottom: "1px solid #F0EDE5" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  {userImage ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={userImage}
                      alt=""
                      referrerPolicy="no-referrer"
                      style={{
                        width: 36,
                        height: 36,
                        borderRadius: 10,
                        objectFit: "cover",
                      }}
                    />
                  ) : (
                    <div
                      style={{
                        width: 36,
                        height: 36,
                        borderRadius: 10,
                        background: "linear-gradient(135deg, #C8A24E 0%, #A07828 100%)",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        color: "#fff",
                        fontSize: 13,
                        fontWeight: 700,
                      }}
                    >
                      {initials}
                    </div>
                  )}
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 600, color: "#0C1222" }}>
                      {userName || "Officer"}
                    </div>
                    {userEmail && (
                      <div style={{ fontSize: 11, color: "#B0A999", marginTop: 1 }}>
                        {userEmail}
                      </div>
                    )}
                  </div>
                </div>
                <div
                  style={{
                    marginTop: 8,
                    display: "inline-flex",
                    alignItems: "center",
                    gap: 4,
                    padding: "2px 8px",
                    borderRadius: 6,
                    background: "rgba(200,162,78,0.1)",
                    fontSize: 10,
                    fontWeight: 600,
                    color: "#A07828",
                    textTransform: "uppercase",
                    letterSpacing: "0.05em",
                  }}
                >
                  <User size={10} />
                  Officer
                </div>
              </div>

              {/* Menu items */}
              <div style={{ padding: "6px" }}>
                <button
                  onClick={() => {
                    onTabChange("settings");
                    setProfileOpen(false);
                  }}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 10,
                    width: "100%",
                    padding: "10px 12px",
                    border: "none",
                    background: "none",
                    cursor: "pointer",
                    borderRadius: 8,
                    fontSize: 13,
                    color: "#4A453D",
                    transition: "background 0.15s",
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = "#F5F2EA";
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = "none";
                  }}
                >
                  <Settings size={14} color="#7A7568" />
                  Settings
                </button>

                <div
                  style={{
                    height: 1,
                    background: "#F0EDE5",
                    margin: "4px 8px",
                  }}
                />

                <button
                  onClick={() => signOut({ callbackUrl: "/" })}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 10,
                    width: "100%",
                    padding: "10px 12px",
                    border: "none",
                    background: "none",
                    cursor: "pointer",
                    borderRadius: 8,
                    fontSize: 13,
                    color: "#C0392B",
                    transition: "background 0.15s",
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = "#FDF2F2";
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = "none";
                  }}
                >
                  <LogOut size={14} color="#C0392B" />
                  Sign Out
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
