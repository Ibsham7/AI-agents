import React from "react";
import { ImageWithFallback } from "../figma/ImageWithFallback";
import logoSvg from "../../imports/file.svg";

export function Logo({ width = 64 }: { width?: number }) {
  // SVG viewBox is 354×261, aspect ratio ≈ 1.357
  const height = Math.round(width / (354 / 261));
  return (
    <ImageWithFallback
      src={logoSvg}
      alt="Study Buddy logo"
      style={{ width, height, objectFit: "contain", display: "block" }}
    />
  );
}
