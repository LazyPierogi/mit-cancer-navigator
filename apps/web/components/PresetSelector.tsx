"use client";

import { Preset } from "@/lib/presets";

type PresetSelectorProps = {
    presets: Preset[];
    goldenVignettes: Preset[];
    activePresetId: string | null;
    onSelect: (preset: Preset) => void;
    showGolden: boolean;
    onToggleGolden: () => void;
};

export function PresetSelector({
    presets,
    goldenVignettes,
    activePresetId,
    onSelect,
    showGolden,
    onToggleGolden
}: PresetSelectorProps) {
    return (
        <div className="preset-bar">
            <div className="form-section-header">
                <h3>Quick Presets</h3>
                <button
                    type="button"
                    className="form-section-toggle"
                    onClick={onToggleGolden}
                >
                    {showGolden ? "Hide Golden Vignettes" : `Show Golden Vignettes (${goldenVignettes.length})`}
                </button>
            </div>

            <div className="preset-list">
                {presets.map((preset) => (
                    <button
                        key={preset.id}
                        type="button"
                        className={`preset-card${activePresetId === preset.id ? " preset-active" : ""}`}
                        onClick={() => onSelect(preset)}
                    >
                        <span className="preset-name">{preset.name}</span>
                        <span className="preset-detail">{preset.detail}</span>
                    </button>
                ))}

                <button
                    type="button"
                    className={`preset-card preset-custom${activePresetId === null ? " preset-active" : ""}`}
                    onClick={() => onSelect({
                        id: "__custom__",
                        name: "Custom",
                        detail: "Current form values",
                        variant: "custom",
                        vignette: null as never
                    })}
                >
                    <span className="preset-name">✎ Custom</span>
                    <span className="preset-detail">Edit fields manually</span>
                </button>
            </div>

            {showGolden && (
                <div className="preset-list" style={{ marginTop: 10 }}>
                    {goldenVignettes.map((gv) => (
                        <button
                            key={gv.id}
                            type="button"
                            className={`preset-card preset-golden${activePresetId === gv.id ? " preset-active" : ""}`}
                            onClick={() => onSelect(gv)}
                        >
                            <span className="preset-name">{gv.name}</span>
                            <span className="preset-detail">{gv.detail}</span>
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
}
