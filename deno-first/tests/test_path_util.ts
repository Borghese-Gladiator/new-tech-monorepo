import { add } from "../utils/calc.ts";

import { fromFileUrl } from "@std/path/posix/from-file-url";
import { assertEquals } from "@std/assert";

assertEquals(fromFileUrl("file:///home/foo"), "/home/foo");

Deno.test(function addTest() {
  assertEquals(add(2, 3), 5);
});
