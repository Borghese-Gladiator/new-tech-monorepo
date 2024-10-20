import { serve } from "https://deno.land/std@0.198.0/http/server.ts";

//===============================
//  CONSTANTS
//===============================
const PORT = 8000;

//===============================
//  TYPES
//===============================
interface ResponseData {
  message: string;
  data?: Record<string, unknown>;
}

//===============================
//  MAIN
//===============================
async function handler(req: Request): Promise<Response> {
  const url = new URL(req.url);
  const { pathname, searchParams } = url;
  console.log("Method:", req.method);
  console.log("Path:", pathname);
  console.log("Query parameters:", searchParams);

  console.log("Headers:", req.headers);

  if (req.body) {
    const body = await req.text();
    console.log("Body:", body);
  }

  // Route handling
  if (pathname === "/") {
    const response: ResponseData = { message: "Welcome to the Deno API!" };
    return new Response(JSON.stringify(response), { status: 200, headers: { "Content-Type": "application/json" } });
  } else if (pathname === "/hello") {
    const response: ResponseData = { message: "Hello from the Deno API!" };
    return new Response(JSON.stringify(response), { status: 200, headers: { "Content-Type": "application/json" } });
  } else if (pathname.startsWith("/data")) {
    const data = { id: 1, name: "Deno", type: "Server" };
    const response: ResponseData = { message: "Here is your data", data };
    return new Response(JSON.stringify(response), { status: 200, headers: { "Content-Type": "application/json" } });
  } else if (pathname.startsWith("/stream")) {
    let timer: number;
    const streamResponse = new ReadableStream({
      async start(controller) {
        timer = setInterval(() => {
          controller.enqueue("Hello, World!\n");
        }, 1000);
      },
      cancel() {
        clearInterval(timer);
      },
    });
    return new Response(streamResponse.pipeThrough(new TextEncoderStream()), {
      headers: {
        "content-type": "text/plain; charset=utf-8",
      },
    });
  } else {
    const response: ResponseData = { message: "404: Not Found" };
    return new Response(JSON.stringify(response), { status: 404, headers: { "Content-Type": "application/json" } });
  }
}

// Serve the handler
console.log(`Server running on http://localhost:${PORT}`);
serve(handler, { hostname: "0.0.0.0", port: PORT });

/*
// deno run -A --unstable-kv server.ts

const kv = await Deno.openKv();
Deno.serve(async (request: Request) => {
  // Create short links
  if (request.method == "POST") {
    const body = await request.text();
    const { slug, url } = JSON.parse(body);
    const result = await kv.set(["links", slug], url);
    return new Response(JSON.stringify(result));
  }

  // Redirect short links
  const slug = request.url.split("/").pop() || "";
  const url = (await kv.get(["links", slug])).value as string;
  if (url) {
    return Response.redirect(url, 301);
  } else {
    const m = !slug ? "Please provide a slug." : `Slug "${slug}" not found`;
    return new Response(m, { status: 404 });
  }
});
*/