import React from "react";

export function MarkdownText({ text }: { text: string }) {
  return (
    <div className="space-y-1 text-sm leading-relaxed">
      {text.split("\n").map((line, i) => {
        if (line.startsWith("- ")) {
          return (
            <li
              key={i}
              className="ml-4 list-disc"
              dangerouslySetInnerHTML={{
                __html: line.slice(2).replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>"),
              }}
            />
          );
        }
        if (line === "") return <div key={i} className="h-1" />;
        return (
          <p
            key={i}
            dangerouslySetInnerHTML={{
              __html: line.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>"),
            }}
          />
        );
      })}
    </div>
  );
}
