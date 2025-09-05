// public/sw.js
import {precacheAndRoute} from "serwist";

// Injected at build; make sure @serwist/next is configured:
precacheAndRoute(self.__SW_MANIFEST || []);

self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (e) => e.waitUntil(self.clients.claim()));
