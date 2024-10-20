// THIRD PARTY IMPORTS
//// import { camelCase } from "jsr:@luca/cases@1.0.0";
//// import { say } from "npm:cowsay@1.6.0";
//// import { pascalCase } from "https://deno.land/x/case/mod.ts";

// LOCAL IMPORTS
import { add } from "@utils/calc.ts";
import { camelCase } from "@luca/cases";
import { say } from "cowsay";
import { pascalCase } from "cases";

//===============================
//  CONSTANTS
//===============================


//===============================
//  MAIN
//===============================
// Learn more at https://docs.deno.com/runtime/manual/examples/module_metadata#concepts
if (import.meta.main) {
  console.log(Deno.args);
  console.log("Add 2 + 3 =", add(2, 3));

  console.log(camelCase("Hello, World!"));
  console.log(pascalCase("Hello, World!"));
}