"use client";

import { signOut } from "next-auth/react";
import { UserAvatar } from "./user-avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { LogOut, User } from "lucide-react";

interface ProfileMenuProps {
  name?: string | null;
  email?: string | null;
  image?: string | null;
}

export function ProfileMenu({ name, email, image }: ProfileMenuProps) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger className="flex items-center gap-2 rounded-full hover:bg-slate-100 px-2 py-1 transition-colors cursor-pointer outline-none">
        <span className="text-sm text-slate-600 font-medium hidden sm:inline">{name}</span>
        <UserAvatar name={name} image={image} />
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <div className="px-3 py-2">
          <p className="text-sm font-medium text-slate-800">{name}</p>
          {email && <p className="text-xs text-slate-500 mt-0.5">{email}</p>}
        </div>
        <DropdownMenuSeparator />
        <DropdownMenuItem
          onClick={() => signOut({ callbackUrl: "/" })}
          className="text-red-600 cursor-pointer"
        >
          <LogOut className="w-4 h-4 mr-2" />
          Sign out
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
