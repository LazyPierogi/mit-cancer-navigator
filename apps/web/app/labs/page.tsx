import { readFileSync } from "fs";
import { join } from "path";
import { LabsDashboard } from "@/components/LabsDashboard";

const versionManifestPath = join(process.cwd(), "..", "..", "VERSION.json");
const versionManifest = JSON.parse(readFileSync(versionManifestPath, "utf-8")) as {
  productVersion: string;
  uiVersion: string;
  backendVersion: string;
  rulesetVersion: string;
  corpusVersion: string;
  releaseDate?: string;
  buildLabel: string;
  notes: string[];
};

export default function LabsPage() {
  return <LabsDashboard versionManifest={versionManifest} />;
}
