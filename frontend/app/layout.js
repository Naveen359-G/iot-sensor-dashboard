import "./globals.css";
import { Analytics } from "@vercel/analytics/react";

export const metadata = {
  title: "IoT Sensor Dashboard",
  description: "Live IoT Monitoring System"
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        {children}
        <Analytics />
      </body>
    </html>
  );
}
