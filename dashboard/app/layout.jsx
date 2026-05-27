import "./globals.css";

export const metadata = {
  title: "Cancelling the fuel duty rise — analysis dashboard | PolicyEngine",
  description:
    "Interactive PolicyEngine UK analysis of the cost, counterfactual, and distributional impact of cancelling the Autumn Budget 2025 fuel-duty plan.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
