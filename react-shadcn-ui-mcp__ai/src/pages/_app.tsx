  // pages/_app.tsx
  import type { AppProps } from "next/app";
  import Head from "next/head";
  
  import "@/styles/globals.css";
  import { Toaster } from "@/components/ui/sonner"; // new sonner toaster

  export default function App({ Component, pageProps }: AppProps) {
    return (
      <>
        <Head>
          <link rel="manifest" href="/manifest.webmanifest" />
          <meta name="theme-color" content="#0B0B0B" />
        </Head>
        <Component {...pageProps} />
        <Toaster />
      </>
    );
  }