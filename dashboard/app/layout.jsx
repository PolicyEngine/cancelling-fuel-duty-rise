import { PolicyEngineShell } from "@policyengine/ui-kit/layout";
import "@policyengine/ui-kit/styles.css";

import "./globals.css";

export const metadata = {
  title: "Cancelling the fuel duty rise | PolicyEngine",
  description:
    "Interactive PolicyEngine UK analysis of the cost, counterfactual, and distributional impact of cancelling the Autumn Budget 2025 fuel-duty plan.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <PolicyEngineShell country="uk">{children}</PolicyEngineShell>
      </body>
    </html>
  );
}
