"use client";

import {
  AudioLines,
  Disc3,
  Facebook,
  Globe,
  Instagram,
  Link2,
  Music,
  Music2,
  Trash2,
  Twitter,
  Youtube,
  type LucideIcon,
} from "lucide-react";
import { Button } from "@/components/ui/Button";

/** Catálogo de plataformas de redes sociales (espeja el ENUM TipoRedSocial). */
export const RED_PLATFORMS: Array<{
  value: string;
  label: string;
  Icon: LucideIcon;
  placeholder: string;
}> = [
  { value: "spotify", label: "Spotify", Icon: Music, placeholder: "https://open.spotify.com/artist/…" },
  { value: "instagram", label: "Instagram", Icon: Instagram, placeholder: "https://instagram.com/tu_usuario" },
  { value: "youtube", label: "YouTube", Icon: Youtube, placeholder: "https://youtube.com/@tu_canal" },
  { value: "tiktok", label: "TikTok", Icon: Music2, placeholder: "https://tiktok.com/@tu_usuario" },
  { value: "facebook", label: "Facebook", Icon: Facebook, placeholder: "https://facebook.com/tu_pagina" },
  { value: "twitter", label: "X / Twitter", Icon: Twitter, placeholder: "https://x.com/tu_usuario" },
  { value: "soundcloud", label: "SoundCloud", Icon: AudioLines, placeholder: "https://soundcloud.com/tu_usuario" },
  { value: "bandcamp", label: "Bandcamp", Icon: Disc3, placeholder: "https://tu_usuario.bandcamp.com" },
  { value: "website", label: "Sitio web", Icon: Globe, placeholder: "https://tu-sitio.com" },
  { value: "otro", label: "Otro", Icon: Link2, placeholder: "https://…" },
];

export function platformMeta(tipo: string) {
  return RED_PLATFORMS.find((p) => p.value === tipo) ?? RED_PLATFORMS[RED_PLATFORMS.length - 1];
}

type RedSocialRowProps = {
  tipo: string;
  url: string;
  onRemove: () => void;
  removing?: boolean;
};

/** Fila de una red social ya guardada: ícono + URL + botón eliminar. */
export function RedSocialRow({ tipo, url, onRemove, removing }: RedSocialRowProps) {
  const { Icon, label } = platformMeta(tipo);
  return (
    <div className="flex items-center gap-3 rounded-md border border-border bg-surface-2 px-3.5 py-2.5">
      <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-primary/15 text-primary-light">
        <Icon size={18} />
      </span>
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium text-text">{label}</p>
        <a
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          className="block truncate text-xs text-text-muted hover:text-primary-light hover:underline"
        >
          {url}
        </a>
      </div>
      <Button
        type="button"
        variant="ghost"
        size="sm"
        onClick={onRemove}
        loading={removing}
        aria-label={`Eliminar ${label}`}
        className="shrink-0"
      >
        <Trash2 size={16} />
      </Button>
    </div>
  );
}
