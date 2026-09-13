import React, { useState, useEffect, useRef } from "react";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

interface AnimatedFormFieldProps {
  label: string;
  value: string;
  fieldKey?: string;
  icon?: React.ComponentType<{ size?: number; className?: string }>;
  isTextarea?: boolean;
  rows?: number;
  placeholder?: string;
}

export function AnimatedFormField({
  label,
  value,
  fieldKey,
  icon: Icon,
  isTextarea = false,
  rows = 3,
  placeholder = "—",
}: AnimatedFormFieldProps) {
  const targetValue = value || "";
  const [displayedValue, setDisplayedValue] = useState(targetValue);
  const [isAnimating, setIsAnimating] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const isFirstRender = useRef(true);
  const prevTargetRef = useRef(targetValue);

  useEffect(() => {
    // Skip animation on initial component mount if target is unchanged
    if (isFirstRender.current) {
      isFirstRender.current = false;
      setDisplayedValue(targetValue);
      prevTargetRef.current = targetValue;
      return;
    }

    // If target value hasn't actually changed, do nothing
    if (prevTargetRef.current === targetValue) {
      return;
    }

    const startVal = displayedValue;
    const endVal = targetValue;
    prevTargetRef.current = targetValue;

    setIsAnimating(true);

    // Auto-scroll into view smoothly
    if (wrapperRef.current) {
      wrapperRef.current.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }

    let cancel = false;

    const animateUpdate = async () => {
      // Phase 1: Erase current text character-by-character
      let currentText = startVal;
      while (currentText.length > 0 && !cancel) {
        currentText = currentText.slice(0, -1);
        setDisplayedValue(currentText);
        await new Promise((resolve) => setTimeout(resolve, 18));
      }

      await new Promise((resolve) => setTimeout(resolve, 120));

      // Phase 2: Type out new text character-by-character
      let typedText = "";
      for (let i = 0; i < endVal.length; i++) {
        if (cancel) break;
        typedText += endVal[i];
        setDisplayedValue(typedText);
        await new Promise((resolve) => setTimeout(resolve, 24));
      }

      // Phase 3: Hold green hue glow highlight for 1 second after typing finishes
      if (!cancel) {
        await new Promise((resolve) => setTimeout(resolve, 1000));
        setIsAnimating(false);
      }
    };

    animateUpdate();

    return () => {
      cancel = true;
    };
  }, [targetValue]);

  const displayString = displayedValue || placeholder;

  return (
    <div
      ref={wrapperRef}
      className={`form-field transition-all duration-300 rounded-lg p-1.5 ${
        isAnimating
          ? "field-update-active ring-2 ring-emerald-500/80 bg-emerald-500/10 shadow-[0_0_15px_rgba(16,185,129,0.3)]"
          : ""
      }`}
      data-field-key={fieldKey}
    >
      <Label className="form-label flex items-center justify-between">
        <span className="flex items-center gap-1.5">
          {Icon && <Icon size={13} className="form-label-icon text-primary" />}
          {label}
        </span>
        {isAnimating && (
          <span className="text-[10px] font-semibold text-emerald-600 dark:text-emerald-400 animate-pulse flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 inline-block" />
            AI Updating...
          </span>
        )}
      </Label>

      <div className="relative flex items-center mt-1">
        {isTextarea ? (
          <div className="relative w-full">
            <Textarea
              value={displayString}
              readOnly
              rows={rows}
              className={`form-textarea-readonly transition-colors duration-300 ${
                isAnimating ? "border-emerald-500 text-emerald-950 dark:text-emerald-100 font-medium" : ""
              }`}
            />
            {isAnimating && (
              <span className="typewriter-cursor absolute bottom-3 right-3" />
            )}
          </div>
        ) : (
          <div className="relative w-full flex items-center">
            <Input
              value={displayString}
              readOnly
              className={`form-input-readonly transition-colors duration-300 pr-6 ${
                isAnimating ? "border-emerald-500 text-emerald-950 dark:text-emerald-100 font-medium" : ""
              }`}
            />
            {isAnimating && (
              <span className="typewriter-cursor absolute right-3" />
            )}
          </div>
        )}
      </div>
    </div>
  );
}
